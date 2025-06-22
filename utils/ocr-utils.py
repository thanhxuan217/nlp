import numpy as np
from difflib import SequenceMatcher
import re

def convert_numpy_types(obj):
    """Chuyển đổi numpy types thành Python native types để JSON serializable"""
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_types(item) for item in obj)
    else:
        return obj

def normalize_text(text):
    """Chuẩn hóa text để so sánh"""
    # Loại bỏ khoảng trắng thừa, ký tự đặc biệt
    text = re.sub(r'\s+', ' ', text.strip())
    # Chuyển về lowercase để so sánh
    text = text.lower()
    # Loại bỏ dấu câu
    text = re.sub(r'[^\w\s\u4e00-\u9fff]', '', text)
    return text

def calculate_text_similarity(text1, text2):
    """Tính độ tương đồng giữa 2 text"""
    norm_text1 = normalize_text(text1)
    norm_text2 = normalize_text(text2)
    
    if not norm_text1 or not norm_text2:
        return 0.0
    
    # Sử dụng SequenceMatcher để tính similarity
    similarity = SequenceMatcher(None, norm_text1, norm_text2).ratio()
    return similarity

def calculate_iou(box1, box2):
    """Tính toán Intersection over Union (IoU) giữa 2 bounding box"""
    def polygon_to_bbox(poly):
        xs = [p[0] for p in poly]
        ys = [p[1] for p in poly]
        return [min(xs), min(ys), max(xs), max(ys)]
    
    bbox1 = polygon_to_bbox(box1)
    bbox2 = polygon_to_bbox(box2)
    
    # Tính intersection
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])
    
    if x2 <= x1 or y2 <= y1:
        return 0.0
    
    intersection = (x2 - x1) * (y2 - y1)
    
    # Tính union
    area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
    area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0

def get_engine_weight(engine_name):
    """Trọng số cho từng engine dựa trên độ tin cậy"""
    weights = {
        'paddleocr': 1.0,
        'easyocr': 0.9,
        'tesseract_chi_sim': 0.8,
        'tesseract_chi_tra': 0.7,
        'trocr': 0.6
    }
    return weights.get(engine_name, 0.5)

def vote_for_best_text(candidates, similarity_threshold=0.7):
    """
    Voting algorithm để chọn text tốt nhất
    candidates: list of {"text": str, "score": float, "engine": str, "poly": list}
    """
    if not candidates:
        return None
    
    if len(candidates) == 1:
        return candidates[0]
    
    # Nhóm các candidates tương đồng
    groups = []
    used = [False] * len(candidates)
    
    for i, candidate in enumerate(candidates):
        if used[i]:
            continue
        
        # Tạo nhóm mới
        group = [candidate]
        used[i] = True
        
        # Tìm các candidate tương đồng
        for j, other_candidate in enumerate(candidates):
            if i != j and not used[j]:
                similarity = calculate_text_similarity(candidate["text"], other_candidate["text"])
                if similarity >= similarity_threshold:
                    group.append(other_candidate)
                    used[j] = True
        
        groups.append(group)
    
    # Tính điểm cho mỗi nhóm
    best_group = None
    best_score = -1
    
    for group in groups:
        # Tính điểm tổng hợp cho nhóm
        group_score = 0
        total_weight = 0
        
        for candidate in group:
            engine_weight = get_engine_weight(candidate["engine"])
            confidence_score = candidate["score"]
            
            # Điểm = confidence * trọng số engine * số lượng vote
            weighted_score = confidence_score * engine_weight * len(group)
            group_score += weighted_score
            total_weight += engine_weight
        
        # Chuẩn hóa điểm
        if total_weight > 0:
            group_score = group_score / total_weight
        
        print(f"    🗳️ Nhóm '{group[0]['text'][:20]}...': {len(group)} votes, score: {group_score:.3f}")
        for candidate in group:
            print(f"      - {candidate['engine']}: '{candidate['text']}' (conf: {candidate['score']:.3f})")
        
        if group_score > best_score:
            best_score = group_score
            best_group = group
    
    # Trong nhóm tốt nhất, chọn candidate có confidence cao nhất
    if best_group:
        best_candidate = max(best_group, key=lambda x: x["score"])
        print(f"    🏆 Chọn: {best_candidate['engine']} - '{best_candidate['text']}' (score: {best_score:.3f})")
        return best_candidate
    
    # Fallback: chọn confidence cao nhất
    best_candidate = max(candidates, key=lambda x: x["score"])
    print(f"    🏆 Fallback - chọn confidence cao nhất: {best_candidate['engine']} - '{best_candidate['text']}'")
    return best_candidate

