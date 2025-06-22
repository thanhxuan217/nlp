import torch
import os 
import json 
from collections import Counter, defaultdict
from ocr.paddle_ocr import ocr_paddleocr
from ocr.easy_ocr import ocr_easyocr
from ocr.tesseract_ocr import ocr_tesseract
from ocr.tro_ocr import ocr_trocr


# Thư mục chứa ảnh đầu vào và thư mục lưu đầu ra 
input_folder = "./resized_img"
output_dir = "output_voting_ocr" 
os.makedirs(output_dir, exist_ok=True)

# Duyệt qua các ảnh trong thư mục 
for filename in sorted(os.listdir(input_folder)): 
    if filename.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")): 
        input_path = os.path.join(input_folder, filename) 
        print(f"\n🔍 Processing: {input_path}") 
        
        all_ocr_results = []

        print("  🔤 Chạy Tesseract OCR...")
        tesseract_results = ocr_tesseract(input_path)
        all_ocr_results.extend(tesseract_results)
        for result in tesseract_results:
            print(f"    {result['engine']}: {result['rec_texts']} {result['rec_polys']} text boxes")

        print("  🔤 Chạy PaddleOCR...")
        paddle_result = ocr_paddleocr(input_path)
        all_ocr_results.append(paddle_result)
        print(f"    {paddle_result['engine']}: {paddle_result['rec_texts']} {paddle_result['rec_polys']} text boxes")    

        print("  🔤 Chạy EasyOCR...")
        easy_result = ocr_easyocr(input_path)
        all_ocr_results.append(easy_result)
        print(f"    {easy_result['engine']}: {easy_result['rec_texts']} {easy_result['rec_polys']} text boxes")        

        print("  🔤 Chạy TrOCR...")
        trocr_result = ocr_trocr(input_path)
        all_ocr_results.append(trocr_result)
        print(f"    {trocr_result['engine']}: {trocr_result['rec_texts']} {trocr_result['rec_polys']} text boxes")        

        
        print(all_ocr_results)
        # Áp dụng voting algorithm
        # print("  🗳️ Đang áp dụng voting algorithm...")
        # merged_result = merge_multiple_ocr_results_with_voting(all_ocr_results)
        
        # # Sắp xếp theo vị trí
        # sorted_texts, sorted_polys, sorted_scores, sorted_sources = sort_text_by_position(
        #     merged_result["rec_texts"], 
        #     merged_result["rec_polys"], 
        #     merged_result["rec_scores"],
        #     merged_result["sources"]
        # )
        
        # # Ghép thành một dòng
        # final_text = " ".join(sorted_texts)
        # avg_confidence = sum(sorted_scores) / len(sorted_scores) if sorted_scores else 0
        
        # print(f"\n  📝 Kết quả cuối cùng sau voting:")
        # print(f"  Text: {final_text}")
        # print(f"  Confidence trung bình: {avg_confidence:.3f}")
        # print(f"  Số text boxes: {len(sorted_texts)}")
        # print(f"  Engines thắng cuộc: {set(sorted_sources)}")
        
        # # Lưu kết quả chi tiết
        # output_filename = f"{os.path.splitext(filename)[0]}_voting_ocr.json"
        # output_path = os.path.join(output_dir, output_filename)
        
        # # Thống kê từng engine
        # engine_stats = {}
        # for result in all_ocr_results:
        #     engine_stats[result['engine']] = len(result['rec_texts'])
        
        # # Thống kê winners
        # winner_stats = Counter(sorted_sources)
        
        # result_data = {
        #     "filename": filename,
        #     "final_text": final_text,
        #     "average_confidence": avg_confidence,
        #     "total_text_boxes": len(sorted_texts),
        #     "voting_summary": {
        #         "total_positions": len(merged_result["voting_details"]),
        #         "winner_distribution": dict(winner_stats)
        #     },
        #     "detailed_results": {
        #         "texts": sorted_texts,
        #         "scores": sorted_scores,
        #         "polygons": sorted_polys,
        #         "sources": sorted_sources
        #     },
        #     "voting_details": merged_result["voting_details"],
        #     "engine_stats": engine_stats,
        #     "engines_used": list(set(sorted_sources)),
        #     "raw_results": {
        #         result['engine']: {
        #             "texts": result['rec_texts'],
        #             "scores": result['rec_scores'],
        #             "polygons": result['rec_polys']
        #         } for result in all_ocr_results
        #     }
        # }
        
        # # Convert tất cả numpy types trước khi lưu JSON
        # result_data = convert_numpy_types(result_data)
        
        # with open(output_path, "w", encoding="utf-8") as f:
        #     json.dump(result_data, f, ensure_ascii=False, indent=4)
        
        # print(f"  💾 Đã lưu kết quả: {output_path}")

print("\n✅ Hoàn tất xử lý toàn bộ ảnh với Voting OCR Algorithm!")
