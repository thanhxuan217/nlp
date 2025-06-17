import pandas as pd
import re
import ast
import numpy as np


# Hàm sắp xếp các điểm theo quy tắc top-left → top-right → bottom-right → bottom-left
def sort_box(points):
    points = np.array(points)  # Chuyển sang numpy array
    sorted_indices = np.lexsort((points[:, 0], points[:, 1]))  # Sắp xếp theo y trước, sau đó x
    top_two = points[sorted_indices[:2]]  # Lấy 2 điểm trên cùng
    bottom_two = points[sorted_indices[2:]]  # Lấy 2 điểm dưới cùng

    # Xác định top-left và top-right
    top_two = top_two[np.argsort(top_two[:, 0])]  # Sắp xếp theo x
    top_left, top_right = top_two[0], top_two[1]

    # Xác định bottom-left và bottom-right
    bottom_two = bottom_two[np.argsort(bottom_two[:, 0])]  # Sắp xếp theo x
    bottom_left, bottom_right = bottom_two[0], bottom_two[1]

    # Kết hợp theo quy tắc
    return [top_left.tolist(), top_right.tolist(), bottom_right.tolist(), bottom_left.tolist()]

def convert_data_to_Labeltxt(df, _FolderImagesName_path, _ImageName_Column = "Image_name", _PositionBBoxName_Column = "Image Box" , _OCRName_Column = "Text OCR"):

    #df.loc[:, "ID"] = df["ID"].apply(lambda x: convert_ID_To_png(x))

    
    # Nhóm dữ liệu theo Page_ID
    grouped = df.groupby(f'{_ImageName_Column}')

    result = []
    folder_name = _FolderImagesName_path.split('/')[-1]

    for page_id, group in grouped:
        page_result = []

        for _, row in group.iterrows():
            points = sort_box(eval(row[f'{_PositionBBoxName_Column}'])) 
            transcription = row[f'{_OCRName_Column}']
            
            page_result.append({"transcription": transcription, "points": points})

        result_string = "[" + ", ".join(
            [f'{{"transcription": "{item["transcription"]}", "points": {item["points"]}, "difficult": false}}' for item in page_result]
        ) + "]"

        result.append(f"{folder_name}/{page_id}\t{result_string}")

    output_path = f"{_FolderImagesName_path}/Label.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(result))

    print(f"Đã lưu dữ liệu vào {output_path}")

    list_images_name = df[f'{_ImageName_Column}'].unique().tolist()
    return list_images_name


def convert_data_to_fileStatetxt(_FolderImagesName_path, folder_list_ImageName):
    output_path = f"{_FolderImagesName_path}/fileState.txt"
    with open(f"{output_path}", "w", encoding="utf-8") as file:
        folder_name = _FolderImagesName_path.split('/')[-1]
        for _imgName in folder_list_ImageName:
            file.write(f"{folder_name}/{_imgName}\t1\n")
    print(f"Đã lưu dữ liệu vào {output_path}")



#==============================================================
# YOU CAN CHANGE HERE:
def convert_ID_To_png(string: str):
    result = string[:-4]
    result = result.replace(".","_page")
    result += ".png"
    return result
#==============================================================


def main():
    #==============================================================
    # YOU CAN CHANGE HERE:

    # Chỉnh thành tên file Excel ngữ liệu GK
    result_file_path = '../output_ocr/output_ocr_raw_2.xlsx'

    # Chỉnh thành tên folder chứa thư mục ảnh của bạn
    folder_images_path = "../images_label"

    # Chỉnh thành Tên cột của cột chứa "Tên ảnh" trong file Excel của bạn
    _ImageName_Column = "Image Name"

    # Chỉnh thành Tên cột của cột chứa tọa độ "Bounding Box" trong file Excel của bạn
    _PositionBBoxName_Column = "Image box"

    # Chỉnh thành Tên cột của cột chứa "Văn bản OCR" trong file Excel của bạn
    _OCRName_Column = "Hán char"

    # Result already sorted

    # df = pd.read_excel(result_file_path)
    # df.insert(0, "Image_name", [ convert_ID_To_png(x) for x in df["ID"]])
    # df.insert(4, "Sorted_Box", df['Image Box'].apply(lambda x: sort_box(ast.literal_eval(x))))

    # result_file_path_sorted = './result_sorted.xlsx'
    # df.to_excel(result_file_path_sorted, index=False)
    


    df = pd.read_excel(result_file_path)

    _img_names = convert_data_to_Labeltxt(df, folder_images_path, _ImageName_Column, _PositionBBoxName_Column, _OCRName_Column)
    convert_data_to_fileStatetxt(folder_images_path, _img_names)

if __name__ == "__main__":
    main()