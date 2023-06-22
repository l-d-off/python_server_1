import json
from io import BytesIO
from PIL import Image, ImageTk
from flask import Flask, request
import tkinter as tk
from program import algorithm as make

app = Flask(__name__)


@app.route('/process_image', methods=['POST'])
def process_image():
    image_data = request.get_data()  # получение из запроса
    if not image_data:
        return 'File not found', 400

    image = Image.open(BytesIO(image_data))
    print("File received")
    print(image)

    path = 'input.png'
    image.save(path)
    result = make(path)
    dict_list = [data.to_dict() for data in result]
    json_data = json.dumps(dict_list, ensure_ascii=False)
    return json_data


def show_image(image):
    window = tk.Tk()
    window.title("Image Viewer")
    tk_image = ImageTk.PhotoImage(image)
    label = tk.Label(window, image=tk_image)
    label.pack()
    window.mainloop()


host_name = "192.168.1.69"
port_number = 4000
if __name__ == '__main__':
    app.run(host=host_name, port=port_number)
