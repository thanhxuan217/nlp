import pandas as pd
import xml.etree.ElementTree as ET
import os


os.makedirs("output_final", exist_ok=True)

# Đọc file Excel
FILE_ID = "LSE_001"
SECT_NUM="004"

df = pd.read_excel('output_paddle_ocr_label/output.xlsx')  # Thay bằng đường dẫn file thực tế

# Khởi tạo root
root = ET.Element("root")
file_elem = ET.SubElement(root, "FILE", ID=FILE_ID)

# Gắn metadata
meta = ET.SubElement(file_elem, "meta")
ET.SubElement(meta, "TITLE").text = "Việt Nam Hán Văn Tiểu Thuyết Tập Thành"  # Tên tuyển tập
ET.SubElement(meta, "VOLUME").text = "Tập 4"  # Thay "X" bằng số tập cụ thể (ví dụ: "Tập IV" hay "Tập 4")
ET.SubElement(meta, "AUTHOR").text = "Nhiều tác giả"  # Vì là tuyển tập, thường không rõ một tác giả
ET.SubElement(meta, "PERIOD").text = "Trung đại"
ET.SubElement(meta, "LANGUAGE").text = "Hán"
ET.SubElement(meta, "SOURCE").text = "Đại học Sư phạm Thượng Hải (Trung Quốc), Viện Nghiên cứu Hán Nôm (Việt Nam), Đại học Thành Công Đài Loan và Trung tâm Nghiên cứu Khoa học xã hội (Cộng hòa Pháp)"  # Hoặc "Nhà xuất bản Văn Học" nếu lấy từ sách xuất bản

# Gom nhóm theo SECT (từ tên ảnh)
grouped = df.groupby("Image Name")

sect_id = FILE_ID + "." + SECT_NUM
sect = ET.SubElement(file_elem, "SECT", ID=sect_id, NAME="VN_HánVăn_TiểuThuyết_TậpThành")

for image_name, group in grouped:
    # Lấy số trang từ tên ảnh, ví dụ: ..._page004.png => 004
    page_number = image_name.split("_page")[-1].split(".")[0]
    page = ET.SubElement(sect, "PAGE", ID=page_number)

    for _, row in group.iterrows():
        stc = ET.SubElement(page, "STC", ID=row["ID"])
        stc.text = str(row["Hán char"])  # Gán văn bản Hán vào trong STC


# Ghi ra file XML
tree = ET.ElementTree(root)
tree.write("output_final/output.xml", encoding="utf-8", xml_declaration=True)
print("DONE")