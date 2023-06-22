import cv2
import pytesseract
from classes import Points, Word, Draw, String, Point, Size
from detect_horizontal_lines import detect_horizontal_lines as dhl
from detect_horizontal_lines import get_fields_rectangle_parameters as get_frp

pytesseract.pytesseract.tesseract_cmd = r'E:\Program Files\Tesseract-OCR\tesseract.exe'


# start = time.time()

# image_path = "1.png"
# img = cv2.imread(image_path)
# img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)


# img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
# _, img = cv2.threshold(img, 127, 255, 0)

# Page segmentation modes:
#   0    Orientation and script detection (OSD) only.
#   1    Automatic page segmentation with OSD.
#   2    Automatic page segmentation, but no OSD, or OCR. (not implemented)
#   3    Fully automatic page segmentation, but no OSD. (Default)
#   4    Assume a single column of text of variable sizes.
#   5    Assume a single uniform block of vertically aligned text.
#   6    Assume a single uniform block of text.
#   7    Treat the image as a single text line.
#   8    Treat the image as a single word.
#   9    Treat the image as a single word in a circle.
#  10    Treat the image as a single character.
#  11    Sparse text. Find as much text as possible in no particular order.
#  12    Sparse text with OSD.
#  13    Raw line. Treat the image as a single text line,
#        bypassing hacks that are Tesseract-specific.


# составляем удобный для использования список данных (таких, как выше)
def get_words(img):
    custom_config = r'--oem 3 --psm 6'
    data = pytesseract.image_to_data(img, lang="rus", config=custom_config)
    words: list[Word] = []
    for i, word_data in enumerate(data.splitlines()):
        if i == 0:
            continue
        word_data = word_data.split()
        word_data_0 = int(word_data[0])
        if word_data_0 == 4 or word_data_0 == 5:
            words.append(
                Word(
                    level=word_data[0],
                    line_num=word_data[4],
                    point=Point(*word_data[6:8]),
                    size=Size(*word_data[8:10]),
                    text=word_data[11] if len(word_data) == 12 else None
                )
            )
    return words


# считаем среднюю высоту строк
def get_average_strings_height(words):
    sum_of_heights = 0
    count_of_heights = 0
    for word in words:
        if word.has_text():
            x, y, w, h = word.get_xy_wh()
            sum_of_heights += h
            count_of_heights += 1
    return sum_of_heights / count_of_heights


draw = Draw([], [], [], [], img=None)


# сужаем слишком большие квадраты с помощью средней высоты
def make_big_boxes_smaller(words, img):
    draw.img = img
    average_height = get_average_strings_height(words)
    words_rectangle_parameters = []
    new_words_rectangle_parameters = []
    for word in words:
        if word.has_text():
            x, y, w, h = word.get_xy_wh()
            if h > average_height * 1.5:  # h > 20
                # хардкод :(
                if word.text == "_":
                    words.remove(word)
                    continue
                _words = get_words(img[y:y + h, x:x + w])
                for _word in _words:
                    if _word.has_text():
                        _x, _y, _w, _h = _word.get_xy_wh()
                        # отрисовываем на общей картинке, т.к. если отрисовывать на подкартинке, то отрисовка будет неполной
                        word.x = x = x + _x
                        word.y = y = y + _y
                        word.w = w = _w
                        word.h = h = _h
                        new_words_rectangle_parameters.append(
                            [(x - 2, y - 2), (x + w + 1, y + h + 1), (0, 120, 120), 2])
            else:
                words_rectangle_parameters.append(
                    [(x - 2, y - 2), (x + w + 1, y + h + 1), (0, 0, 240), 2])
    draw.words_parameters = words_rectangle_parameters
    draw.new_words_parameters = new_words_rectangle_parameters


