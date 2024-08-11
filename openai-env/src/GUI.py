import customtkinter as ctk
from tkinter import filedialog
from PIL import Image, ImageTk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import LLM_use_pic_to_plan as GPT_plan
import LLM_adjust_oven as GPT_control
import ovenControll
import sys
import threading

# globle variables declaration
ax=None
canvas=None
real_food_characristic_list='3000','2','80','20','0.2'
model_name = 'OvenSim'
matlab_file = 'ovenSimConfig.m'
file_path=None
pic_response=""
current_time_temp_list=[]
preference_text=""
reference_param_dict = None
referenced_data = None
real_param_dict = None
time_past=0
time_to_finish=60 #initial value for time_to_finish is 60 minutes (will change quickly)
state_dict=None

# 定义上传图片功能
def upload_photo():
    global file_path
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif")])
    if file_path:
        img = Image.open(file_path)
        img = img.resize((160, 120), Image.LANCZOS)
        photo = ctk.CTkImage(light_image=img, dark_image=img, size=(200, 150))
        photo_label.configure(image=photo, text="")  # 清除默认文本
        photo_label.image = photo
        #状态文本框更改
        update_state_text_box("Photo uploaded.")
    # enable recognize button
    recognize_button.configure(state='normal')
        
def recognize():
    global reference_param_dict
    global pic_response
    #状态文本框更改
    state_text_box.delete("1.0", "end")
    state_text_box.insert("1.0", "Calling GPT to recognize...")
    # Call GPT to recognize the picture
    pic_response, reference_param_dict=GPT_plan.call(file_path)
    #状态文本框更改
    update_state_text_box("Recognition finished.")
    #显示食物种类
    food_type_label=ctk.CTkLabel(frame1, text=f'food type: {reference_param_dict["type of food"]}')
    food_type_label.grid(row=4,column=0, sticky="news", padx=5, pady=5)
       
def confirm_btn():
    global preference_text
    preference_text=user_preference_textbox.get("1.0", "end-1c")
    update_state_text_box("User preference saved.")    
    #加一句检查

# 更新温度曲线
def update_curve(data_points):
    global ax, canvas
    # 清除已有的曲线，保留其他设置
    for line in ax.lines:
        line.remove()
    
    # 将字符串数据转换为浮点数
    converted_points = [float(point) for point in data_points]
    
    # 生成时间列表，根据数据点的数量生成 [0, 1, 2, ...]
    times = list(range(len(converted_points)))
    
    # 更新曲线，画出所有数据点
    ax.plot(times, converted_points, color='#007acc', linewidth=2)
    
    # 重新绘制图形
    canvas.draw()
    root.update_idletasks()

# 动态更新时间
def update_time():
    time_label.configure(text=f"Time Proceed: {time_past} minutes")
    # time_left_label.configure(text=f"Time Left: {time_to_finish} minutes")
    root.update_idletasks()

# 更新文本框内容
def update_state_text_box(text):
    state_text_box.delete("1.0", "end")
    state_text_box.insert("1.0", text)
    
def start():

    
    state_text_box.delete("1.0", "end")
    state_text_box.insert("1.0", "Starting baking process...")
    
    # button enable & disable
    start_btn.configure(state='disabled')
    user_preference_btn.configure(state='disabled')
    upload_button.configure(state='disabled')
    recognize_button.configure(state="disabled")
    stop_btn.configure(state='normal')
    
    # 创建线程执行烤制过程
    baking_thread = threading.Thread(target=baking_process)
    baking_thread.start()
    
def print_temptimelist(temp_time_list):
    print(f"TIME TEMP LIST FOR CURVE: {temp_time_list}")
    
