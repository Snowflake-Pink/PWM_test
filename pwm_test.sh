#!/bin/bash
set -e

# === 配置区 ===
CHIPS=(0 1)             # 要测试的 pwmchip 列表
CHANNEL=0               # 每个 pwmchip 上的通道号
PERIOD_NS=1000000       # 周期：1_000_000 ns = 1 ms
STEP_NS=50000           # 占空比步长：50_000 ns = 5%
SLEEP_SEC=0.05          # 每步延时：0.05 s

# === 导出并初始化 PWM 通道 ===
for chip in "${CHIPS[@]}"; do
  PWM_ROOT="/sys/class/pwm/pwmchip${chip}"
  # 导出
  if [ ! -d "${PWM_ROOT}/pwm${CHANNEL}" ]; then
    echo "${CHANNEL}" | sudo tee "${PWM_ROOT}/export" >/dev/null
    sleep 0.1
  fi
  # 配置周期与初始占空比
  PWM_CH_DIR="${PWM_ROOT}/pwm${CHANNEL}"
  echo "${PERIOD_NS}"   | sudo tee "${PWM_CH_DIR}/period"     >/dev/null
  echo       "0"        | sudo tee "${PWM_CH_DIR}/duty_cycle" >/dev/null
  echo       "1"        | sudo tee "${PWM_CH_DIR}/enable"     >/dev/null
done

# === 循环扫描占空比 ===
# 从 0 → 100% → 0%
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

# === 清理（按 Ctrl+C 停止后执行） ===
cleanup() {
  for chip in "${CHIPS[@]}"; do
    PWM_ROOT="/sys/class/pwm/pwmchip${chip}"
    PWM_CH_DIR="${PWM_ROOT}/pwm${CHANNEL}"
    echo "0" | sudo tee "${PWM_CH_DIR}/enable" >/dev/null
    echo "${CHANNEL}" | sudo tee "${PWM_ROOT}/unexport" >/dev/null
  done
  echo "PWM 已全部关闭并撤销导出。"
}
trap cleanup EXIT