# номера строк теперь определяем не по line[1], а вычисляем по чередованию line[0]
# список строк (доступны по номеру)
def get_strings(words):
    strings_rectangle_parameters = []
    strings: dict[int, String] = {}
    current_string_number = 0
    for word in words:
        if word.level == 4:
            current_string_number += 1
        if word.has_text():
            x, y, w, h = word.get_xy_wh()
            # получаем координаты строки
            if current_string_number not in strings:
                strings[current_string_number] = String(
                    points=Points(
                        start=Point(x, y),
                        end=Point(x + w, y + h)
                    ),
                    words=[],
                    fields={}
                )
            else:
                points = strings[current_string_number].points
                min_x, min_y = points.start.get_tuple()
                max_x, max_y = points.end.get_tuple()
                strings[current_string_number].set_points(
                    points=Points(
                        start=Point(min(x, min_x), min(y, min_y)),
                        end=Point(max(x + w, max_x), max(y + h, max_y))
                    )
                )
            strings[current_string_number].append_word(word)
    # обводим строки
    # начало строки - минимальные x и y, конец строки - максимальные x + w и y + h
    for string in strings.values():
        points = string.points
        start_x, start_y = points.start.get_tuple()
        end_x, end_y = points.end.get_tuple()
        strings_rectangle_parameters.append([
            (start_x - 2 - 3, start_y - 2 - 3),
            (end_x + 1 + 3, end_y + 1 + 3),
            (2, 97, 0), 2
        ])
    return strings


# выводим пары строка-поле, где поле входит в строку или относится к строке
def append_fields_to_strings(fields, strings):
    string_number = field_number = 1
    while 1:
        string_points = strings[string_number].points
        string_start_x, string_start_y = string_points.start.get_tuple()
        string_end_x, string_end_y = string_points.end.get_tuple()

        field_points = fields[field_number].get_points()
        field_start_x, field_start_y = field_points.start.get_tuple()
        field_end_x, field_end_y = field_points.end.get_tuple()

        # если поле находится внутри строки, то оно относится к этой строке
        if 1 \
                and string_start_x - 5 < field_start_x \
                and string_start_y - 5 < field_start_y \
                and string_end_y + 5 > field_end_y:
            strings[string_number].append_field(field_number, fields[field_number])
            # если поле находится справа от строки, то оно относится к этой строке
            if string_end_x + 5 < field_end_x:
                string_number += 1
            field_number += 1
        # если текущая строка - не первая, а поле находится до неё
        # то поле относится к предыдущей строке
        elif string_number != 1 and field_end_y < string_start_y:
            strings[string_number - 1].append_field(field_number, fields[field_number])
            field_number += 1
        else:
            string_number += 1
        # странный код - почему заканчиваем цикл, если строка - последняя?
        if string_number - 1 == len(strings) or field_number - 1 == len(fields):
            break


# append_fields_to_strings()


# выводим номера строк-смыслов для соответствующих полей выше
# DEPRECATED
def get_string_numbers_and_field_numbers_list(strings):
    string_numbers = []  # номера строк, у которых есть список полей / _if_fields_numbers_is_not_empty
    string_numbers_and_field_numbers_list = []
    for string_number, string in strings.items():
        field_numbers = string.fields.keys()
        if field_numbers:
            string_numbers.append(string_number)
    current_string_number = 1  # было использовано ранее
    for string_number in string_numbers:
        string_numbers_and_field_numbers_list.append((
            list(range(current_string_number, string_number + 1)),
            list(strings[string_number].fields.keys())
        ))
        current_string_number = string_number + 1
    return string_numbers_and_field_numbers_list


def put_text_on_image(img, text, start_point):
    font = cv2.FONT_HERSHEY_COMPLEX
    font_scale = 0.5
    font_thickness = 1
    cv2.putText(img, text, start_point,
                font, font_scale, (0, 0, 0), font_thickness)


class DataElement:
    def __init__(self, text, x, y):
        self.text = text
        self.x = x
        self.y = y

    def to_dict(self):
        return {
            'text': self.text,
            'x': self.x,
            'y': self.y
        }

    def __str__(self):
        dict = self.to_dict()
        return f"{dict['text']}\n{dict['x']}\n{dict['y']}\n"


