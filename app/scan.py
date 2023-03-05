import logging
logging.basicConfig(level=logging.DEBUG,
    format='collector_ocr::%(asctime)s.%(msecs)03d-%(levelname)s-%(message)s',
    datefmt='%H:%M:%S')
logging.info("初始化...")

from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ExifTags
import re, sys


def getNextLine(from_lines):
    width, height = img.size
    from_box = from_lines[-1][0]
    # 克隆 list 防止干扰整体

    left_top = from_box[0]
    left_top[0] -= 0.1 * width
    # 向左延伸
    
    right_top = from_box[1]
    right_top[0] += 0.3 * width
    # 向右延伸

    right_bottom = from_box[2]
    right_bottom[0] += 0.3 * width
    right_bottom[1] += 0.1 * height
    # 向右向下延伸

    left_bottom = from_box[3]
    left_bottom[0] -= 0.1 * width
    left_bottom[1] += 0.1 * height
    # 向左向下延伸
    
    for next_line in ocr_result:
        next_box = next_line[0]
        # 获取到的下一行需包含在该行下
        if (next_box[0][0] > left_top[0]\
          and next_box[0][1] > left_top[1]\
          and next_box[2][0] - right_bottom[0] < 0.05 * width \
          and next_box[2][1] - right_bottom[1] < 0.05 * height):
            # return None
        # 获取到的下一行不能与已有的重复
        # if next(filter(lambda line: line==next_line, from_lines), None) == None:
            return next_line
        # return None

def newLine(from_lines, do_action, new_line=None):
    if not new_line:
        # 获取新行
        new_line = getNextLine(from_lines)

    action = do_action(new_line) if new_line else "STOP" # 对新行的处理
    logging.info("FROM {} FOUND {} TO {}".format(from_lines[-1][1][0], new_line, action))
    if action == "NEW_LINE": # 新行
        # 直接将获取到的新行加入
        from_lines.append(new_line)
    elif action == "CONNECT_LINE": # 延续旧行（连结换行）
        # 扩展右下和左下的 box
        box = from_lines[-1][0]
        box[2] = new_line[0][2]
        box[3] = new_line[0][3]
        from_lines[-1][0] = box
        # 将下段文本连接到上行文字
        text = list(from_lines[-1][1])
        text[0] += new_line[1][0]
        from_lines[-1][1] = tuple(text)
    elif action == "STOP":
        return from_lines
    
    from_lines = newLine(from_lines, do_action)
    
    return from_lines

def subOptions(from_line):
    # 通过 选择题题干 获取 选择题选项
    options = []
    
    width, height = img.size
    from_box = from_line[0][:]
    # 克隆 list 防止干扰整体

    left_top = from_box[0]
    left_top[0] -= 0.05 * width
    # 向左延伸
    
    right_top = from_box[1]
    right_top[0] += 0.05 * width
    # 向右延伸

    right_bottom = from_box[2]
    right_bottom[0] += 0.05 * width
    right_bottom[1] += 0.2 * height
    # 向右向下延伸

    left_bottom = from_box[3]
    left_bottom[0] -= 0.05 * width
    left_bottom[1] += 0.2 * height
    # 向左向下延伸
    
    for next_line in ocr_result:
        next_box = next_line[0]
        next_text = next_line[1][0]
        # 获取到的选项需包含在题干下
        if not (next_box[0][0] > left_top[0]\
          and next_box[0][1] > left_top[1]\
          and next_box[2][0] - right_bottom[0] < 0.05 * width \
          and next_box[2][1] - right_bottom[1] < 0.05 * height): continue
        # 获取到的下一行不能与已有的重复
        # if next(filter(lambda line: line==next_line, from_lines), None) == None:
        
        # 文本符合 新题号 则退出
        if re.match("^\D{0,7}\d{1,3}\s*[.:。：\]】]", next_text): break

        # 文本符合 新选项 则添加新选项
        is_option = re.match("^[^a-zA-Z]{0,7}([a-zA-Z])\s*[.:。：\]】]\s*(\S{2,}.*)", next_text)
        if is_option:
            options.append({
                "choice": is_option.group(1),
                "text": is_option.group(2),
                "box": next_box
            })
        else:
            # 不是新题号也不是新选项
            # 则连接上条选项的文本（是换行）
            if len(options): options[-1]["text"] += next_text
    return options
        

def subQuestion(from_line):
    # 判断是不是题干
    def do_action(new_line):
        text = new_line[1][0]
        if re.match("^.{0,7}\d{1,3}\s*[.:。：\]】]", text):
            # 发现题号停止
            return "STOP"
        elif re.match("^.{0,7}[a-zA-Z]\s*[.:。：\]】]\s*\S{2,}", text):
            # 新选项新行
            return "NEW_LINE"
        else:
            # 其它情况说明是换行
            return "CONNECT_LINE"

    
    is_ques = re.match("^\D{0,7}(\d{1,3})\s*[.:。：\]】]\s*(\S{2,}.*)", from_line[1][0])
    if is_ques:
        return {
            'type': "choice_ques",
            'num': is_ques.group(1),
            'text': is_ques.group(2),
            'options': subOptions(from_line),
            'box': from_line[0]
        }


def Image2Document(image_path = "temp.jpg", lang = "ch"):
    logging.info("准备 OCR...")
    ocr = PaddleOCR(det_db_box_thresh=0.3, use_angle_cls = True, use_gpu = False, show_log = False,
        lang=lang)

    logging.info("开始 OCR...")
    global ocr_result, img
    ocr_result = ocr.ocr(image_path, cls=True)[0]
    logging.info("开始处理文档...")
    img = Image.open(image_path)
    
    # 修复 exif 中指定的旋转（tks chatgpt）
    for orientation in ExifTags.TAGS.keys():
        if ExifTags.TAGS[orientation] == 'Orientation':
            break
    try:
        exif = dict(img._getexif().items())
        if exif[orientation] == 3:
            img = img.rotate(180, expand=True)
        elif exif[orientation] == 6:
            img = img.rotate(270, expand=True)
        elif exif[orientation] == 8:
            img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        # No EXIF data present
        pass
    draw = ImageDraw.Draw(img, "RGBA")
        
    
    docment_result = []
    for line in ocr_result:
        text = line[1][0]
        draw.polygon([tuple(int(n) for n in xy) for xy in line[0]], (255, 0, 0, 10), outline=(255, 0, 0, 255))
        ques = subQuestion(line)
        if ques:
            docment_result.append(ques)
            draw.polygon([tuple(int(n) for n in xy) for xy in ques["box"]], (0, 0, 255, 40), outline=(0, 0, 255, 255))
                
    img.save("output.jpg")
    
    logging.info("完成！")
    return docment_result
    
    # text = "\n".join([line[1][0] for line in ocr_result])

    # # filter consecutive whitespace
    # text = re.sub(r"(\S)\s\s*", r"\1\n", text)

    # # replace line break with space after engilsh words
    # text = re.sub(r"([a-zA-Z0-9,.?!;])\n", r"\1 ", text)
    # # delete line break after other characters
    # text = re.sub(r"(\S)\n", r"\1", text)

    # # add spaces around english words and others characters
    # text = re.sub(r"([^a-zA-Z0-9,\.?!;:'\"%+~\-\_=/\()，。？！；：、\s])([a-zA-Z0-9,\.\?!;])",
                # r"\1 \2", text)
    # text = re.sub(r"([a-zA-Z0-9,\.\?!;])([^a-zA-Z0-9,\.?!;:'\"%+~\-\_=/\()，。？！；：、\s])",
                # r"\1 \2", text)
    # print(text)


if __name__ == "__main__":
    Image2Document()