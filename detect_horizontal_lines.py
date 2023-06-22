# тут мы ищем длинные горизонтальные линии - поля для ввода
import cv2
from classes import Points, Field, Point, Size


def __detect_horizontal_lines(image_path, min_line_length=20):
    # Загрузка изображения и преобразование в оттенки серого
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Адаптивная пороговая обработка
    # threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)
    # Обычная пороговая обработка
    threshold_value = 128
    _, threshold = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # Морфологическая операция для удлинения горизонтальных линий
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (50, 1))
    horizontal_lines = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

    # Поиск контуров горизонтальных линий
    contours, hierarchy = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Фильтрация контуров по длине или площади
    # filtered_contours = [[cnt, print(cv2.arcLength(cnt, False))][0] for cnt in contours if
    #                      cv2.arcLength(cnt, False) > min_line_length]
    filtered_contours = [cnt for cnt in contours if
                         cv2.arcLength(cnt, False) > min_line_length]
    # cv2.arcLength(image, True) вдвое больше реальной длины линий, можно урезать
    # вывод идет с нижних линий к верхним
    # для False длина реальная
    # сигнатура: False - кривая не замкнута, True - замкнута

    # Рисование прямоугольников вокруг найденных линий на изображении и сохранение координат линий
    result = image.copy()
    lines_points = []
    for cnt in filtered_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.rectangle(result, (x - 2, y - 2), (x + w + 1, y + h + 1), (0, 0, 255), 1)
        lines_points.append(((x, y), (x + w, y + h)))

    # Вывод координат найденных линий (сверху вниз)
    lines_points.reverse()
    for idx, coords in enumerate(lines_points, start=1):
        print(f"Line {idx}: {coords}")

    # Сохранение результата
    cv2.imwrite('result.jpg', result)


def detect_horizontal_lines(image_path, img, min_line_length=10):
    # Загрузка изображения и преобразование в оттенки серого
    image = cv2.imread(image_path)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Адаптивная пороговая обработка
    # threshold = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 15, 10)
    # Обычная пороговая обработка
    threshold_value = 128
    _, threshold = cv2.threshold(gray, threshold_value, 255, cv2.THRESH_BINARY_INV)

    # Морфологическая операция для удлинения горизонтальных линий
    horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (45, 1))
    horizontal_lines = cv2.morphologyEx(threshold, cv2.MORPH_OPEN, horizontal_kernel, iterations=1)

    # Поиск контуров горизонтальных линий
    contours, hierarchy = cv2.findContours(horizontal_lines, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Фильтрация контуров по длине или площади
    # filtered_contours = [[cnt, print(cv2.arcLength(cnt, False))][0] for cnt in contours if
    #                      cv2.arcLength(cnt, False) > min_line_length]
    filtered_contours = [cnt for cnt in contours if cv2.arcLength(cnt, False) > min_line_length]
    # cv2.arcLength(image, True) вдвое больше реальной длины линий, можно урезать
    # вывод идет с нижних линий к верхним
    # для False длина реальная
    # сигнатура: False - кривая не замкнута, True - замкнута

    # Рисование прямоугольников вокруг найденных линий на изображении и сохранение координат линий
    fields = []
    for cnt in filtered_contours:
        x, y, w, h = cv2.boundingRect(cnt)
        fields.append(Field(
            Point(x, y),
            Size(w, h)
        ))
    fields.reverse()

    return fields


def get_fields_rectangle_parameters(fields: list[Field] | dict[int, Field]):
    fields_rectangle_parameters = []
    _fields = fields if fields is list else fields.values()
    for field in _fields:
        points = field.get_points()
        start_x, start_y = points.start.get_tuple()
        end_x, end_y = points.end.get_tuple()
        fields_rectangle_parameters.append([
            (start_x - 2, start_y - 2),
            (end_x + 1, end_y + 1),
            (255, 0, 0), 1
        ])


if __name__ == "__main__":
    image_path = '9.png'
    __detect_horizontal_lines(image_path)
