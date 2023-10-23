import os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import scrolledtext
from tkinter.messagebox import showinfo
import tkinter as tk
from PIL import ImageTk, Image
from datetime import date, datetime
import imghdr

from rgb_ps_ccws import areaLeaf as al_rgb
from lab_pr_ca import areaLeaf as al_lab

class App(tk.Tk):

    image_folder = ""
    result_folder = "result/"
    log_file = ""
    images = []
    result_images = []
    viewed_images = []
    al_per_image = {}
    enable_alg = ["RGB_PS_CCWS", "LAB_PR_CA"]
    main_w = 400

    def selectFolder(self):
        self.image_folder = fd.askdirectory()
        self.images = os.listdir(self.image_folder)

        for file in self.images:
            if not imghdr.what(os.path.join(self.image_folder, file)):
                self.images.remove(file)

        self.info.config(state=NORMAL)
        self.info.delete("1.0", END)
        self.info_text = f"Выбранная папка: {self.image_folder}\nВсего изображений: {len(self.images)}\n\n"
        self.info.insert(INSERT, self.info_text)
        self.highlightWord(["Выбранная папка", "Всего изображений"], self.info_text, "dark green")
        self.info.config(state=DISABLED)

        self.geometry(f"{self.main_w}x300")
        self.btn_start_ac.config(state=ACTIVE)
        self.middle_frame.pack(side=TOP, padx=5, pady=2, fill=BOTH)

    def areaCalculation(self):
        self.btn_start_ac.config(state=DISABLED)
        selected_algorithm = self.selected_alg.get()
        self.result_folder = os.path.join(self.result_folder, selected_algorithm)
        if selected_algorithm == self.enable_alg[0]:
            af = al_rgb(self.images, self.image_folder, self.result_folder)
            self.al_per_image = af.run()
        else:
            af = al_lab(self.images, self.image_folder, self.result_folder)
            self.al_per_image = af.run()

        self.result_images = os.listdir(self.result_folder)
        for i, img_name in enumerate(self.images):
            self.result_preview.insert("", END, iid=str(i), text=img_name, values=[img_name])
            for rimg in self.result_images:
                if img_name.split('.')[0] in rimg:
                    self.result_preview.insert(str(i), END, text=rimg, values=[rimg])

        self.geometry(f"{self.main_w}x550")
        self.bottom_frame.pack(side=BOTTOM, padx=5, pady=3, fill=BOTH)

        self.info_text += f"Выбранный алгоритм: {selected_algorithm}\n\n"
        current_date = date.today()
        now = datetime.now()
        current_time = now.strftime("%H-%M")
        self.log_file = f"log_{current_date}-{current_time}.txt"
        with open(self.log_file, "w") as file:
            text = f"Выбранный алгоритм: {selected_algorithm}\n\n"
            file.write(text)
            for key, value in self.al_per_image.items():
                text = f"Для изображения {key}:\n"
                file.write(text)
                self.info_text += text
                for i, v in enumerate(value):
                    text = f"- объект №{i+1}, площадь: {v[0]} pix, {v[1]} cm2\n"
                    file.write(text)
                    self.info_text += text
                file.write("\n")
                self.info_text += "\n"

        self.info.config(state=NORMAL)
        self.info.delete("1.0", END)
        self.info.insert(INSERT, self.info_text)
        self.highlightWord(["Выбранная папка", "Всего изображений", "площадь", "pix", "cm2", "Выбранный алгоритм"],
                           self.info_text, "dark green")
        self.info.config(state=DISABLED)

    def viewImage(self, event):
        selected_item = self.result_preview.focus()
        item_details = self.result_preview.item(selected_item)

        image = Image.open(f"{self.result_folder}/{item_details.get('values')[0]}")
        width, height = image.size
        self.tk_image = ImageTk.PhotoImage(image.resize((int(width/2), int(height/2))))
        if self.tk_image not in self.viewed_images:
            self.viewed_images.append(self.tk_image)

        image_viewer = Toplevel(self)
        image_viewer.title(item_details.get('values')[0])
        image_viewer.geometry(f"{int(width/2)+10}x{int(height/2)}")
        canvas = tk.Canvas(image_viewer)
        index = self.viewed_images.index(self.tk_image)
        canvas.create_image(0, 0, anchor=NW, image=self.viewed_images[index])
        canvas.pack(padx=5, pady=5, expand=True, fill=BOTH)

    def finishApp(self):
        if not self.confirm_save.get():
            os.remove(self.log_file)
        self.destroy()

    def highlightWord(self, words, text, color):
        for l, line in enumerate(text.split("\n")):
            for word in words:
                if word in line:
                    start_index = line.index(word)
                    end_index = start_index + len(word)
                    self.info.tag_add("highlight", f"{l+1}.{start_index}", f"{l+1}.{end_index}")
        self.info.tag_config("highlight", foreground=color)

    def open_info(self):
        message = "Федеральное государственное бюджетное учреждение науки Институт программных " \
                  "систем им. А.К. Айламазяна Российской академии наук (ИПС им. А.К. Айламазяна РАН)\n\n" \
                  "Лаборатория методов обработки и анализа изображений (ЛМОАИ)\n\n" \
                  "2023 год"
        showinfo(title="Разработчик", message=message)

    def __init__(self):
        super().__init__()
        self.title("ALP")
        self.geometry(f"{self.main_w}x200")
        self.update()
        self.protocol("WM_DELETE_WINDOW", self.finishApp)

        self.main_menu = Menu()
        self.select_menu = Menu(tearoff=0)
        self.select_menu.add_command(label="Выбрать папку", command=self.selectFolder)
        self.info_menu = Menu(tearoff=0)
        self.info_menu.add_command(label="Разработчик", command=self.open_info)
        self.main_menu.add_cascade(label="Открыть", menu=self.select_menu)
        self.main_menu.add_cascade(label="О программе", menu=self.info_menu)
        self.config(menu=self.main_menu)

        self.top_frame = tk.LabelFrame(self, text="Статистика", borderwidth=1, relief=SOLID)
        self.middle_frame = tk.LabelFrame(self, text="Выбор алгоритма обработки", borderwidth=1, relief=SOLID)
        self.bottom_frame = tk.LabelFrame(self, text="Предпросмотр результата", borderwidth=1, relief=SOLID)

        self.info_text = "Выберете папку с изображениями с помощью меню: Открыть -> Выбрать папку"
        self.info = scrolledtext.ScrolledText(self.top_frame, wrap=WORD, height=10, state=NORMAL)
        self.info.insert(INSERT, self.info_text)
        self.highlightWord(["Открыть", "Выбрать папку"], self.info_text, "dark green")
        self.info.config(state=DISABLED)

        self.selected_alg = StringVar(value=self.enable_alg[0])
        self.rgb_radio = ttk.Radiobutton(self.middle_frame, text=self.enable_alg[0], value=self.enable_alg[0],
                                         variable=self.selected_alg)
        self.lab_radio = ttk.Radiobutton(self.middle_frame, text=self.enable_alg[1], value=self.enable_alg[1],
                                         variable=self.selected_alg)

        self.btn_start_ac = ttk.Button(self.middle_frame, text="Выполнить обработку изображений", width=60,
                                       command=self.areaCalculation, state=DISABLED)

        self.confirm_save = IntVar(value=1)
        self.log_save = ttk.Checkbutton(self.bottom_frame, text="Сохранить лог файл", variable=self.confirm_save,
                                         onvalue=1, offvalue=0)

        self.result_preview = ttk.Treeview(self.bottom_frame, show="tree", height=400)
        self.myscrollbar = tk.Scrollbar(self.bottom_frame, orient="vertical", command=self.result_preview.yview)
        self.result_preview.configure(yscrollcommand=self.myscrollbar.set)
        self.result_preview.bind("<Double-Button-1>", self.viewImage)

        self.top_frame.pack(side=TOP, padx=5, pady=2, fill=BOTH)
        self.info.pack(padx=5, pady=5, fill=X)
        self.rgb_radio.pack(anchor=NW, padx=10)
        self.lab_radio.pack(anchor=NW, padx=10)
        self.btn_start_ac.pack(padx=5, pady=5, side=BOTTOM)
        self.log_save.pack(padx=5, anchor=NW, fill=X)
        self.myscrollbar.pack(side=RIGHT, fill=Y)
        self.result_preview.pack(padx=5, pady=5, expand=True, fill=BOTH)


if __name__ == "__main__":
    app = App()
    app.mainloop()