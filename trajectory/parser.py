# trajectory/parser.py
from collections import defaultdict

PACKET_SIZE = 47
FINGER_REPORT_ID = 0x2F
FINGER_SLOTS = [3, 11, 19, 27, 35]

class FingerPoint:
    def __init__(self, x, y, finger_id, status, packet_index):
        self.x = x
        self.y = y
        self.finger_id = finger_id
        self.status = status
        self.packet_index = packet_index


class FingerDataParser:
    def parse_hex_value(self, hex_str):
        if isinstance(hex_str, str):
            if hex_str.startswith('0x') or hex_str.startswith('0X'):
                return int(hex_str, 16)
            return int(hex_str)
        return int(hex_str)

    def process_csv_data(self, csv_path):
        """处理CSV文件，提取手指轨迹，返回 trajectories(dict->list[FingerPoint]) 和 packet_count"""
        lines = []
        with open(csv_path, 'r') as f:
            header = f.readline()
            for line in f:
                parts = line.strip().split(',')
                if len(parts) >= 5:
                    data_val = self.parse_hex_value(parts[3])
                    lines.append(data_val)

        trajectories = defaultdict(list)
        packet_index = 0
        packet_scantimes = {}
        i = 0

        while i < len(lines):
            if lines[i] == FINGER_REPORT_ID:
                pkt = lines[i:i + PACKET_SIZE]
                if len(pkt) == PACKET_SIZE:
                    # 提取 scantime（第44与第45字节，little-endian u16）
                    try:
                        # 多重候选位置检测：优先查找非全零的两字节组合
                        last_slot = FINGER_SLOTS[-1]
                        candidates = [
                            (last_slot + 5, last_slot + 6),
                            (PACKET_SIZE - 4, PACKET_SIZE - 3),
                            (PACKET_SIZE - 3, PACKET_SIZE - 2),
                            (last_slot + 6, last_slot + 7),
                        ]

                        found = None
                        for low_idx, high_idx in candidates:
                            if 0 <= low_idx < len(pkt) and 0 <= high_idx < len(pkt):
                                low = pkt[low_idx]
                                high = pkt[high_idx]
                                # 若任一字节非零，则认为找到了合理的 scantime 字段
                                if (low != 0) or (high != 0):
                                    # 尝试读取紧随的一个字节作为手指个数（若存在）
                                    # 以及随后一个字节作为按键状态
                                    finger_cnt = None
                                    key_state = None
                                    cnt_idx = high_idx + 1
                                    if 0 <= cnt_idx < len(pkt):
                                        finger_cnt = pkt[cnt_idx]
                                    key_idx = cnt_idx + 1
                                    if 0 <= key_idx < len(pkt):
                                        key_state = pkt[key_idx]
                                    found = (low, high, finger_cnt, key_state)
                                    break

                        # 如果都为零，仍回退到 PACKET_SIZE-3/ -2 的位置（历史上曾使用 44/45）
                        if not found:
                            low_idx = PACKET_SIZE - 3
                            high_idx = PACKET_SIZE - 2
                            if 0 <= low_idx < len(pkt) and 0 <= high_idx < len(pkt):
                                low = pkt[low_idx]
                                high = pkt[high_idx]
                                finger_cnt = None
                                key_state = None
                                cnt_idx = high_idx + 1
                                if 0 <= cnt_idx < len(pkt):
                                    finger_cnt = pkt[cnt_idx]
                                key_idx = cnt_idx + 1
                                if 0 <= key_idx < len(pkt):
                                    key_state = pkt[key_idx]
                                found = (low, high, finger_cnt, key_state)
                            else:
                                found = None

                        packet_scantimes[packet_index] = found
                    except Exception:
                        packet_scantimes[packet_index] = None

                    fingers = self.parse_packet(pkt, packet_index)
                    for finger in fingers:
                        trajectories[finger.finger_id].append(finger)
                    packet_index += 1
                i += PACKET_SIZE
            else:
                i += 1

        return trajectories, packet_index, packet_scantimes

    def parse_packet(self, data_bytes, packet_index):
        fingers = []
        if len(data_bytes) < PACKET_SIZE:
            return fingers

        for slot_pos in FINGER_SLOTS:
            if slot_pos + 4 >= len(data_bytes):
                break

            byte_val = data_bytes[slot_pos]
            finger_id = (byte_val >> 4) & 0x0F
            finger_status = byte_val & 0x0F

            x = data_bytes[slot_pos + 1] | (data_bytes[slot_pos + 2] << 8)
            y = data_bytes[slot_pos + 3] | (data_bytes[slot_pos + 4] << 8)

            if x != 0 or y != 0:
                fingers.append(FingerPoint(x, y, finger_id, finger_status, packet_index))

        return fingers
