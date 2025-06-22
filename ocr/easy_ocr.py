import numpy as np
import easyocr

# Khởi tạo EasyOCR
EASY_AVAILABLE = False
try:
    print("  📦 Đang tải EasyOCR models (có thể mất vài phút lần đầu)...")
    easy_ocr = easyocr.Reader(['ch_sim','en'], gpu=True)
    EASY_AVAILABLE = True
    print("✅ EasyOCR đã sẵn sàng")
except Exception as e:
    print(f"⚠️ EasyOCR không khả dụng: {e}")
    EASY_AVAILABLE = False

def ocr_easyocr(image_path):
    """OCR với EasyOCR"""
    if not EASY_AVAILABLE:
        return {"engine": "easyocr", "rec_texts": [], "rec_scores": [], "rec_polys": []}
    
    try:
        results = easy_ocr.readtext(image_path, detail=1)
        
        rec_texts = []
        rec_scores = []
        rec_polys = []
        
        for (bbox, text, confidence) in results:
            if text.strip() and confidence > 0.1:  # Lọc confidence thấp
                # EasyOCR trả về bbox dạng 4 điểm
                poly = bbox.tolist() if isinstance(bbox, np.ndarray) else bbox
                rec_texts.append(text)
                rec_scores.append(confidence)
                rec_polys.append(poly)
        
        return {
            "engine": "easyocr",
            "rec_texts": rec_texts,
            "rec_scores": rec_scores,
            "rec_polys": rec_polys
        }
    except Exception as e:
        print(f"  ⚠️ Lỗi EasyOCR: {e}")
        return {"engine": "easyocr", "rec_texts": [], "rec_scores": [], "rec_polys": []}
