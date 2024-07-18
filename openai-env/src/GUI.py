import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import threading

# 定义上传图片功能
def upload_photo():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
    if file_path:
        img = Image.open(file_path)
        img = img.resize((200, 150), Image.LANCZOS)
        photo = ImageTk.PhotoImage(img)
        photo_label.configure(image=photo, text="")  # 清除默认文本
        photo_label.image = photo

# 更新温度曲线
def update_curve():
    # 示例时间和温度数据
    times = list(range(0, 30))
    temperatures = [200 + i * 2 for i in times]

    # 创建图形和坐标轴
    fig, ax = plt.subplots(figsize=(4, 3))

    # 绘制数据，设置线条颜色
    ax.plot(times, temperatures, color='#1f77b4')  # 线条颜色，可以根据需要调整

    # 设置网格
    #ax.grid()  # 网格颜色，可以根据需要调整

    # 去除标题
    ax.set_title('')

    # 设置坐标轴背景颜色
    ax.set_facecolor('#f7f7f7')  # 背景颜色，可以根据需要调整

    # 设置坐标轴刻度颜色和标签颜色
    ax.tick_params(axis='both', colors='#4a4a4a', direction='in')  # 刻度颜色和方向
    ax.tick_params(axis='x', pad=2)  # 调整x轴刻度标签的内边距
    ax.tick_params(axis='y', pad=2)  # 调整y轴刻度标签的内边距

    # 设置坐标轴边框颜色
    for spine in ax.spines.values():
        spine.set_edgecolor('#4a4a4a')  # 坐标轴边框颜色

    # 调整内边距去除留白
    plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1)
    
    # 设置缩放比例
    scaling_factor = 2 / 5

    # 调整图形大小
    fig.set_size_inches(fig.get_size_inches() * scaling_factor)
    
    # 调整字体大小和线条宽度
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(item.get_fontsize() * scaling_factor)

    for line in ax.get_lines():
        line.set_linewidth(line.get_linewidth() * scaling_factor)
    
    canvas = FigureCanvasTkAgg(fig, master=frame2)
    canvas.draw()
    canvas.get_tk_widget().pack()

# 动态更新时间
def update_time():
    start_time = time.time()
    while True:
        elapsed_time = int(time.time() - start_time)
        time_label.configure(text=f"Time: {elapsed_time} seconds")
        time_left = max(0, 1800 - elapsed_time)  # 假设总时间为1800秒（30分钟）
        time_left_label.configure(text=f"Time Left: {time_left//60} minutes {time_left%60} seconds")
        time.sleep(1)

# 设置界面外观
ctk.set_appearance_mode("light")  
ctk.set_default_color_theme("green")  

# 创建主窗口
root = ctk.CTk()
root.title("Smart Oven Control")
root.geometry("550x650")

# # 设置主窗口的行列权重
# root.grid_rowconfigure(1, weight=1)
# root.grid_columnconfigure(1, weight=1)

# Create frames
frame1 = ctk.CTkFrame(root)
frame1.pack(fill="both", expand=True)

frame2 = ctk.CTkFrame(root)
frame2.pack(fill="both", expand=True)

# 上传照片按钮
upload_button = ctk.CTkButton(frame1, text="Upload Photo", command=upload_photo)
upload_button.pack()

# 显示照片
photo_label = ctk.CTkLabel(frame1, text="No Image")  # 设置默认文本
photo_label.pack()

# 用户偏好
user_preference_label = ctk.CTkLabel(frame1, text="User Preference: Crispy skin for chicken")
user_preference_label.pack()

# 更新温度曲线
update_curve()

# 剩余时间
time_left_label = ctk.CTkLabel(frame2, text="Time Left: 30 minutes")
time_left_label.pack()

# 已烤时间
time_label = ctk.CTkLabel(frame2, text="Time: 0 seconds")
time_label.pack()

# 启动时间更新线程
threading.Thread(target=update_time, daemon=True).start()

# 运行主循环
root.mainloop()