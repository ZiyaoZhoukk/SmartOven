import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import time
import threading
import LLM_use_pic_to_plan as GPT_plan
import LLM_adjust_oven as GPT_control

# 定义上传图片功能
def upload_photo():
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
    if file_path:
        img = Image.open(file_path)
        img = img.resize((200, 150), Image.LANCZOS)
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 150))
        photo_label.configure(image=photo, text="")  # 清除默认文本
        photo_label.image = photo
        
        # Call GPT to recognize the picture
        json_initial_param=GPT_plan.call(file_path)
        
        #显示食物种类
        food_type_label=ctk.CTkLabel(frame1, text=f'food type: {json_initial_param["type of food"]}')
        food_type_label.grid(row=4,column=0, sticky="news", padx=5, pady=5)
        
def btn_confirm():
    # preference_text=user_preference_textbox.get("1.0", "end-1c")    
    return

# 更新温度曲线
def update_curve():
    # 示例时间和温度数据
    times = list(range(0, 30))
    temperatures = [200 + i * 2 for i in times]
    # 创建图形和坐标轴
    fig, ax = plt.subplots(figsize=(4, 3))
    # 绘制数据，设置线条颜色
    ax.plot(times, temperatures, color='#1f77b4')  # 线条颜色，可以根据需要调整
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
    
    #在界面上画图
    canvas = FigureCanvasTkAgg(fig, master=frame2)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0, rowspan=2, sticky="nsew", padx=15, pady=5)

# 动态更新时间
def update_time():
    start_time = time.time()
    while True:
        elapsed_time = int(time.time() - start_time)
        time_label.configure(text=f"Time Proceed: {elapsed_time//60} minutes")
        time_left = max(0, 1800 - elapsed_time)  # 假设总时间为1800秒（30分钟）
        time_left_label.configure(text=f"Time Left: {time_left//60} minutes")
        time.sleep(1)

def start():
    return

def stop():
    sys.exit(0)

def initial_curve():
    # 示例时间和温度数据
    times = list(range(0, 100))
    temperatures = [200 + i * 2 for i in times]
    # 创建图形和坐标轴
    fig, ax = plt.subplots(figsize=(6, 4))  # 长方形，横纵比3:2
    # 设置坐标轴范围和标签
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.set_xlabel('Time (minutes)', labelpad=0.5)  # 横坐标标签
    ax.set_ylabel('Temperature (°C)', labelpad=-1)  # 纵坐标标签
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
    # plt.subplots_adjust(left=0.2, right=0.4, top=0.4, bottom=0.1)    
    
    # 设置缩放比例
    scaling_factor = 2 / 5
    # 调整图形大小
    fig.set_size_inches(fig.get_size_inches() * scaling_factor)    
    # 调整字体大小和线条宽度
    for item in ([ax.title, ax.xaxis.label, ax.yaxis.label] +
                ax.get_xticklabels() + ax.get_yticklabels()):
        item.set_fontsize(item.get_fontsize() * scaling_factor)

    # 不显示曲线
    for line in ax.get_lines():
        line.remove()
    
    #在界面上画图
    canvas = FigureCanvasTkAgg(fig, master=frame2)
    canvas.draw()
    canvas.get_tk_widget().grid(row=1, column=0, rowspan=2, columnspan=2, sticky="new", padx=15, pady=5)

    

if __name__ == "__main__":
    # 设置界面外观
    ctk.set_appearance_mode("light")  
    ctk.set_default_color_theme("dark-blue")  

    # 创建主窗口
    root = ctk.CTk()
    root.title("Smart Oven Control")
    root.geometry("520x750")

    # Create frames
    frame1 = ctk.CTkFrame(root)
    frame1.pack(fill="both", expand=True)

    frame2 = ctk.CTkFrame(root)
    frame2.pack(fill="both", expand=True)

    #----------frame1-----------
    # 上传照片按钮
    upload_button = ctk.CTkButton(frame1, text="Upload Photo", width=200, command=upload_photo)
    upload_button.grid(row=0, column=0, sticky="sew", padx=15, pady=20)
    # 显示照片
    photo_label = ctk.CTkLabel(frame1, text="")  # 设置默认文本
    photo_label.grid(row=1, column=0, rowspan=3, sticky="new", padx=5, pady=5)
    # 用户偏好label
    user_preference_label = ctk.CTkLabel(frame1, text="User Preference:")
    user_preference_label.grid(row=1, column=1,columnspan=2, sticky="wn", padx=5, pady=5)
    #用户偏好text box
    user_preference_textbox=ctk.CTkTextbox(frame1, width=150, height=100, corner_radius=10, fg_color="lightgray")
    user_preference_textbox.grid(row=2, column=1, rowspan=2, sticky="ne", padx=5, pady=5)
    #用户偏好button
    user_preference_btn=ctk.CTkButton(frame1, text="Confirm", corner_radius=10, width=50, height=30, command=btn_confirm)
    user_preference_btn.grid(row=3, column=2, sticky="sw", padx=5, pady=5)

    #配置frame1的行、列
    frame1.grid_columnconfigure(0, minsize=250)
    frame1.grid_columnconfigure(1, minsize=150)

    #----------frame2-----------
    # 曲线label
    curve_name_label=ctk.CTkLabel(frame2, text="Real-Time Food Temperature")
    curve_name_label.grid(row=0, column=0, columnspan=2, sticky="snwe", padx=5, pady=5)
    # 更新温度曲线
    initial_curve()
    # 剩余时间
    time_left_label = ctk.CTkLabel(frame2, text="Time Left (Estimated):")
    time_left_label.grid(row=4, column=0, columnspan=2, sticky="nsw", padx=30, pady=5)
    # 已烤时间
    time_label = ctk.CTkLabel(frame2, text="Time Passed:")
    time_label.grid(row=3, column=0, sticky="nsw", columnspan=2, padx=30, pady=5)
    # 启动时间更新线程
    # threading.Thread(target=update_time, daemon=True).start()
    # start按钮
    start_btn=ctk.CTkButton(frame2, text="START", width=30,height=50, corner_radius=20, font=("Arial",35),command=start)
    start_btn.grid(row=5, column=1, sticky="new", padx=5, pady=15)
    # stop按钮
    stop_btn=ctk.CTkButton(frame2, text="STOP",corner_radius=40, font=("Arial",35),fg_color="dark red", command=stop, state="disabled")
    stop_btn.grid(row=5, column=0, sticky="w", padx=5, pady=15)
    #配置frame1的行、列
    frame2.grid_rowconfigure(2, minsize=340)
    # frame1.grid_columnconfigure(1, minsize=150)

    # 运行主循环
    root.mainloop()