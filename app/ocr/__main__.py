from paddleocr import PaddleOCR
from paddleocr import PPStructure,draw_structure_result,save_structure_res
from PIL import Image, ImageDraw, ExifTags
import re, sys
import json, os

def subQuestion(result, img, from_box):
    width, height = img.size
    last_box = from_box[:]
    # 克隆 list 防止干扰整体
    
    left_top = last_box[0]
    
    right_top = last_box[1]
    right_top[0] += 0.2 * width
    # 向右延伸

    right_bottom = last_box[2]
    right_bottom[0] += 0.2 * width
    right_bottom[1] += 0.1 * height
    # 向右向下延伸

    left_bottom = last_box[3]
    left_bottom[0] += 0.05 * width
    left_bottom[1] += 0.1 * height
    # 向左收缩，向下延伸
    
    sub_lines = []
    for line in result:
        next_box = line[0]
        text = line[1][0]
        # 是选项
        if not re.match("^.{0,7}[a-zA-Z0-9]\s*[.:。：\]】]\s*\S{2,}", text): break
        # 是否有其它行（选项）包含在该小题题干下
        if next_box[0][0] > left_top[0]\
            and next_box[0][1] < left_top[1]\
            and next_box[2][0] - right_bottom[0] < 0.05 * width \
            and next_box[2][1] - right_bottom[1] < 0.05 * height:
            sub_lines.append(line)
            sub_lines.extend(subQuestion(result, img, from_box=next_box))
    return sub_lines


def main():
    image_path = "temp.jpg"
    ocr = PaddleOCR(det_db_box_thresh=0.3, use_angle_cls = True, use_gpu = False, show_log = False,\
        lang=sys.argv[1] or "ch")

    result = ocr.ocr(image_path, cls=True)[0]
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
        
    
    for line in result:
        text = line[1][0]
        draw.polygon([tuple(int(n) for n in xy) for xy in line[0]], (255, 0, 0, 10), outline=(255, 0, 0, 255))
        if re.match("^.{0,7}\d{1,3}\s*[.:。：\]】]", text):
            # 是小题题干
            print(line[1][0])
            ques = subQuestion(result, img, from_box=line[0])
            print(str(ques) + "\n")
            for line in ques:
                draw.polygon([tuple(int(n) for n in xy) for xy in line[0]], (0, 255, 0, 40), outline=(0, 255, 0, 255))

    
    img.save("output.jpg")
    
    # text = "\n".join([line[1][0] for line in result])

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
    main()