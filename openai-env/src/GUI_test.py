import customtkinter as ctk

# 创建主窗口
root = ctk.CTk()
root.title("Grid Cell Size Example")

# 创建一个CTkFrame
frame = ctk.CTkFrame(root)
frame.pack(fill=ctk.BOTH, expand=True)

# 在frame中添加几个按钮和一张图片作为示例
btn1 = ctk.CTkButton(frame, text="Button 0,0")
btn2 = ctk.CTkButton(frame, text="Button 0,1")
btn3 = ctk.CTkButton(frame, text="Button 1,0")
btn4 = ctk.CTkButton(frame, text="Button 1,1")

btn1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
btn2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
btn3.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
btn4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)

# 配置行属性，使第一行的最小高度为200，第二行的最小高度为100
frame.grid_rowconfigure(0, minsize=200, weight=1)
frame.grid_rowconfigure(1, minsize=100, weight=1)

# 配置列属性，使第一列的最小宽度为100，第二列的最小宽度为300
frame.grid_columnconfigure(0, minsize=100, weight=1)
frame.grid_columnconfigure(1, minsize=300, weight=2)  # 第二列的weight更大，意味着它会占更多的空间

# 启动主循环
root.mainloop()