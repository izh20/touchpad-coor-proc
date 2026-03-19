#!/usr/bin/env python3
"""
手指包数据轨迹可视化工具
解析手指包数据，按手指状态和ID显示轨迹
支持打印坐标包 (-p 选项)

数据包格式 (47字节 = 0x2F):
- Byte 0: Report ID (0x2F)
- 手指槽位: Byte 3, 11, 19, 27, 35
  - 高4bit = 手指ID
  - 低4bit = 手指状态 (3=按下, 1=松开, 2=保持)
- 每个手指数据从 slot+1 开始: X(2字节), Y(2字节)
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import argparse
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Dict

# 坐标包配置
PACKET_SIZE = 0x2F  # 47字节
REPORT_ID = 0x2F
FINGER_SLOTS = [3, 11, 19, 27, 35]  # 手指ID和状态字节位置


@dataclass
class FingerPoint:
    """手指坐标点"""
    x: int
    y: int
    finger_id: int
    status: int  # 3=按下, 1=松开, 2=保持
    packet_index: int


class FingerDataParser:
    """手指数据解析器"""

    def __init__(self, print_packets=False, max_print=100):
        self.print_packets = print_packets
        self.max_packets_to_print = max_print
        self.packets_printed = 0
        self.trajectories = defaultdict(list)
        self.total_packets = 0

    def parse_hex_value(self, hex_str):
        """解析十六进制字符串为整数"""
        if isinstance(hex_str, str):
            if hex_str.startswith('0x') or hex_str.startswith('0X'):
                return int(hex_str, 16)
            return int(hex_str)
        return int(hex_str)

    def is_valid_point(self, x, y):
        """检查坐标点是否有效"""
        return not (x == 0 and y == 0)

    def parse_packet(self, data_bytes: List[int], packet_index: int) -> List[FingerPoint]:
        """解析单个坐标包 (47字节)"""
        fingers = []

        if len(data_bytes) < PACKET_SIZE or data_bytes[0] != REPORT_ID:
            return fingers

        # 解析5个手指槽位
        for slot_pos in FINGER_SLOTS:
            if slot_pos + 4 >= len(data_bytes):
                break

            byte_val = data_bytes[slot_pos]
            finger_id = (byte_val >> 4) & 0x0F
            finger_status = byte_val & 0x0F

            # 坐标: slot_pos+1 到 slot_pos+4
            x = data_bytes[slot_pos + 1] | (data_bytes[slot_pos + 2] << 8)
            y = data_bytes[slot_pos + 3] | (data_bytes[slot_pos + 4] << 8)

            if self.is_valid_point(x, y):
                fingers.append(FingerPoint(
                    x=x,
                    y=y,
                    finger_id=finger_id,
                    status=finger_status,
                    packet_index=packet_index
                ))

        return fingers

    def print_packet_info(self, data_bytes: List[int], packet_index: int):
        """打印坐标包详细信息"""
        if self.packets_printed >= self.max_packets_to_print:
            return

        self.packets_printed += 1

        print(f"\n{'='*70}")
        print(f"Packet #{packet_index} (Length: {len(data_bytes)} bytes)")
        print(f"{'='*70}")

        # 打印完整Hex数据
        hex_str = ' '.join(f'{b:02X}' for b in data_bytes)
        print(f"Hex: {hex_str}")

        # 打印包头
        print(f"\nHeader:")
        print(f"  Report ID: 0x{data_bytes[0]:02X}")

        # 解析并显示手指数据
        print(f"\nFinger Data (slots at bytes 3,11,19,27,35):")
        for slot_idx, slot_pos in enumerate(FINGER_SLOTS):
            if slot_pos + 4 < len(data_bytes):
                byte_val = data_bytes[slot_pos]
                finger_id = (byte_val >> 4) & 0x0F
                finger_status = byte_val & 0x0F
                x = data_bytes[slot_pos + 1] | (data_bytes[slot_pos + 2] << 8)
                y = data_bytes[slot_pos + 3] | (data_bytes[slot_pos + 4] << 8)

                status_name = {3: 'PRESS', 1: 'RELEASE', 2: 'HOVER'}.get(finger_status, f'UNK({finger_status})')
                valid = self.is_valid_point(x, y)

                print(f"  Slot{slot_idx} (byte{slot_pos}): ID={finger_id} Status={finger_status}({status_name}) X={x:5d} Y={y:5d} [{byte_val:02X}] {'VALID' if valid else 'EMPTY'}")

    def process_csv_data(self, csv_path: str):
        """处理CSV文件，提取手指轨迹"""
        lines = []
        with open(csv_path, 'r') as f:
            header = f.readline()  # 跳过表头
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    data_val = self.parse_hex_value(parts[3])
                    lines.append(data_val)

        # 按47字节分组解析包
        packet_index = 0
        i = 0
        while i < len(lines):
            if lines[i] == REPORT_ID:
                pkt = lines[i:i + PACKET_SIZE]
                if len(pkt) == PACKET_SIZE:
                    fingers = self.parse_packet(pkt, packet_index)
                    for finger in fingers:
                        self.trajectories[finger.finger_id].append(finger)

                    if self.print_packets:
                        self.print_packet_info(pkt, packet_index)

                    packet_index += 1
                i += PACKET_SIZE
            else:
                i += 1

        self.total_packets = packet_index

    def print_summary(self):
        """打印解析摘要"""
        print(f"\n{'='*70}")
        print("PARSING SUMMARY")
        print(f"{'='*70}")
        print(f"Total Packets: {self.total_packets}")
        print(f"Packets Printed: {self.packets_printed}")
        print(f"Valid Finger Trajectories: {len(self.trajectories)}")

        status_names = {3: 'PRESS', 1: 'RELEASE', 2: 'HOVER'}

        for finger_id, points in sorted(self.trajectories.items()):
            print(f"\n  Finger ID {finger_id}: {len(points)} points")

            # 统计各状态数量
            status_counts = defaultdict(int)
            for p in points:
                status_counts[p.status] += 1
            status_str = ', '.join(f"{status_names.get(s,s)}({c})" for s, c in sorted(status_counts.items()))
            print(f"    Status: {status_str}")

            if points:
                xs = [p.x for p in points]
                ys = [p.y for p in points]
                print(f"    X range: {min(xs)} - {max(xs)}")
                print(f"    Y range: {min(ys)} - {max(ys)}")


def plot_trajectories(trajectories: Dict[int, List[FingerPoint]], output_path: str = None):
    """绘制手指轨迹"""
    plt.figure(figsize=(14, 10))

    # 手指颜色映射
    finger_colors = ['red', 'blue', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']
    # 状态颜色映射
    status_colors = {3: 'red', 1: 'green', 2: 'blue'}

    for finger_id, points in sorted(trajectories.items()):
        if len(points) < 1:
            continue

        color = finger_colors[finger_id % len(finger_colors)]
        xs = [p.x for p in points]
        ys = [p.y for p in points]

        # 绘制轨迹线
        plt.plot(xs, ys, '-', color=color, alpha=0.6, linewidth=2, label=f'Finger {finger_id} ({len(points)} pts)')

        # 绘制轨迹点，用颜色区分状态
        for p in points:
            status_color = status_colors.get(p.status, 'gray')
            plt.scatter(p.x, p.y, c=status_color, s=30, alpha=0.8)
            plt.annotate(f'{p.status}', (p.x, p.y), fontsize=6, color=status_color)

        # 标记起点和终点
        if xs:
            plt.annotate(f'S', (xs[0], ys[0]), fontsize=10, color='black', fontweight='bold')
            plt.annotate(f'E', (xs[-1], ys[-1]), fontsize=10, color='black', fontweight='bold')

    plt.xlabel('X Coordinate', fontsize=12)
    plt.ylabel('Y Coordinate', fontsize=12)
    plt.title('Finger Trajectories (Red=PRESS, Green=RELEASE, Blue=HOVER)', fontsize=14)
    plt.legend(loc='upper right', fontsize=10)
    plt.grid(True, alpha=0.3)

    if output_path:
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"Image saved to: {output_path}")
    else:
        plt.show()

    plt.close()


def main():
    parser = argparse.ArgumentParser(
        description='Finger Trajectory Visualization Tool\n'
                    'Usage: python3 finger_trajectory_gui.py <input_file> [-p] [-m N] [-o output.png]',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('input_file', help='Input CSV file path')
    parser.add_argument('-p', '--print-packets', action='store_true',
                        help='Print all parsed coordinate packets (hex dump + finger data)')
    parser.add_argument('-m', '--max-print', type=int, default=100,
                        help='Maximum packets to print (default: 100)')
    parser.add_argument('-o', '--output', help='Output image path')

    args = parser.parse_args()

    print(f"Parsing file: {args.input_file}")

    parser_obj = FingerDataParser(print_packets=args.print_packets, max_print=args.max_print)
    parser_obj.process_csv_data(args.input_file)
    parser_obj.print_summary()

    if args.output:
        plot_trajectories(parser_obj.trajectories, args.output)
    else:
        plot_trajectories(parser_obj.trajectories)


if __name__ == '__main__':
    main()
