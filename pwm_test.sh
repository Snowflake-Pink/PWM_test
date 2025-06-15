#!/bin/bash
set -e

# === 配置区 (不变) ===
CHIPS=(0 1)
CHANNEL=0
PERIOD_NS=1000000
STEP_NS=50000
SLEEP_SEC=0.05

# === 导出并初始化 PWM 通道 ===
for chip in "${CHIPS[@]}"; do
  PWM_ROOT="/sys/class/pwm/pwmchip${chip}"

  # 导出 (如果不存在)
  if [ ! -d "${PWM_ROOT}/pwm${CHANNEL}" ]; then
    echo "${CHANNEL}" | sudo tee "${PWM_ROOT}/export" >/dev/null
    sleep 0.1
  fi

  PWM_CH_DIR="${PWM_ROOT}/pwm${CHANNEL}"

  # --- 【核心修复】正确的初始化顺序 ---
  # 1. 必须先确保通道处于 disable 状态
  echo "0" | sudo tee "${PWM_CH_DIR}/enable" >/dev/null

  # 2. 必须先将 duty_cycle 置零，以防它大于即将设置的 period
  echo "0" | sudo tee "${PWM_CH_DIR}/duty_cycle" >/dev/null

  # 3. 现在可以安全地设置任何 period 值
  echo "${PERIOD_NS}" | sudo tee "${PWM_CH_DIR}/period" >/dev/null

  # 4. 最后，使能 PWM
  echo "1" | sudo tee "${PWM_CH_DIR}/enable" >/dev/null
done

# === 循环扫描占空比 (不变) ===
while true; do
  # 上升阶段
  for dc in $(seq 0 "${STEP_NS}" "${PERIOD_NS}"); do
    sudo tee "/sys/class/pwm/pwmchip0/pwm${CHANNEL}/duty_cycle" <<< "${dc}" >/dev/null
    sudo tee "/sys/class/pwm/pwmchip1/pwm${CHANNEL}/duty_cycle" <<< "$(( PERIOD_NS - dc ))" >/dev/null
    sleep "${SLEEP_SEC}"
  done
  # 下降阶段
  for dc in $(seq "${PERIOD_NS}" -${STEP_NS} 0); do
    sudo tee "/sys/class/pwm/pwmchip0/pwm${CHANNEL}/duty_cycle" <<< "${dc}" >/dev/null
    sudo tee "/sys/class/pwm/pwmchip1/pwm${CHANNEL}/duty_cycle" <<< "$(( PERIOD_NS - dc ))" >/dev/null
    sleep "${SLEEP_SEC}"
  done
done

# === 清理（按 Ctrl+C 停止后执行）(不变) ===
cleanup() {
  for chip in "${CHIPS[@]}"; do
    PWM_ROOT="/sys/class/pwm/pwmchip${chip}"
    PWM_CH_DIR="${PWM_ROOT}/pwm${CHANNEL}"
    # 在 unexport 之前先 disable 是一个好习惯
    echo "0" | sudo tee "${PWM_CH_DIR}/enable" >/dev/null
    echo "${CHANNEL}" | sudo tee "${PWM_ROOT}/unexport" >/dev/null
  done
  echo "PWM 已全部关闭并撤销导出。"
}
trap cleanup EXIT