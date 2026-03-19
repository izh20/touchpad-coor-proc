#!/bin/bash
# run_viewer.command - 将数据文件拖放到此脚本上以在 macOS 上运行实时查看器

cd "$(dirname "$0")"

if [ "$#" -eq 0 ]; then
  echo "请把数据文件（例如 1.txt）拖放到此脚本上运行。"
  read -n1 -r -p "按任意键退出..."
  exit 1
fi

PY=python3
# 如果你需指定虚拟环境或自定义 Python 路径，请修改下面一行
# PY=/usr/local/bin/python3

if ! command -v "$PY" >/dev/null 2>&1; then
  echo "未在 PATH 中找到 python3。请安装 Python 或修改脚本设置正确的解释器路径。"
  read -n1 -r -p "按任意键退出..."
  exit 1
fi

DATAFILE="$1"

echo "正在使用文件： $DATAFILE"

"$PY" "$(pwd)/finger_trajectory_realtime.py" "$DATAFILE"

echo "程序已退出。"
read -n1 -r -p "按任意键退出..."
