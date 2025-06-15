#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import signal
import sys
from periphery import PWM

# ==================== 配置区 ====================
# --- 1. PWM 芯片和通道号 ---
# !! 这是最关键的配置。必须是整数，且与你的硬件对应 !!
# 0 对应 /sys/class/pwm/pwmchip0
# 1 对应 /sys/class/pwm/pwmchip1
PWM_CHIP_PAN = 0  # 水平舵机 (Pan)
PWM_CHANNEL_PAN = 0
PWM_CHIP_TILT = 1  # 垂直舵机 (Tilt)
PWM_CHANNEL_TILT = 0

# --- 2. 舵机信号参数 ---
SERVO_FREQ = 50.0  # 伺服舵机标准频率 (50Hz -> 20ms 周期)
MIN_PULSE_MS = 0.5  # 对应 0°   的脉冲宽度 (毫秒)
MAX_PULSE_MS = 2.5  # 对应 180° 的脉冲宽度 (毫秒)
# 注意: 不同舵机型号的脉宽范围可能略有不同 (例如 1.0ms - 2.0ms)。
# 如果 0.5-2.5ms 范围不工作，可以尝试改为 1.0-2.0ms。

# --- 3. 运动参数 ---
SWEEP_STEP_DEG = 15  # 扫描时的步进角度
SWEEP_DELAY_S = 0.3  # 每一步的角度停留时间
CENTER_DELAY_S = 1.0  # 程序启动和退出时，回中位的等待时间
# ================================================


# 全局PWM实例变量，以便在 cleanup 函数中访问
pan_pwm = None
tilt_pwm = None


def set_angle(pwm: PWM, angle: float):
    """
    根据设定的角度(0-180)，计算对应的脉冲宽度，并设置PWM的占空比。
    """
    # 角度限幅，确保在 0-180 度之间
    angle = max(0.0, min(180.0, angle))

    # 线性映射: 将角度 (0-180) 转换为脉冲宽度 (MIN_PULSE_MS - MAX_PULSE_MS)
    pulse_ms = MIN_PULSE_MS + (angle / 180.0) * (MAX_PULSE_MS - MIN_PULSE_MS)

    # periphery库要求duty_cycle单位是秒
    pwm.duty_cycle = pulse_ms / 1000.0


def cleanup(signum=None, frame=None):
    """
    程序中断 (Ctrl+C) 或终止时调用的清理函数。
    安全地将舵机回中，然后禁用并关闭PWM。
    """
    print("\n程序中断，正在将舵机归位并关闭PWM...")

    # 仅当PWM对象已成功初始化时才操作
    if pan_pwm and tilt_pwm:
        try:
            set_angle(pan_pwm, 90)
            set_angle(tilt_pwm, 90)
            time.sleep(CENTER_DELAY_S)  # 等待舵机到达中位
        except Exception as e:
            # 即使在设置角度时出错，也要继续尝试关闭
            print(f"归位时出错: {e}")
            pass

    # 逐个安全地禁用和关闭PWM
    for pwm in (pan_pwm, tilt_pwm):
        if pwm:
            try:
                pwm.disable()
            except Exception as e:
                print(f"禁用PWM时出错: {e}")
                pass
            try:
                pwm.close()
            except Exception as e:
                print(f"关闭PWM时出错: {e}")
                pass

    print("清理完成，程序退出。")
    sys.exit(0)


def main():
    """
    主程序
    """
    global pan_pwm, tilt_pwm

    # 捕获 Ctrl+C (SIGINT) 和 kill 命令 (SIGTERM)
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # --- 初始化PWM ---
        # 必须先创建PWM对象，再设置参数，最后使能
        print(f"正在初始化 Pan PWM: chip={PWM_CHIP_PAN}, channel={PWM_CHANNEL_PAN}")
        pan_pwm = PWM(PWM_CHIP_PAN, PWM_CHANNEL_PAN)
        pan_pwm.frequency = SERVO_FREQ
        pan_pwm.duty_cycle = 0  # 初始占空比为0
        pan_pwm.enable()
        print("Pan PWM 已使能。")

        print(f"正在初始化 Tilt PWM: chip={PWM_CHIP_TILT}, channel={PWM_CHANNEL_TILT}")
        tilt_pwm = PWM(PWM_CHIP_TILT, PWM_CHANNEL_TILT)
        tilt_pwm.frequency = SERVO_FREQ
        tilt_pwm.duty_cycle = 0  # 初始占空比为0
        tilt_pwm.enable()
        print("Tilt PWM 已使能。")

        # --- 启动后先归位 ---
        print(f"舵机回中 (90°)，请稍候 {CENTER_DELAY_S} 秒...")
        set_angle(pan_pwm, 90)
        set_angle(tilt_pwm, 90)
        time.sleep(CENTER_DELAY_S)

        # --- 无限循环扫描 ---
        print("开始水平扫描 (0° <-> 180°)... (按 Ctrl+C 停止)")
        while True:
            # 从 0° 扫描到 180°
            for angle in range(0, 181, SWEEP_STEP_DEG):
                print(f"Pan -> {angle:3d}°")
                set_angle(pan_pwm, angle)
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)

            # 从 180° 扫描回 0°
            for angle in range(180, -1, -SWEEP_STEP_DEG):
                print(f"Pan -> {angle:3d}°")
                set_angle(pan_pwm, angle)
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)

    except Exception as e:
        print(f"\n程序主循环发生严重错误: {e}")
    finally:
        # 无论发生什么，最后都执行清理
        cleanup()


if __name__ == "__main__":
    main()