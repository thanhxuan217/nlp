import pandas as pd
import xml.etree.ElementTree as ET
import os


os.makedirs("output_final", exist_ok=True)

# Đọc file Excel
FILE_ID = "PKS_001"
SECT_NUM="004"

df = pd.read_excel('output_paddle_ocr_label/output.xlsx')  # Thay bằng đường dẫn file thực tế

# Khởi tạo root
root = ET.Element("root")
file_elem = ET.SubElement(root, "FILE", ID=FILE_ID)

# Gắn metadata
meta = ET.SubElement(file_elem, "meta")
ET.SubElement(meta, "TITLE").text = "Đại học" # Dummy
ET.SubElement(meta, "VOLUME").text = "Tứ thư" # Dummy
ET.SubElement(meta, "AUTHOR").text = "Tăng Tử" # Dummy
ET.SubElement(meta, "PERIOD").text = "Chiến Quốc" # Dummy
ET.SubElement(meta, "LANGUAGE").text = "Hán"
ET.SubElement(meta, "SOURCE").text = "ctext.org" # Dummy

# Gom nhóm theo SECT (từ tên ảnh)
grouped = df.groupby("Image Name")

for image_name, group in grouped:
    sect_id = FILE_ID + "." + SECT_NUM
    sect = ET.SubElement(file_elem, "SECT", ID=sect_id, NAME="VN_HánVăn_TiểuThuyết_TậpThành")

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