# реализация через ходьбу по strings и проверке fields на пустоту
def get_result(img, strings, copy):
    data_list: list[DataElement] = []  # io
    output = ""
    for string in strings.values():
        if not string.fields:
            for word in string.words:
                output += word.text + " "
            continue
        words = string.words  # список слов в строке с полями
        fields = string.fields
        fields_length = len(fields)
        field_numbers = string.get_field_numbers()
        field_index = 0
        for word in words:
            # если закончились поля, сохраняем оставшийся текст в строке
            if field_index == fields_length:
                output += word.text
                continue
            # слово и координаты
            word_points = word.get_points()
            word_start_x, word_start_y = word_points.start.get_tuple()
            word_end_x, word_end_y = word_points.end.get_tuple()
            # поле и координаты
            field_number = field_numbers[field_index]
            field_points = fields[field_number].get_points()
            field_start_x, field_start_y = field_points.start.get_tuple()
            field_end_x, _ = field_points.end.get_tuple()
            # если слово после поля, то сохраняем смысл до поля, вводим поле
            if word_start_x > field_end_x and word_end_y + 5 > field_start_y:
                field_index += 1
                data_list.append(DataElement(output, -1, -1))
                data_list.append(DataElement(None, field_start_x, field_start_y - 6))
                print(output + " >")
                value = input()
                put_text_on_image(copy, value, (field_start_x, field_start_y - 6))
                output = word.text
            # если слово последнее, то вводим поля справа и снизу
            elif word == words[-1] and field_index != fields_length:
                # несколько строк
                output += word.text
                data_list.append(DataElement(output, -1, -1))
                print(output + " >")
                for i in range(field_index, fields_length):
                    value = input()
                    number = field_numbers[i]
                    points = fields[number].get_points()
                    x, y = points.start.get_tuple()
                    put_text_on_image(copy, value, (x, y - 6))
                    data_list.append(DataElement(None, x, y - 6))
                output = ""
            else:
                output += word.text + " "
        if output != "":
            print(output)
            data_list.append(DataElement(output, -1, -1))
            output = ""
    if output != "":
        print(output)
        data_list.append(DataElement(output, -1, -1))
    # return data_list

    print('не психуй')
    # cv2.imshow('Result', copy)
    # cv2.destroyAllWindows()
    # cv2.waitKey(0)
    show(copy)


def show(image, i=0):
    # percent by which the image is resized
    scale_persent = 60
    # calculate the 50 percent of original dimensions
    width = int(image.shape[1] * scale_persent / 100)
    height = int(image.shape[0] * scale_persent / 100)
    # dsize
    dsize = (width, height)
    # resize image
    output = cv2.resize(image, dsize)
    cv2.imshow(f'Result{i}', output)
    cv2.waitKey(0)


def preprocess_image(image):
    # Бинаризация изображения
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    show(gray, 1)
    _, binary = cv2.threshold(gray, 112, 255, cv2.THRESH_BINARY)
    show(binary, 2)

    # kernel = np.ones((2, 2), np.uint8)
    # dilated_image = cv2.dilate(binary, kernel, iterations=1)
    # show(dilated_image)

    # Фильтрация шума
    # denoised = cv2.medianBlur(binary, 3)
    # show(denoised)

    return binary


def algorithm(path='9.png'):
    img = cv2.imread(path)
    copy = img.copy()
    show(img, 3)
    # img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
    img = preprocess_image(img)

    words = get_words(img)
    make_big_boxes_smaller(words, img)

    strings = get_strings(words)
    fields = dict(enumerate(dhl(path, img), start=1))
    draw.fields_parameters = get_frp(fields)

    append_fields_to_strings(fields, strings)
    return get_result(img, strings, copy)


# end = time.time() - start
# print(f"Время: {end}")

algorithm()
