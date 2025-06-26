from paddleocr import PaddleOCR 
import numpy as np

# Khởi tạo PaddleOCR
PADDLE_AVAILABLE = False
try:
    paddle_ocr = PaddleOCR( 
        lang="ch", 
        use_doc_orientation_classify=False, 
        use_doc_unwarping=False, 
        use_textline_orientation=False, 
        device="cpu" # Conlfict cuda version with other ocr package
    )
    PADDLE_AVAILABLE = True
    print("✅ PaddleOCR đã sẵn sàng")
except Exception as e:
    print(f"⚠️ PaddleOCR không khả dụng: {e}")
    PADDLE_AVAILABLE = False

def ocr_paddleocr(image_path):
    """OCR với PaddleOCR"""
    if not PADDLE_AVAILABLE:
        return {"engine": "paddleocr", "rec_texts": [], "rec_scores": [], "rec_polys": []}
    
    try:
        result = paddle_ocr.predict(image_path)
        
        rec_texts = []
        rec_scores = []
        rec_polys = []
        
        for res in result:
            print(res)

        if result and result[0]:
            for line in result[0]:
                if line:
                    bbox, (text, confidence) = line
                    bbox = bbox.tolist() if isinstance(bbox, np.ndarray) else bbox
                    
                    rec_texts.append(text)
                    rec_scores.append(confidence)
                    rec_polys.append(bbox)
        
        return {
            "engine": "paddleocr",
            "rec_texts": rec_texts,
            "rec_scores": rec_scores,
            "rec_polys": rec_polys
        }
    except Exception as e:
        print(f"  ⚠️ Lỗi PaddleOCR: {e}")
        return {"engine": "paddleocr", "rec_texts": [], "rec_scores": [], "rec_polys": []}
