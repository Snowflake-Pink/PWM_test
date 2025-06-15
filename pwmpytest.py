#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import signal
import sys
from periphery import PWM

# ==================== 配置区 (与之前相同) ====================
PWM_CHIP_PAN = 0
PWM_CHANNEL_PAN = 0
PWM_CHIP_TILT = 1
PWM_CHANNEL_TILT = 0

SERVO_FREQ = 50.0  # 50Hz -> 20ms 周期
MIN_PULSE_MS = 0.5
MAX_PULSE_MS = 2.5

SWEEP_STEP_DEG = 15
SWEEP_DELAY_S = 0.3
CENTER_DELAY_S = 1.0
# ==========================================================

pan_pwm = None
tilt_pwm = None


def set_angle(pwm: PWM, angle: float):
    """
    根据设定的角度(0-180)，计算对应的脉冲宽度，并转换为占空比比例后设置PWM。
    """
    # 角度限幅
    angle = max(0.0, min(180.0, angle))

    # 1. 线性映射: 将角度 (0-180) 转换为脉冲宽度 (单位：毫秒)
    pulse_ms = MIN_PULSE_MS + (angle / 180.0) * (MAX_PULSE_MS - MIN_PULSE_MS)

    # 2. 【核心修正】将脉冲宽度(ms)转换为占空比比例 (0.0 到 1.0)
    #    总周期 (秒) = 1 / 频率 (Hz)
    #    占空比 = 脉冲宽度(秒) / 总周期(秒)
    period_s = 1.0 / pwm.frequency
    pulse_s = pulse_ms / 1000.0
    duty_cycle_ratio = pulse_s / period_s

    # 3. 设置占空比
    pwm.duty_cycle = duty_cycle_ratio


def cleanup(signum=None, frame=None):
    """
    程序中断 (Ctrl+C) 或终止时调用的清理函数。
    """
    print("\n程序中断，正在将舵机归位并关闭PWM...")

    if pan_pwm and tilt_pwm:
        try:
            # 使用修正后的函数进行归位
            set_angle(pan_pwm, 90)
            set_angle(tilt_pwm, 90)
            time.sleep(CENTER_DELAY_S)
        except Exception as e:
            print(f"归位时出错: {e}")
            pass

    for pwm in (pan_pwm, tilt_pwm):
        if pwm:
            try:
                pwm.disable()
            except Exception:
                pass
            try:
                pwm.close()
            except Exception:
                pass

    print("清理完成，程序退出。")
    sys.exit(0)


def main():
    """
    主程序 (逻辑不变)
    """
    global pan_pwm, tilt_pwm

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        print(f"正在初始化 Pan PWM: chip={PWM_CHIP_PAN}, channel={PWM_CHANNEL_PAN}")
        pan_pwm = PWM(PWM_CHIP_PAN, PWM_CHANNEL_PAN)
        pan_pwm.frequency = SERVO_FREQ
        pan_pwm.duty_cycle = 0
        pan_pwm.enable()
        print("Pan PWM 已使能。")

        print(f"正在初始化 Tilt PWM: chip={PWM_CHIP_TILT}, channel={PWM_CHANNEL_TILT}")
        tilt_pwm = PWM(PWM_CHIP_TILT, PWM_CHANNEL_TILT)
        tilt_pwm.frequency = SERVO_FREQ
        tilt_pwm.duty_cycle = 0
        tilt_pwm.enable()
        print("Tilt PWM 已使能。")

        print(f"舵机回中 (90°)，请稍候 {CENTER_DELAY_S} 秒...")
        set_angle(pan_pwm, 90)
        set_angle(tilt_pwm, 90)
        time.sleep(CENTER_DELAY_S)

        print("开始水平扫描 (0° <-> 180°)... (按 Ctrl+C 停止)")
        while True:
            for angle in range(0, 181, SWEEP_STEP_DEG):
                print(f"Pan -> {angle:3d}°")
                set_angle(pan_pwm, angle)
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)

            for angle in range(180, -1, -SWEEP_STEP_DEG):
                print(f"Pan -> {angle:3d}°")
                set_angle(pan_pwm, angle)
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)

    except Exception as e:
        print(f"\n程序主循环发生严重错误: {e}")
    finally:
        cleanup()


if __name__ == "__main__":
    main()