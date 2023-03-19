from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ExifTags
import re, sys, logging
logging.basicConfig(level=logging.DEBUG,
    format='collector::%(asctime)s.%(msecs)03d-%(levelname)s-%(message)s',
    datefmt='%H:%M:%S')
logging.info("Scan Module 初始化完成！")



def Image2Document(image_path = "temp.jpg", lang = "ch"):
    ocr = PaddleOCR(det_db_box_thresh=0.3, use_angle_cls = True, use_gpu = False, show_log = False,
        lang=lang)

    ocr_result = ocr.ocr(image_path, cls=True)[0]

    text = "\n".join([line[1][0] for line in ocr_result])

    # 过滤连续空格
    text = re.sub(r"(\S)\s\s*", r"\1\n", text)

    # 替换英文单词后的换行
    text = re.sub(r"([a-zA-Z0-9,.?!;])\n", r"\1 ", text)
    # 删除其它字符后的换行（标点后保留换行）
    text = re.sub(r"([^,\.?!;:'\"%+~\-\_=/\()，。？！；：、\s])\n", r"\1", text)

    # 英文和其它字符间添加空格
    text = re.sub(r"([^a-zA-Z0-9,\.?!;:'\"%+~\-\_=/\()，。？！；：、（）\s])([a-zA-Z0-9,\.\?!;])",
                r"\1 \2", text)
    text = re.sub(r"([a-zA-Z0-9,\.\?!;])([^a-zA-Z0-9,\.?!;:'\"%+~\-\_=/\()，。？！；：、（）\s])",
                r"\1 \2", text)
    print(text)
    
    logging.info("完成！")
    return text


if __name__ == "__main__":
    Image2Document()