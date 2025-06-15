from collections import defaultdict

def get_center(poly):
    x = sum([pt[0] for pt in poly]) / len(poly)
    y = sum([pt[1] for pt in poly]) / len(poly)
    return x, y

def sort_rec_texts_polys(rec_texts, rec_polys, rec_scores):
     # ======================
    # ✅ BƯỚC 1: Sắp từ phải sang trái
    # ======================
    items = []
    for text, poly, score in zip(rec_texts, rec_polys, rec_scores):
        cx, cy = get_center(poly)
        items.append({'text': text, 'poly': poly, 'score': score, 'cx': cx, 'cy': cy})

    # Sắp xếp toàn bộ theo cx giảm dần
    items.sort(key=lambda item: -item['cx'])

    # ======================
    # ✅ BƯỚC 2: Sắp từng cột từ trên xuống dưới
    # ======================
    columns = defaultdict(list)
    column_threshold = 15  # khoảng cách X để xem là cùng một cột
    column_keys = []

    for item in items:
        assigned = False
        for key in column_keys:
            if abs(item['cx'] - key) < column_threshold:
                columns[key].append(item)
                assigned = True
                break
        if not assigned:
            columns[item['cx']].append(item)
            column_keys.append(item['cx'])

    # Trong mỗi cột, sắp theo cy tăng dần
    for key in column_keys:
        columns[key].sort(key=lambda item: item['cy'])

    # Nối lại theo đúng thứ tự cột
    final_items = []
    for key in column_keys:
        final_items.extend(columns[key])

    # Tách kết quả
    sorted_texts = [item['text'] for item in final_items]
    sorted_polys = [item['poly'] for item in final_items]
    sorted_scores = [item['score'] for item in final_items]
    return sorted_texts, sorted_polys, sorted_scores
