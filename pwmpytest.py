#!/usr/bin/env python3
from periphery import PWM
import time

PWM_CHIP_PAN  = "/sys/class/pwm/pwmchip0"; PWM_CHANNEL_PAN = 0
PWM_CHIP_TILT = "/sys/class/pwm/pwmchip1"; PWM_CHANNEL_TILT = 0
SERVO_FREQ    = 50.0  # 50 Hz

MIN_PULSE_MS = 0.5
MAX_PULSE_MS = 2.5

def set_angle(pwm, angle):
    angle = max(0, min(180, angle))
    pulse_ms = MIN_PULSE_MS + (angle / 180.0) * (MAX_PULSE_MS - MIN_PULSE_MS)
    pwm.duty_cycle = pulse_ms * 1e-3

if __name__ == "__main__":
    pan  = PWM(PWM_CHIP_PAN, PWM_CHANNEL_PAN)
    tilt = PWM(PWM_CHIP_TILT, PWM_CHANNEL_TILT)
    for p in (pan, tilt):
        p.frequency = SERVO_FREQ
        p.enable()

    try:
        # 先居中
        set_angle(pan,  90); set_angle(tilt, 90)
        time.sleep(1)

        while True:
            for a in range(0, 181, 15):
                set_angle(pan, a); print(f"Pan → {a}°"); time.sleep(0.3)
            time.sleep(0.5)
            for a in range(180, -1, -15):
                set_angle(pan, a); print(f"Pan → {a}°"); time.sleep(0.3)
            time.sleep(0.5)

    except KeyboardInterrupt:
        pass
    finally:
        for p in (pan, tilt):
            if p.is_enabled:
                p.disable()
                p.close()
