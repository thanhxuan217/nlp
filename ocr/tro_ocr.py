from PIL import Image

# Khởi tạo TrOCR
TROCR_AVAILABLE = False
try:
    from transformers import TrOCRProcessor, VisionEncoderDecoderModel
    print("  📦 Đang tải TrOCR models...")
    trocr_processor = TrOCRProcessor.from_pretrained('microsoft/trocr-base-printed')
    trocr_model = VisionEncoderDecoderModel.from_pretrained('microsoft/trocr-base-printed')
    TROCR_AVAILABLE = True
    print("✅ TrOCR đã sẵn sàng")
except ImportError:
    print("⚠️ TrOCR không khả dụng (cần cài: pip install transformers torch)")
    TROCR_AVAILABLE = False
except Exception as e:
    print(f"⚠️ TrOCR không khả dụng: {e}")
    TROCR_AVAILABLE = False

def ocr_trocr(image_path):
    """OCR với TrOCR (Microsoft)"""
    if not TROCR_AVAILABLE:
        return {"engine": "trocr", "rec_texts": [], "rec_scores": [], "rec_polys": []}
    
    try:
        image = Image.open(image_path).convert('RGB')
        
        # TrOCR xử lý toàn bộ ảnh, không có bounding box riêng
        pixel_values = trocr_processor(images=image, return_tensors="pt").pixel_values
        generated_ids = trocr_model.generate(pixel_values)
        generated_text = trocr_processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

        print(generated_text)

        if generated_text.strip():
            # Tạo bounding box cho toàn bộ ảnh
            height, width = image.size[::-1]
            full_bbox = [[0, 0], [width, 0], [width, height], [0, height]]
            
            return {
                "engine": "trocr",
                "rec_texts": [generated_text],
                "rec_scores": [0.9],  # TrOCR không cung cấp confidence score
                "rec_polys": [full_bbox]
            }
        else:
            return {"engine": "trocr", "rec_texts": [], "rec_scores": [], "rec_polys": []}
    except Exception as e:
        print(f"  ⚠️ Lỗi TrOCR: {e}")
        return {"engine": "trocr", "rec_texts": [], "rec_scores": [], "rec_polys": []}