def merge_multiple_ocr_results_with_voting(ocr_results, iou_threshold=0.3, text_similarity_threshold=0.7):
    """Merge kết quả từ nhiều OCR engines với voting algorithm"""
    if not ocr_results:
        return {"rec_texts": [], "rec_scores": [], "rec_polys": [], "sources": [], "voting_details": []}
    
    final_texts = []
    final_scores = []
    final_polys = []
    final_sources = []
    voting_details = []
    
    # Tạo danh sách tất cả text boxes từ tất cả engines
    all_boxes = []
    for result in ocr_results:
        for i, (text, score, poly) in enumerate(zip(
            result["rec_texts"], result["rec_scores"], result["rec_polys"]
        )):
            all_boxes.append({
                "text": text,
                "score": score,
                "poly": poly,
                "engine": result["engine"],
                "used": False
            })
    
    # Nhóm các boxes có IoU cao (cùng vị trí)
    position_groups = []
    for i, box in enumerate(all_boxes):
        if box["used"]:
            continue
        
        # Tạo nhóm mới cho vị trí này
        current_group = [box]
        box["used"] = True
        
        # Tìm các boxes ở vị trí tương tự
        for j, other_box in enumerate(all_boxes):
            if i != j and not other_box["used"]:
                iou = calculate_iou(box["poly"], other_box["poly"])
                if iou >= iou_threshold:
                    current_group.append(other_box)
                    other_box["used"] = True
        
        position_groups.append(current_group)
    
    # Áp dụng voting algorithm cho mỗi nhóm vị trí
    for group_idx, group in enumerate(position_groups):
        print(f"  📍 Vị trí {group_idx + 1}: {len(group)} candidates")
        
        # Chuẩn bị candidates cho voting
        candidates = []
        for box in group:
            candidates.append({
                "text": box["text"],
                "score": box["score"],
                "engine": box["engine"],
                "poly": box["poly"]
            })
        
        # Thực hiện voting
        winner = vote_for_best_text(candidates, text_similarity_threshold)
        
        if winner:
            final_texts.append(winner["text"])
            final_scores.append(winner["score"])
            final_polys.append(winner["poly"])
            final_sources.append(winner["engine"])
            
            # Lưu chi tiết voting
            voting_detail = {
                "position": group_idx + 1,
                "winner": winner,
                "candidates": candidates,
                "total_votes": len(candidates)
            }
            voting_details.append(voting_detail)
    
    return {
        "rec_texts": final_texts,
        "rec_scores": final_scores,
        "rec_polys": final_polys,
        "sources": final_sources,
        "voting_details": voting_details
    }

def sort_text_by_position(texts, polys, scores, sources):
    """Sắp xếp text theo vị trí từ trên xuống dưới, trái sang phải"""
    if not texts:
        return [], [], [], []
    
    items = []
    for text, poly, score, source in zip(texts, polys, scores, sources):
        y_center = sum(p[1] for p in poly) / len(poly)
        x_center = sum(p[0] for p in poly) / len(poly)
        items.append((text, poly, score, source, y_center, x_center))
    
    # Sắp xếp theo y_center trước, sau đó theo x_center
    items.sort(key=lambda x: (x[4], x[5]))
    
    sorted_texts = [item[0] for item in items]
    sorted_polys = [item[1] for item in items]
    sorted_scores = [item[2] for item in items]
    sorted_sources = [item[3] for item in items]
    
    return sorted_texts, sorted_polys, sorted_scores, sorted_sources

