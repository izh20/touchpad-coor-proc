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
        i = 0

        while i < len(lines):
            if lines[i] == FINGER_REPORT_ID:
                pkt = lines[i:i + PACKET_SIZE]
                if len(pkt) == PACKET_SIZE:
                    fingers = self.parse_packet(pkt, packet_index)
                    for finger in fingers:
                        trajectories[finger.finger_id].append(finger)
                    packet_index += 1
                i += PACKET_SIZE
            else:
                i += 1

        return trajectories, packet_index

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
