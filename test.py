import numpy as np

def is_normal_box(box, max_width=130, max_height=1000):
    """
    Kiểm tra xem box có gần vuông và không quá lớn không.

    Args:
        box (list): Danh sách 4 điểm [[x1,y1], [x2,y2], ...].
        max_width (float): Chiều rộng tối đa cho phép.
        max_height (float): Chiều cao tối đa cho phép.

    Returns:
        bool: True nếu box hợp lệ, False nếu lệch góc hoặc quá lớn.
    """
    box = np.array(box)
    if box.shape != (4, 2):
        return False

    # Tính góc giữa các cạnh
    vecs = [box[(i+1)%4] - box[i] for i in range(4)]
    angles = []
    for i in range(4):
        v1 = vecs[i]
        v2 = vecs[(i+1)%4]
        cos_angle = np.dot(v1, v2) / (np.linalg.norm(v1)*np.linalg.norm(v2) + 1e-6)
        angle = np.arccos(np.clip(cos_angle, -1, 1)) * 180 / np.pi
        angles.append(angle)

    # Kiểm tra độ vuông
    if not all(75 < a < 105 for a in angles):
        return False

    # Tính width và height từ bounding box
    x_coords = box[:, 0]
    y_coords = box[:, 1]
    width = max(x_coords) - min(x_coords)
    height = max(y_coords) - min(y_coords)

    if width > max_width or height > max_height:
        return False

    return True
