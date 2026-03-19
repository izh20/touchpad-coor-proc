#!/usr/bin/env python3
"""
手指包数据轨迹可视化工具
解析手指包数据，按手指状态和ID显示轨迹
"""

import matplotlib.pyplot as plt
import argparse
import re
from collections import defaultdict


def parse_hex_value(hex_str):
    """解析十六进制字符串为整数"""
    if isinstance(hex_str, str):
        if hex_str.startswith('0x') or hex_str.startswith('0X'):
            return int(hex_str, 16)
        return int(hex_str)
    return int(hex_str)


def parse_finger_packet(data_bytes):
    """
    解析手指包数据
    根据HP012协议格式 (64字节包):
    - Byte 0: Report ID (0x2F)
    - Bytes 1-3: 头部
    - 每个手指数据 (5字节):
      - Byte 0-1: X坐标 (小端)
      - Byte 2-3: Y坐标 (小端)
      - Byte 4: 压力/ID
    - 后续: 手指2, 手指2, ...
    """
    if len(data_bytes) < 2:
        return []

    report_id = data_bytes[0]
    if report_id != 0x2F:
        return []

    # 手指数据从字节4开始
    fingers = []
    offset = 4

    # 解析所有可能的手指 (最多10个，64字节包)
    while offset + 4 < len(data_bytes):
        x = data_bytes[offset] | (data_bytes[offset + 1] << 8)
        y = data_bytes[offset + 2] | (data_bytes[offset + 3] << 8)
        finger_info = data_bytes[offset + 4]

        # 手指ID (通常是bit0-3或整个字节)
        finger_id = finger_info & 0x0F

        # 如果X和Y都是0且finger_id为0，可能是无效数据
        if x == 0 and y == 0 and finger_id == 0:
            break

        fingers.append({
            'id': finger_id,
            'x': x,
            'y': y,
            'pressure': finger_info,
            'status': 0,  # 假设按下状态
            'timestamp': None
        })
        offset += 5

    return fingers


def parse_data_value(data_str):
    """解析数据字段"""
    return parse_hex_value(data_str.strip())


def process_csv_data(csv_path):
    """处理CSV文件，提取手指数据"""
    reports = []
    current_report = []
    current_time = None
    report_start_time = None

    with open(csv_path, 'r') as f:
        header = f.readline()  # 跳过表头

        for line in f:
            parts = line.strip().split(',')
            if len(parts) < 5:
                continue

            time_val = float(parts[0])
            data_val = parse_data_value(parts[3])

            # 检测到新的报告开始(0x2F)，处理之前的报告
            if data_val == 0x2F and current_report:
                # 处理之前的报告
                if len(current_report) >= 2:
                    fingers = parse_finger_packet(current_report)
                    if fingers:
                        for f in fingers:
                            f['timestamp'] = report_start_time
                        reports.append({
                            'time': report_start_time,
                            'fingers': fingers
                        })
                # 开始新报告
                current_report = [data_val]
                report_start_time = time_val
            else:
                if report_start_time is None:
                    report_start_time = time_val
                current_report.append(data_val)

            current_time = time_val

    # 处理最后一个报告
    if current_report and len(current_report) >= 2:
        fingers = parse_finger_packet(current_report)
        if fingers:
            for f in fingers:
                f['timestamp'] = report_start_time
            reports.append({
                'time': report_start_time,
                'fingers': fingers
            })

    return reports


def extract_trajectories(reports):
    """提取所有手指的轨迹"""
    trajectories = defaultdict(list)

    for report in reports:
        for finger in report['fingers']:
            finger_id = finger['id']
            trajectories[finger_id].append({
                'x': finger['x'],
                'y': finger['y'],
                'status': finger['status'],
                'time': finger['timestamp']
            })

    return trajectories


def plot_trajectories(trajectories, output_path=None):
    """绘制手指轨迹"""
    plt.figure(figsize=(12, 10))

    # 使用固定颜色区分不同手指ID
    finger_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

    for finger_id, points in trajectories.items():
        if len(points) < 2:
            continue

        xs = [p['x'] for p in points]
        ys = [p['y'] for p in points]
        color = finger_colors[finger_id % len(finger_colors)]

        # 绘制轨迹线
        plt.plot(xs, ys, '-', color=color, alpha=0.5, linewidth=1.5, label=f'Finger {finger_id}')

        # 绘制轨迹点
        plt.scatter(xs, ys, c=color, s=15, alpha=0.7)

        # 标记起点
        plt.annotate(f'F{finger_id}', (xs[0], ys[0]), fontsize=10, color=color, fontweight='bold')

    plt.xlabel('X Coordinate')
    plt.ylabel('Y Coordinate')
    plt.title('Finger Trajectories')
    plt.legend(loc='upper right')
    plt.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Image saved to: {output_path}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(description='手指包数据轨迹可视化')
    parser.add_argument('input_file', help='输入的CSV文件路径')
    parser.add_argument('-o', '--output', help='输出图像路径', default=None)

    args = parser.parse_args()

    print(f"正在解析文件: {args.input_file}")
    reports = process_csv_data(args.input_file)
    print(f"解析到 {len(reports)} 个有效手指报告")

    if not reports:
        print("未找到有效的手指数据")
        return

    trajectories = extract_trajectories(reports)
    print(f"发现 {len(trajectories)} 个手指轨迹")

    for finger_id, points in trajectories.items():
        print(f"  手指ID {finger_id}: {len(points)} 个点")

    plot_trajectories(trajectories, args.output)


if __name__ == '__main__':
    main()
