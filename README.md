Python version: 3.10.0

1. Chạy file pdf2img.py để convert từ pdf sang image.
2. Chạy resize-img.py để giảm kích thước ảnh.
3. Chạy paddle-ocr.py để OCR
4. Chạy convert_to_xlsx.py để xuất kết quả ra xlsx
5. Đọc Guideline trong check_label v2/Guideline
6. Sau bước này, sẽ cần dùng chạy file check_label v2/convert_data_to_labelsPaddle_v2.py để convert xlsx sang label của PPOCRLabel
7. Mở PPOCRLabel và chỉnh sửa bounding box bán thủ công (python ./PPOCRLabel/PPOCRLabel.py
8. Chạy file convert_image_labels_to_xlsx.py để chuyển labels ở bước 7 sang xlsx
9. Chạy file convert_xlsx_to_xml.py để chuyển sang file xml

!!! Lưu ý quan trọng: Nhớ đổi tên file name cho đúng (Do bài này đang làm file VN_HánVăn_TiểuThuyết_TậpThành - 04)

NOTE: Có thể chạy file write_bounding_box_v2.py để kiểm tra kết quả bouding box sau bước 8