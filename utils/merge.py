# def get_box_x_center(box):
#     xs = [pt[0] for pt in box]
#     return sum(xs) / len(xs)

# def group_boxes_by_vertical_column(rec_polys, x_threshold=10, min_group_size=1):
#     groups = []

#     boxes = rec_polys
#     x_centers = [get_box_x_center(box) for box in boxes]
#     n = len(boxes)
#     used = [False] * n

#     for i in range(n):
#         if used[i]:
#             continue
#         group = [boxes[i]]
#         used[i] = True
#         for j in range(i + 1, n):
#             if not used[j] and abs(x_centers[i] - x_centers[j]) < x_threshold:
#                 group.append(boxes[j])
#                 used[j] = True
#         if len(group) >= min_group_size:
#             groups.append(group)
#     return groups

def get_box_x_center(box):
    xs = [pt[0] for pt in box]
    return sum(xs) / len(xs)

def get_box_y_range(box):
    ys = [pt[1] for pt in box]
    return min(ys), max(ys)

def group_boxes_by_vertical_column(rec_polys, x_threshold=10, y_threshold=30, min_group_size=1):
    """
    Gom nhóm các box thẳng hàng dọc (cột) với giới hạn x_center và khoảng cách y.
    """
    boxes = rec_polys
    x_centers = [get_box_x_center(box) for box in boxes]
    y_ranges = [get_box_y_range(box) for box in boxes]
    n = len(boxes)
    used = [False] * n
    groups = []

    for i in range(n):
        if used[i]:
            continue
        group = [boxes[i]]
        group_y_min, group_y_max = y_ranges[i]
        used[i] = True
        for j in range(i + 1, n):
            if used[j]:
                continue
            # Điều kiện gần nhau về x
            if abs(x_centers[i] - x_centers[j]) < x_threshold:
                y_min_j, y_max_j = y_ranges[j]
                # Điều kiện khoảng cách y không vượt quá y_threshold
                if y_min_j <= group_y_max + y_threshold and y_max_j >= group_y_min - y_threshold:
                    group.append(boxes[j])
                    group_y_min = min(group_y_min, y_min_j)
                    group_y_max = max(group_y_max, y_max_j)
                    used[j] = True
        if len(group) >= min_group_size:
            groups.append(group)
    return groups


def merge_boxes(boxes):
    all_points = [pt for box in boxes for pt in box]

    # Tìm min và max cho x, y
    min_x = min(pt[0] for pt in all_points)
    max_x = max(pt[0] for pt in all_points)
    min_y = min(pt[1] for pt in all_points)
    max_y = max(pt[1] for pt in all_points)

    # Tạo bounding box mới theo thứ tự: top-left, top-right, bottom-right, bottom-left
    merged_box = [(min_x, min_y), (max_x, min_y), (max_x, max_y), (min_x, max_y)]

    return merged_box
