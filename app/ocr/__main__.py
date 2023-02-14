from paddleocr import PaddleOCR
from PIL import Image, ImageDraw, ExifTags
import re, sys

def subQuestion(result, img, ques_box):
    width, height = img.size
    draw = ImageDraw.Draw(img, "RGBA")
    
    
    left_top = ques_box[0]
    
    right_top = ques_box[1]
    right_top[0] += 0.2 * width
    # 向右延伸

    right_bottom = ques_box[2]
    right_bottom[0] += 0.2 * width
    right_bottom[1] += 0.2 * height
    # 向右向下延伸

    left_bottom = ques_box[3]
    left_bottom[0] += 0.05 * width
    left_bottom[1] += 0.2 * height
    # 向左收缩，向下延伸
    
    draw.polygon([tuple(int(n) for n in xy) for xy in ques_box], (0, 255, 0, 80), outline=(0, 255, 0, 255))
     
    for line in result:
        box = line[0]
        text = line[1][0]
        draw.polygon([tuple(int(n) for n in xy) for xy in box], (255, 0, 0, 10), outline=(255, 0, 0, 255))
        # 是否有其它行（选项）包含在该小题题干下
        if box[0][0] > left_top[0]\
            and box[0][1] > left_top[1]\
            and box[2][0] - right_bottom[0] < 0.05 * height \
            and box[2][1] - right_bottom[1] < 0.05 * width \
            and re.match("^.{0,7}[a-zA-Z]\s*[.:。：\]】]\s*\S{2,}", text):
            print(str(line)+"\n")
            draw.polygon([tuple(int(n) for n in xy) for xy in box], (0, 0, 255, 80), outline=(0, 0, 255, 255))

            

def main():
    TEMP_IMG = "temp.jpg"
    ocr = PaddleOCR(use_angle_cls = True, use_gpu= False, show_log = False,\
        lang=sys.argv[1] if len(sys.argv) > 1 else "ch")
    result = ocr.ocr(TEMP_IMG, cls=True)[0]

    img = Image.open(TEMP_IMG)
    
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

    
    for line in result:
        text = line[1][0]
        if re.match("^.{0,7}\d{1,3}\s*[.:。：\]】]", text):
            # 是小题题干
            subQuestion(result, img, ques_box=line[0])
    
    img.save("output.jpg")
    
    # text = "\n".join([line[1][0] for line in result[0]])

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