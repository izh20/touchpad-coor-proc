class FingerTrajectory:
    def __init__(self, finger_id, status, x, y):
        self.finger_id = finger_id
        self.status = status
        self.x = x
        self.y = y

    def __repr__(self):
        return f"FingerTrajectory(finger_id={self.finger_id}, status={self.status}, x={self.x}, y={self.y})"


class LargeTouchArea:
    def __init__(self, area_id, status, coordinates):
        self.area_id = area_id
        self.status = status
        self.coordinates = coordinates  # List of (x, y) tuples

    def __repr__(self):
        return f"LargeTouchArea(area_id={self.area_id}, status={self.status}, coordinates={self.coordinates})"