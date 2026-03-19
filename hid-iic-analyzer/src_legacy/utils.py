def convert_to_bytes(data):
    return data.to_bytes(2, byteorder='little')

def calculate_distance(point1, point2):
    return ((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2) ** 0.5

def normalize_coordinates(x, y, width, height):
    return (x / width, y / height)

def is_within_bounds(x, y, bounds):
    return bounds[0] <= x <= bounds[2] and bounds[1] <= y <= bounds[3]
