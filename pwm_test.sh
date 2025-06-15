#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
import signal
import sys
from periphery import PWM

# ==================== 配置区 (为你的设备全新配置) ====================
# 使用与 sh 脚本完全相同的参数
PWM_CHIP_PAN     = 0
PWM_CHANNEL_PAN  = 0
PWM_CHIP_TILT    = 1
PWM_CHANNEL_TILT = 0

# 频率和周期，模仿 sh 脚本
SERVO_FREQ     = 1000.0  # 1000 Hz
PERIOD_NS      = 1000000 # 1,000,000 ns = 1ms

# 扫描步长和延时
STEP_NS        = 50000   # 50,000 ns
SLEEP_SEC      = 0.05
# =================================================================

pan_pwm = None
tilt_pwm = None

def set_raw_duty_cycle(pwm: PWM, duty_ns: int):
    """
    直接设置一个以纳秒为单位的原始 duty_cycle 值。
    """
    # 占空比比例 = 想要的duty_cycle(ns) / 总周期(ns)
    duty_cycle_ratio = duty_ns / PERIOD_NS
    pwm.duty_cycle = duty_cycle_ratio

def cleanup(signum=None, frame=None):
    """清理函数"""
    print("\n程序中断，正在关闭PWM...")
    for pwm in (pan_pwm, tilt_pwm):
        if pwm:
            try:
                # 停止时将占空比置零
                pwm.duty_cycle = 0.0
                pwm.disable()
                pwm.close()
            except Exception:
                pass
    print("清理完成，程序退出。")
    sys.exit(0)

def main():
    """主程序：模仿 sh 脚本的扫描逻辑"""
    global pan_pwm, tilt_pwm

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # 初始化两个PWM通道
        pan_pwm = PWM(PWM_CHIP_PAN, PWM_CHANNEL_PAN)
        tilt_pwm = PWM(PWM_CHIP_TILT, PWM_CHANNEL_TILT)

        for pwm in (pan_pwm, tilt_pwm):
            pwm.frequency = SERVO_FREQ
            pwm.duty_cycle = 0.0 # 初始占空比为0
            pwm.enable()

        print("PWM 已初始化，频率: 1000 Hz。开始扫描占空比...")
        print("这个脚本会让两个舵机反向转动。按 Ctrl+C 停止。")

        # 无限循环扫描占空比，完全模仿 sh 脚本
        while True:
            # 从 0 -> 100%
            for dc_ns in range(0, PERIOD_NS + 1, STEP_NS):
                set_raw_duty_cycle(pan_pwm, dc_ns)
                set_raw_duty_cycle(tilt_pwm, PERIOD_NS - dc_ns)
                time.sleep(SLEEP_SEC)

            # 从 100% -> 0
            for dc_ns in range(PERIOD_NS, -1, -STEP_NS):
                set_raw_duty_cycle(pan_pwm, dc_ns)
                set_raw_duty_cycle(tilt_pwm, PERIOD_NS - dc_ns)
                time.sleep(SLEEP_SEC)

    except Exception as e:
        print(f"\n程序主循环发生严重错误: {e}")
    finally:
        cleanup()

if __name__ == "__main__":
    main()