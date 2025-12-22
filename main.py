import tkinter as tk
from tkinter import ttk, messagebox
import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Polygon:
    def __init__(self, points):
        self.points = points

def is_point_left_of_edge(p, a, b):
    return (b.x - a.x) * (p.y - a.y) - (b.y - a.y) * (p.x - a.x) >= 0

def line_intersection(p1, p2, p3, p4):
    x1, y1 = p1.x, p1.y
    x2, y2 = p2.x, p2.y
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y

    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 1e-10:
        return Point((x1 + x2) / 2, (y1 + y2) / 2)

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    x = x1 + t * (x2 - x1)
    y = y1 + t * (y2 - y1)
    return Point(x, y)

def ensure_counter_clockwise(poly):
    if len(poly.points) < 3:
        return
    area = 0.0
    n = len(poly.points)
    for i in range(n):
        j = (i + 1) % n
        area += poly.points[i].x * poly.points[j].y
        area -= poly.points[j].x * poly.points[i].y
    if area < 0:
        poly.points.reverse()

def sutherland_hodgman(subject, clipper):
    if len(subject.points) < 3 or len(clipper.points) < 3:
        return Polygon([])

    # Приводим отсекатель к правильной ориентации
    clip_copy = Polygon(clipper.points[:])  # копия
    ensure_counter_clockwise(clip_copy)

    output = subject.points[:]
    n = len(clip_copy.points)

    for i in range(n):
        if not output:
            break
        input_list = output[:]
        output = []
        a = clip_copy.points[i]
        b = clip_copy.points[(i + 1) % n]
        if not input_list:
            continue
        s = input_list[-1]
        for e in input_list:
            if is_point_left_of_edge(e, a, b):
                if not is_point_left_of_edge(s, a, b):
                    inter = line_intersection(s, e, a, b)
                    output.append(inter)
                output.append(e)
            elif is_point_left_of_edge(s, a, b):
                inter = line_intersection(s, e, a, b)
                output.append(inter)
            s = e

    return Polygon(output)

def scanline_fill(poly, width=800, height=600, fill_color=(0, 180, 0)):
    if len(poly.points) < 3:
        return [[(255, 255, 255) for _ in range(width)] for _ in range(height)]

    pixels = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]
    edges = []
    for i in range(len(poly.points)):
        a = poly.points[i]
        b = poly.points[(i + 1) % len(poly.points)]
        x1, y1, x2, y2 = a.x, a.y, b.x, b.y
        if y1 == y2:
            continue
        if y1 > y2:
            x1, x2, y1, y2 = x2, x1, y2, y1
        edges.append((x1, y1, x2, y2))

    ymin = max(0, int(min(p.y for p in poly.points)))
    ymax = min(height - 1, int(max(p.y for p in poly.points)))

    for y in range(ymin, ymax + 1):
        intersections = []
        for x1, y1, x2, y2 in edges:
            if y1 <= y < y2:
                x = x1 + (x2 - x1) * (y - y1) / (y2 - y1)
                intersections.append(x)
        intersections.sort()
        for i in range(0, len(intersections) - 1, 2):
            x_start = max(0, int(math.floor(intersections[i])))
            x_end = min(width - 1, int(math.ceil(intersections[i + 1])))
            for x in range(x_start, x_end + 1):
                pixels[y][x] = fill_color
    return pixels

class Lab13App:
    def __init__(self, root):
        self.root = root
        self.root.title("Лабораторная работа №13: Отсечение и закрашивание многоугольников")
        self.root.geometry("1200x720")

        self.subject = Polygon([])
        self.clipper = Polygon([])
        self.result = None
        self.fill_color = (0, 180, 0)
        self.mode = "subject"

        self.build_ui()

    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        left = ttk.Frame(main, width=240)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Режим
        mode_frame = ttk.LabelFrame(left, text="Режим ввода", padding=10)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        self.mode_var = tk.StringVar(value="subject")
        ttk.Radiobutton(mode_frame, text="Исходный многоугольник", value="subject",
                        variable=self.mode_var, command=self.switch_mode).pack(anchor=tk.W)
        ttk.Radiobutton(mode_frame, text="Отсекатель (выпуклый)", value="clipper",
                        variable=self.mode_var, command=self.switch_mode).pack(anchor=tk.W)

        btn_frame = ttk.LabelFrame(left, text="Действия", padding=10)
        btn_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(btn_frame, text="✅ Выполнить отсечение", command=self.do_clip).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🎨 Залить результат", command=self.do_fill).pack(fill=tk.X, pady=2)
        ttk.Button(btn_frame, text="🗑️ Очистить всё", command=self.reset).pack(fill=tk.X, pady=2)

        legend = ttk.LabelFrame(left, text="Цвета", padding=10)
        legend.pack(fill=tk.BOTH, expand=True)
        info = (
            "• Фиолетовый — исходный многоугольник\n"
            "• Чёрный — отсекающее окно\n"
            "• Зелёный — результат отсечения\n\n"
            "Кликните на холст, чтобы добавить вершину."
        )
        ttk.Label(legend, text=info, justify=tk.LEFT).pack(anchor=tk.W)

        self.canvas = tk.Canvas(right, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)

        self.redraw()

    def switch_mode(self):
        self.mode = self.mode_var.get()

    def on_click(self, event):
        pt = Point(event.x, event.y)
        if self.mode == "subject":
            self.subject.points.append(pt)
        else:
            self.clipper.points.append(pt)
        self.result = None
        self.redraw()

    def do_clip(self):
        if len(self.subject.points) < 3:
            messagebox.showwarning("Ошибка", "Исходный многоугольник: минимум 3 вершины!")
            return
        if len(self.clipper.points) < 3:
            messagebox.showwarning("Ошибка", "Отсекатель: минимум 3 вершины!")
            return

        try:
            self.result = sutherland_hodgman(self.subject, self.clipper)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось выполнить отсечение:\n{e}")
            return

        self.redraw()

    def do_fill(self):
        if not self.result or len(self.result.points) < 3:
            messagebox.showwarning("Ошибка", "Нет результата для заливки!")
            return
        pixels = scanline_fill(self.result, 800, 600, self.fill_color)
        self.canvas.delete("fill")
        for y in range(600):
            for x in range(800):
                if pixels[y][x] == self.fill_color:
                    self.canvas.create_rectangle(x, y, x + 1, y + 1,
                                                 fill=self.rgb_to_hex(self.fill_color),
                                                 outline="", tags="fill")

    def reset(self):
        self.subject = Polygon([])
        self.clipper = Polygon([])
        self.result = None
        self.redraw()

    def redraw(self):
        self.canvas.delete("all")

        if self.clipper.points:
            self.draw_poly(self.clipper, "black")
        if self.subject.points:
            self.draw_poly(self.subject, "purple")
        if self.result and self.result.points:
            self.draw_poly(self.result, "green")

    def draw_poly(self, poly, color):
        pts = poly.points
        n = len(pts)
        if n < 2:
            return
        for i in range(n):
            x1, y1 = pts[i].x, pts[i].y
            x2, y2 = pts[(i + 1) % n].x, pts[(i + 1) % n].y
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)
        for p in pts:
            self.canvas.create_oval(p.x - 4, p.y - 4, p.x + 4, p.y + 4, fill=color)

    @staticmethod
    def rgb_to_hex(rgb):
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

if __name__ == "__main__":
    root = tk.Tk()
    app = Lab13App(root)
    root.mainloop()