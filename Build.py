import tkinter as tk
from tkinter import messagebox
import time
import threading
import random
import math
import pygame

# ---------------------------- SETTINGS ------------------------------- #
SESSIONS_BEFORE_LONG_BREAK = 4

# ---------------------------- COLORS ------------------------------- #
BUTTON_BG = "#268bd2"
BUTTON_FG = "#ffffff"
LABEL_FG = "#ffffff"

# ---------------------------- GLOBALS ------------------------------- #
reps = 0
timer_running = False
timer_thread = None
custom_times = {"work": 25*60, "short": 5*60, "long": 15*60}  # default in seconds
blobs = []

# ---------------------------- INITIALIZE PYGAME SOUND ------------------------------- #
pygame.mixer.init()
alarm_sound = pygame.mixer.Sound("alarm_sound.mp3")

# ---------------------------- TIMER MECHANISM ------------------------------- #
def start_timer():
    global reps, timer_running, timer_thread
    if not timer_running:
        timer_running = True
        reps += 1
        if reps % (SESSIONS_BEFORE_LONG_BREAK*2) == 0:
            seconds = custom_times["long"]
            session_label.config(text="Long Break")
        elif reps % 2 == 0:
            seconds = custom_times["short"]
            session_label.config(text="Short Break")
        else:
            seconds = custom_times["work"]
            session_label.config(text="Work Session")

        timer_thread = threading.Thread(target=count_down, args=(seconds,))
        timer_thread.start()

def reset_timer():
    global reps, timer_running
    timer_running = False
    reps = 0
    timer_label.config(text="00:00")
    session_label.config(text="Timer")
    session_count_label.config(text="Pomodoros: 0")

def count_down(count):
    global timer_running
    while count > 0 and timer_running:
        mins = count // 60
        secs = count % 60
        timer_label.config(text=f"{mins:02d}:{secs:02d}")
        time.sleep(1)
        count -= 1

    if timer_running:
        timer_running = False
        # Play alarm sound in a loop
        alarm_sound.play(loops=-1)
        update_session_count()
        show_notification(session_label.cget("text"))
        start_timer()

def update_session_count():
    completed_sessions = reps // 2
    session_count_label.config(text=f"Pomodoros: {completed_sessions}")

# ---------------------------- SETTINGS WINDOW ------------------------------- #
def open_settings():
    def save_settings():
        try:
            custom_times["work"] = int(work_hour.get())*3600 + int(work_min.get())*60 + int(work_sec.get())
            custom_times["short"] = int(short_hour.get())*3600 + int(short_min.get())*60 + int(short_sec.get())
            custom_times["long"] = int(long_hour.get())*3600 + int(long_min.get())*60 + int(long_sec.get())
            settings_win.destroy()
        except ValueError:
            messagebox.showerror("Error", "Please select valid numbers")

    settings_win = tk.Toplevel(root)
    settings_win.title("Settings")
    settings_win.geometry("350x250")
    settings_win.resizable(False, False)

    def create_time_picker(label_text, row):
        tk.Label(settings_win, text=label_text).grid(row=row, column=0, padx=5, pady=5)
        hour = tk.Spinbox(settings_win, from_=0, to=23, width=3)
        hour.grid(row=row, column=1)
        tk.Label(settings_win, text="h").grid(row=row, column=2)
        minute = tk.Spinbox(settings_win, from_=0, to=59, width=3)
        minute.grid(row=row, column=3)
        tk.Label(settings_win, text="m").grid(row=row, column=4)
        second = tk.Spinbox(settings_win, from_=0, to=59, width=3)
        second.grid(row=row, column=5)
        tk.Label(settings_win, text="s").grid(row=row, column=6)
        return hour, minute, second

    work_hour, work_min, work_sec = create_time_picker("Work:", 0)
    short_hour, short_min, short_sec = create_time_picker("Short Break:", 1)
    long_hour, long_min, long_sec = create_time_picker("Long Break:", 2)

    apply_btn = tk.Button(settings_win, text="Apply", command=save_settings, bg=BUTTON_BG, fg=BUTTON_FG)
    apply_btn.grid(row=3, column=0, columnspan=7, pady=15)

# ---------------------------- POPUP NOTIFICATION ------------------------------- #
def show_notification(text):
    popup = tk.Toplevel(root)
    popup.title("Pomodoro Finished")
    popup.geometry("200x80+500+300")
    popup.resizable(False, False)

    tk.Label(popup, text=f"{text} Finished!", font=("Helvetica", 12)).pack(pady=10)
    tk.Button(popup, text="OK", command=lambda: stop_alarm(popup)).pack(pady=5)

