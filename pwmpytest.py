#!/usr/bin/env python3
import time, signal, sys
from periphery import PWM

# === 配置区 ===
PWM_CHIP_PAN     = 0   # 对应 /sys/class/pwm/pwmchip0
PWM_CHANNEL_PAN  = 0

PWM_CHIP_TILT    = 1   # 对应 /sys/class/pwm/pwmchip1
PWM_CHANNEL_TILT = 0

SERVO_FREQ     = 50.0   # 50Hz → 20ms 周期
MIN_PULSE_MS   = 1.0    # 0° 对应 1.0ms
MAX_PULSE_MS   = 2.0    # 180° 对应 2.0ms

SWEEP_STEP_DEG = 15     # 每次扫 15°
SWEEP_DELAY_S  = 0.3    # 每步停 0.3s
CENTER_DELAY_S = 1.0    # 回中位后停 1s
# ===============

pan = None
tilt = None

def set_angle(pwm: PWM, angle: float):
    """把 0–180° 线性映射到 MIN_PULSE_MS–MAX_PULSE_MS，再写入 duty_cycle（秒）。"""
    a = max(0.0, min(180.0, angle))
    pulse_ms = MIN_PULSE_MS + (a / 180.0) * (MAX_PULSE_MS - MIN_PULSE_MS)
    pwm.duty_cycle = pulse_ms * 1e-3

def cleanup(signum=None, frame=None):
    """中断或结束时：先回中位，再 disable/close。"""
    print("\nCleanup: moving servos to center then shutting down...")
    try:
        set_angle(pan,  90)
        set_angle(tilt, 90)
        time.sleep(CENTER_DELAY_S)
    except Exception:
        pass

    for pwm in (pan, tilt):
        if pwm:
            try:
                pwm.disable()
            except Exception:
                pass
            try:
                pwm.close()
            except Exception:
                pass
    sys.exit(0)

if __name__ == "__main__":
    # 捕获 Ctrl–C / SIGTERM
    signal.signal(signal.SIGINT,  cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    try:
        # 初始化 Pan
        pan = PWM(PWM_CHIP_PAN, PWM_CHANNEL_PAN)
        pan.frequency = SERVO_FREQ
        pan.enable()
        print(f"Pan PWM initialized: chip={PWM_CHIP_PAN}, channel={PWM_CHANNEL_PAN}")

        # 初始化 Tilt
        tilt = PWM(PWM_CHIP_TILT, PWM_CHANNEL_TILT)
        tilt.frequency = SERVO_FREQ
        tilt.enable()
        print(f"Tilt PWM initialized: chip={PWM_CHIP_TILT}, channel={PWM_CHANNEL_TILT}")

        # 回中位
        set_angle(pan,  90)
        set_angle(tilt, 90)
        time.sleep(CENTER_DELAY_S)

        # 无限水平扫描
        while True:
            for deg in range(0, 181, SWEEP_STEP_DEG):
                set_angle(pan, deg)
                print(f"Pan → {deg:3d}°")
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)
            for deg in range(180, -1, -SWEEP_STEP_DEG):
                set_angle(pan, deg)
                print(f"Pan → {deg:3d}°")
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)

    except Exception as e:
        print("Error:", e)
    finally:
        cleanup()
