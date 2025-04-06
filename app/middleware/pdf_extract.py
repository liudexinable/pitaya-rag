
import os
import fitz
from app.util.minio_util import upload_to_minio


# 3. PDF处理模块
class PDFProcessor:
    def __init__(self):
        pass
    def extract_elements(self, pdf_path):
        """提取并处理PDF元素"""
        doc = fitz.open(pdf_path)
        elements = []

        for page_num in range(len(doc)):
            page = doc.load_page(page_num)

            # 处理文本块
            text_blocks = page.get_text("blocks")
            for block in text_blocks:
                x0, y0, x1, y1, text, _, _ = block
                if text.strip():
                    elements.append({
                        "type": "text",
                        "content": text,
                        "page": page_num,
                        "position": (x0, y0, x1, y1)
                    })

            # 处理图片
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # 暂存图片并上传
                temp_path = f"/tmp/page{page_num}_img{img_index}.{image_ext}"
                with open(temp_path, "wb") as f:
                    f.write(image_bytes)

                s3_path = upload_to_minio(temp_path,f"pages/{os.path.basename(temp_path)}")
                os.remove(temp_path)

                elements.append({
                    "type": "image",
                    "s3_path": s3_path,
                    "page": page_num,
                    "position": page.get_image_rects(xref)[0]
                })

        return elements

    # 2. 语义分组模块f
    def group_elements(self,elements, vertical_threshold=20):
        """根据垂直位置进行元素分组"""
        sorted_elements = sorted(elements, key=lambda x: (x['page'], x['position'][1]))
        groups = []
        current_group = []
        prev_bottom = None

        for elem in sorted_elements:
            page = elem['page']
            y0 = elem['position'][1]
            y1 = elem['position'][3]

            if current_group and (
                    page != current_group[-1]['page'] or
                    (y0 - prev_bottom) > vertical_threshold
            ):
                groups.append(current_group)
                current_group = []

            current_group.append(elem)
            prev_bottom = y1

        if current_group:
            groups.append(current_group)
        return groups