def stop_alarm(popup):
    alarm_sound.stop()
    popup.destroy()

# ---------------------------- BLOBS BACKGROUND ------------------------------- #
class Blob:
    def __init__(self, canvas, x, y, size, color, dx, dy):
        self.canvas = canvas
        self.base_color = color
        self.parts = []
        self.phase = random.uniform(0, 3.14)
        for i, alpha in enumerate([0.4, 0.25, 0.1]):
            c = self._adjust_color_alpha(color, alpha)
            self.parts.append(canvas.create_oval(x+i*5, y+i*5, x+size+i*5, y+size+i*5, fill=c, outline=""))
        self.dx = dx
        self.dy = dy
        self.size = size

    def _adjust_color_alpha(self, hex_color, alpha):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        r = int(r * alpha)
        g = int(g * alpha)
        b = int(b * alpha)
        return f'#{r:02x}{g:02x}{b:02x}'

    def move(self):
        # Move blob
        for part in self.parts:
            coords = self.canvas.coords(part)
            if coords[2] >= self.canvas.winfo_width() or coords[0] <= 0:
                self.dx *= -1
            if coords[3] >= self.canvas.winfo_height() or coords[1] <= 0:
                self.dy *= -1
            self.canvas.move(part, self.dx, self.dy)

        # Smooth glow & color shift
        self.phase += 0.02
        r_base = int(self.base_color[1:3],16)
        g_base = int(self.base_color[3:5],16)
        b_base = int(self.base_color[5:7],16)

        for i, part in enumerate(self.parts):
            alpha = [0.4, 0.25, 0.1][i]
            r = int(max(0, min(255, r_base*alpha + 30*math.sin(self.phase + i))))
            g = int(max(0, min(255, g_base*alpha + 30*math.sin(self.phase + i + 1))))
            b = int(max(0, min(255, b_base*alpha + 30*math.sin(self.phase + i + 2))))
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.itemconfig(part, fill=color)

def create_blobs(canvas, count=12):
    colors = ["#ff6b6b","#feca57","#48dbfb","#1dd1a1","#5f27cd","#ff9ff3"]
    for _ in range(count):
        x = random.randint(0, canvas.winfo_width()-150)
        y = random.randint(0, canvas.winfo_height()-150)
        size = random.randint(50,150)
        dx = random.choice([-1,1])*random.uniform(0.2,0.8)
        dy = random.choice([-1,1])*random.uniform(0.2,0.8)
        color = random.choice(colors)
        blobs.append(Blob(canvas, x, y, size, color, dx, dy))

def animate_blobs():
    for blob in blobs:
        blob.move()
    root.after(50, animate_blobs)

# ---------------------------- UI SETUP ------------------------------- #
root = tk.Tk()
root.title("Pomodoro Timer")
root.geometry("500x350")
root.resizable(False, False)

# Canvas for black background
canvas = tk.Canvas(root, width=500, height=350, highlightthickness=0, bg="#000000")
canvas.place(x=0, y=0)
root.update()

create_blobs(canvas, count=12)
animate_blobs()

# Labels and buttons on top
session_label = tk.Label(root, text="Timer", font=("Helvetica",20), fg=LABEL_FG, bg="#000000")
session_label.place(relx=0.5, rely=0.1, anchor="center")

timer_label = tk.Label(root, text="00:00", font=("Helvetica",50), fg=LABEL_FG, bg="#000000")
timer_label.place(relx=0.5, rely=0.35, anchor="center")

session_count_label = tk.Label(root, text="Pomodoros: 0", font=("Helvetica",14), fg=LABEL_FG, bg="#000000")
session_count_label.place(relx=0.5, rely=0.55, anchor="center")

# Buttons frame
button_frame = tk.Frame(root, bg="#000000")
button_frame.place(relx=0.5, rely=0.75, anchor="center")

start_button = tk.Button(button_frame, text="Start", command=start_timer, bg=BUTTON_BG, fg=BUTTON_FG)
start_button.grid(row=0, column=0, padx=5)
reset_button = tk.Button(button_frame, text="Reset", command=reset_timer, bg=BUTTON_BG, fg=BUTTON_FG)
reset_button.grid(row=0, column=1, padx=5)
settings_button = tk.Button(button_frame, text="Settings", command=open_settings, bg=BUTTON_BG, fg=BUTTON_FG)
settings_button.grid(row=0, column=2, padx=5)

root.mainloop()