def baking_process():
    #variable declaration
    global referenced_data
    global real_param_dict
    global time_past
    global state_dict
    global current_time_temp_list
    global time_to_finish
    # combine real food characristics (whole chicken for example)
    real_param_dict,referenced_data=GPT_control.combine_real_food_params_and_LLM_generated_grill_process(pic_response,real_food_characristic_list)
    
    # start baking process
    #初始化模型
    eng=ovenControll.matlab_initialization(model_name,matlab_file)
    #拿到参考温度曲线
    referenced_data=GPT_control.get_reference_data(eng,model_name,pic_response)
    #开始真实烘烤（第一分钟）
    state_dict=GPT_control.real_grill_process_one_minute(eng,model_name,real_param_dict)
    # 更新时间
    time_past+=1
    update_time()
    #收集数据，更新曲线
    current_time_temp_list=GPT_control.collect_data(current_time_temp_list,state_dict,real_param_dict)
    update_curve(current_time_temp_list)
    #从第二分钟开始循环烤制过程
    while True:
        if not GPT_control.is_finished(current_time_temp_list,referenced_data,time_past):
            is_negligible, reason=GPT_control.call_LLM_is_negligible_error_and_give_reason(current_time_temp_list,referenced_data,reference_param_dict,real_param_dict,preference_text)
            if not is_negligible:
                #发生偏移，生成操作和后果并显示
                control_data_dict, consequences, time_to_finish=GPT_control.call_LLM_generate_controll_instruction(reason,current_time_temp_list,referenced_data,reference_param_dict,real_param_dict,preference_text)
                time_to_finish=time_to_finish.strip()
                #consequences有待改进，暂时先不输出了
                # if GPT_control.oven_setting_is_modified(state_dict,control_data_dict):
                #     update_state_text_box(consequences)
                state_dict=GPT_control.apply_control_data_to_state(control_data_dict,state_dict)
                print(f"State Changed. New State: {state_dict}")
                #继续烤制，记录数据，更新时间和曲线
                state_dict=GPT_control.real_grill_process_one_minute(eng,model_name,state_dict)
                time_past+=1
                update_time()
                print_temptimelist(current_time_temp_list)
                current_time_temp_list=GPT_control.collect_data(current_time_temp_list,state_dict,real_param_dict)
                print_temptimelist(current_time_temp_list)
                update_curve(current_time_temp_list)
            else:
                #没有偏移，继续烤制，记录数据，更新时间和曲线
                    state_dict=GPT_control.real_grill_process_one_minute(eng,model_name,state_dict)
                    time_past+=1
                    update_time()
                    current_time_temp_list=GPT_control.collect_data(current_time_temp_list,state_dict,real_param_dict)
                    print_temptimelist(current_time_temp_list)
                    update_curve(current_time_temp_list)
        else:
            #烤制过程结束，关闭引擎,跳出循环
            ovenControll.quit_matlab_engine(eng)
            update_state_text_box("The food is finish!")
            break

def stop():
    sys.exit(0)

def initial_curve():
    global ax
    global canvas
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
    root.geometry("520x845")

    # Create frames
    frame1 = ctk.CTkFrame(root)
    frame1.pack(fill="both", expand=True)

    frame2 = ctk.CTkFrame(root)
    frame2.pack(fill="both", expand=True)

    #----------frame1-----------
    # 上传照片按钮
    upload_button = ctk.CTkButton(frame1, text="Upload Photo", width=200, command=upload_photo)
    upload_button.grid(row=0, column=0, sticky="sew", padx=15, pady=20)
    # recognize button
    recognize_button=ctk.CTkButton(frame1, text="Recognize", command=recognize,state="disabled")
    recognize_button.grid(row=0,column=1, sticky="sew", padx=15, pady=20)
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
    user_preference_btn=ctk.CTkButton(frame1, text="Confirm", corner_radius=10, width=50, height=30, command=confirm_btn)
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
    # time_left_label = ctk.CTkLabel(frame2, text="Time Left (Estimated):")
    # time_left_label.grid(row=4, column=0, columnspan=2, sticky="nsw", padx=30, pady=5)
    # 已烤时间
    time_label = ctk.CTkLabel(frame2, text="Time Passed:")
    time_label.grid(row=3, column=0, sticky="nsw", columnspan=2, padx=30, pady=5)
    #文本框
    state_text_box=ctk.CTkTextbox(frame2,height=50)
    state_text_box.grid(row=5,column=0,columnspan=2,sticky="news",padx=15,pady=5)
    # start按钮
    start_btn=ctk.CTkButton(frame2, text="START", width=30,height=50, corner_radius=20, font=("Arial",35),command=start)
    start_btn.grid(row=6, column=1, sticky="new", padx=5, pady=15)
    # stop按钮
    stop_btn=ctk.CTkButton(frame2, text="STOP",corner_radius=40, font=("Arial",35),fg_color="dark red", command=stop, state="disabled")
    stop_btn.grid(row=6, column=0, sticky="w", padx=5, pady=15)
    #配置frame1的行、列
    frame2.grid_rowconfigure(2, minsize=340)
    # frame1.grid_columnconfigure(1, minsize=150)

    # 运行主循环
    root.mainloop()