#!/bin/bash
# run_viewer.command - 将数据文件拖放到此脚本上以在 macOS 上运行实时查看器

cd "$(dirname "$0")"

if [ "$#" -eq 0 ]; then
  echo "请把数据文件（例如 1.txt）拖放到此脚本上运行。"
  read -n1 -r -p "按任意键退出..."
  exit 1
fi

PY=""
# 自动检测 python3，可在此处添加自定义解释器路径
if command -v python3 >/dev/null 2>&1; then
  PY=$(command -v python3)
elif [ -x "/usr/bin/python3" ]; then
  PY=/usr/bin/python3
elif [ -x "/opt/homebrew/bin/python3" ]; then
  PY=/opt/homebrew/bin/python3
elif [ -x "/usr/local/bin/python3" ]; then
  PY=/usr/local/bin/python3
else
  PY="/usr/bin/env python3"
fi

DATAFILE="$1"

LOG="$(pwd)/run_viewer.log"
echo "=== run_viewer $(date) ===" >> "$LOG"
echo "DATAFILE=$DATAFILE" >> "$LOG"
echo "PY=$PY" >> "$LOG"

echo "正在使用文件： $DATAFILE"
echo "使用解释器: $PY"

"$PY" "$(pwd)/finger_trajectory_realtime.py" "$DATAFILE" >> "$LOG" 2>&1

echo "程序已退出。输出已写入 $LOG"
read -n1 -r -p "按任意键退出..."
