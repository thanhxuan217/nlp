# Khởi tạo Google Translator
import pandas as pd
import asyncio
from googletrans import Translator

# Load dữ liệu
input_file = "output_ocr/output_ocr_raw.xlsx"
output_file = "output_ocr/output_ocr_translated.xlsx"

df = pd.read_excel(input_file)

async def translate_text(text):
    async with Translator() as translator:
        try:
            result = await translator.translate(text, src='zh-CN', dest='vi')
            return result.text
        except Exception as e:
            print(e)
            return "[Lỗi dịch]"

# Tạm gán Âm Hán Việt bằng chính chuỗi Hán (nếu chưa có cơ chế tra âm Hán Việt từng chữ)
df["Âm Hán Việt"] = df["Hán char"]

def sync_translate_text(text):
    output = asyncio.run(translate_text(text))
    print(output)
    return output

# Dịch nghĩa thuần Việt
df["Nghĩa thuần Việt"] = df["Hán char"].apply(sync_translate_text)

# Xuất ra Excel
df.to_excel(output_file, index=False)
print(f"✅ Xuất file: {output_file}")
