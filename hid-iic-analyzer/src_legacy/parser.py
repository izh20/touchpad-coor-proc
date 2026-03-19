def parse_data_packet(data_packet):
    if len(data_packet) != 47:
        raise ValueError("Data packet must be 47 bytes long.")

    fingers = []
    for i in range(5):
        finger_id = (data_packet[3 + i * 8] >> 4) & 0x0F
        status = data_packet[3 + i * 8] & 0x0F
        x_coord = data_packet[4 + i * 8] | (data_packet[5 + i * 8] << 8)
        y_coord = data_packet[6 + i * 8] | (data_packet[7 + i * 8] << 8)

        fingers.append({
            'finger_id': finger_id,
            'status': status,
            'coordinates': (x_coord, y_coord)
        })

    return fingers

def parse_file(file_path):
    with open(file_path, 'rb') as file:
        data = file.read()
    
    packets = []
    for i in range(0, len(data), 47):
        packet = data[i:i + 47]
        if len(packet) == 47:
            packets.append(parse_data_packet(packet))
    
    return packets
