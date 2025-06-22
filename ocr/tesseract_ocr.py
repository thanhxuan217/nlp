import cv2 
import pytesseract 
from pytesseract import Output

# Kiểm tra Tesseract
TESSERACT_AVAILABLE = False
try:
    # Test Tesseract
    test_version = pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
    print(f"✅ Tesseract {test_version} đã sẵn sàng")
except Exception as e:
    print(f"⚠️ Tesseract không khả dụng: {e}")
    TESSERACT_AVAILABLE = False

def ocr_tesseract(image_path):
    """OCR với Tesseract - Hỗ trợ chi_sim và chi_tra"""
    if not TESSERACT_AVAILABLE:
        return []
    
    image = cv2.imread(image_path) 
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) 
    gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1] 
 
    results = []
    # Thử cả simplified và traditional Chinese
    for lang in ['chi_sim', 'chi_tra']:
        try:
            data = pytesseract.image_to_data(gray, lang=lang, output_type=Output.DICT)
            
            rec_texts = [] 
            rec_scores = [] 
            rec_polys = [] 
         
            for i in range(len(data['text'])): 
                if data['level'][i] == 4: 
                    text = data['text'][i].strip() 
                    try: 
                        conf = float(data['conf'][i]) 
                    except: 
                        conf = -1 
         
                    if text and conf > 0: 
                        x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i] 
                        poly = [[x, y], [x + w, y], [x + w, y + h], [x, y + h]]
                        rec_texts.append(text) 
                        rec_scores.append(conf / 100) 
                        rec_polys.append(poly)
            
            results.append({
                "engine": f"tesseract_{lang}",
                "rec_texts": rec_texts,
                "rec_scores": rec_scores,
                "rec_polys": rec_polys
            })
        except Exception as e:
            print(f"  ⚠️ Lỗi Tesseract {lang}: {e}")
    
    return results
