import tkinter as tk

# 创建主窗口
root = tk.Tk()
root.title("Grid Cell Span Example")

# 创建一个Frame
frame = tk.Frame(root)
frame.pack(fill=tk.BOTH, expand=True)

# 在frame中添加几个按钮作为示例
btn1 = tk.Button(frame, text="Button 0,0")
btn2 = tk.Button(frame, text="Button 0,1")
btn3 = tk.Button(frame, text="Button 1,0")
btn4 = tk.Button(frame, text="Button 1,1")
btn5 = tk.Button(frame, text="Button 2,0 to 2,1 (Merged)")

btn1.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
btn2.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
btn3.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
btn4.grid(row=1, column=1, sticky="nsew", padx=5, pady=5)
# 合并单元格的按钮，跨越了第2行和第3行
btn5.grid(row=2, column=0, columnspan=2, sticky="nsew", padx=5, pady=5)

# 配置行和列属性，确保窗口大小调整时各个格子按比例变化
for i in range(3):
    frame.grid_rowconfigure(i, weight=1)
for i in range(2):
    frame.grid_columnconfigure(i, weight=1)

# 启动主循环
root.mainloop()