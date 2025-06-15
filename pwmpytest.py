#!/usr/bin/env python3
import time
import signal
import sys
from periphery import PWM

# ———— 参数区 ————
PWM_CHIP_PAN    = "/sys/class/pwm/pwmchip0"
PWM_CHANNEL_PAN = 0
PWM_CHIP_TILT   = "/sys/class/pwm/pwmchip1"
PWM_CHANNEL_TILT= 0

SERVO_FREQ   = 50.0        # 50 Hz → 20 ms 周期
MIN_PULSE_MS = 0.5         # 0° 对应 0.5 ms
MAX_PULSE_MS = 2.5         # 180° 对应 2.5 ms

SWEEP_STEP_DEG = 15        # 每次递增 15°
SWEEP_DELAY_S  = 0.3       # 每次角度停留 0.3 s
CENTER_DELAY_S= 1.0        # 回中位后停留 1 s

# ———— 全局 PWM 实例 ————
pan  = PWM(PWM_CHIP_PAN, PWM_CHANNEL_PAN)
tilt = PWM(PWM_CHIP_TILT, PWM_CHANNEL_TILT)

def set_angle(pwm: PWM, angle: float):
    """
    将 angle (0~180) 映射到 0.5~2.5ms 脉宽，并写入 pwm.duty_cycle (单位：秒)。
    """
    # 限幅
    a = max(0.0, min(180.0, angle))
    # 线性映射
    pulse_ms = MIN_PULSE_MS + (a / 180.0) * (MAX_PULSE_MS - MIN_PULSE_MS)
    pwm.duty_cycle = pulse_ms * 1e-3

def cleanup(signum=None, frame=None):
    """
    Ctrl–C 或 SIGTERM 时调用：
    1) 先把舵机回到 90° 中位
    2) 停留一会儿
    3) 再 disable & close
    """
    print("\nReceived signal, returning to center and shutting down...")
    try:
        set_angle(pan,  90)
        set_angle(tilt, 90)
        time.sleep(CENTER_DELAY_S)
    except Exception:
        pass
    for pwm in (pan, tilt):
        if pwm.is_enabled:
            pwm.disable()
            pwm.close()
    sys.exit(0)

# ———— 主程序 ————
if __name__ == "__main__":
    # 捕获 SIGINT/SIGTERM
    signal.signal(signal.SIGINT,  cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # 打开并初始化
    for pwm in (pan, tilt):
        pwm.frequency = SERVO_FREQ
        pwm.enable()

    # 先回中位
    set_angle(pan,  90)
    set_angle(tilt, 90)
    time.sleep(CENTER_DELAY_S)

    try:
        # 无限扫描 pan
        while True:
            # 从 0 → 180
            for a in range(0, 181, SWEEP_STEP_DEG):
                set_angle(pan, a)
                print(f"Pan → {a:3d}°")
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)
            # 从 180 → 0
            for a in range(180, -1, -SWEEP_STEP_DEG):
                set_angle(pan, a)
                print(f"Pan → {a:3d}°")
                time.sleep(SWEEP_DELAY_S)
            time.sleep(0.5)

    except Exception as e:
        print("Error:", e)
    finally:
        cleanup()
