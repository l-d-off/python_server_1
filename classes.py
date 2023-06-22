import cv2


def get_int(element):
    return element if element is int else int(element)


class Point:
    def __init__(self, x, y):
        self.x = get_int(x)
        self.y = get_int(y)

    def get_tuple(self):
        return self.x, self.y

    def get_end(self, size):
        return Point(self.x + size.width, self.y + size.height)


class Size:
    def __init__(self, width, height):
        self.width = get_int(width)
        self.height = get_int(height)

    def get_tuple(self):
        return self.width, self.height


class Points:
    def __init__(self, start: Point, end: Point):
        self.start = start
        self.end = end


class Word:
    def __init__(self, level, line_num, point, size, text):
        self.level = get_int(level)
        self.line_num = get_int(line_num)
        self.point = point
        self.size = size
        self.text = text

    def get_xy_wh(self):
        return *self.point.get_tuple(), *self.size.get_tuple()

    def get_start_point(self):
        return self.point

    def get_end_point(self):
        return self.point.get_end(self.size)

    def get_points(self):
        return Points(
            self.get_start_point(),
            self.get_end_point()
        )

    def has_text(self):
        return self.text is not None


class Field:
    def __init__(self, point, size):
        self.point = point
        self.size = size

    def get_start_point(self):
        return self.point

    def get_end_point(self):
        return self.point.get_end(self.size)

    def get_points(self):
        return Points(
            self.get_start_point(),
            self.get_end_point()
        )


# координаты одной строки
# список слов
# список координат слов
class String:  # by string number
    def __init__(self, points: Points, words: list[Word], fields: dict[int, Field]):
        self.points = points
        self.words = words
        self.fields = fields

    def set_points(self, points):
        self.points = points

    def append_word(self, word):
        self.words.append(word)

    def append_field(self, field_number, field):
        self.fields[field_number] = field

    def get_field_numbers(self):
        return list(self.fields.keys())


class Draw:
    def __init__(
            self,
            words_parameters,
            new_words_parameters,
            strings_parameters,
            fields_parameters,
            img
    ):
        self.words_parameters = words_parameters
        self.new_words_parameters = new_words_parameters
        self.strings_parameters = strings_parameters
        self.fields_parameters = fields_parameters
        self.img = img

    def draw_rectangle(self, parameters_list):
        for parameters in parameters_list:
            cv2.rectangle(self.img, *parameters)

    def draw_words_rectangle(self):
        self.draw_rectangle(self.words_parameters)

    def draw_new_words_rectangle(self):
        self.draw_rectangle(self.new_words_parameters)

    def draw_strings_rectangle(self):
        self.draw_rectangle(self.strings_parameters)

    def draw_fields_rectangle(self):
        self.draw_rectangle(self.fields_parameters)
