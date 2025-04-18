import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import sys
import os
import io
import threading
from epub_to_txt import convert_epub_to_txt

class RedirectedOutput(io.TextIOBase):
    """重定向标准输出到Tkinter组件"""
    def __init__(self, text_widget):
        self.text_widget = text_widget
    def write(self, s):
        # 规范化路径显示（处理日志中的路径）
        normalized_s = self.normalize_paths_in_string(s)
        self.text_widget.insert(tk.END, normalized_s)
        self.text_widget.see(tk.END)
        self.text_widget.update_idletasks()

    @staticmethod
    def normalize_paths_in_string(text):
        """使用系统路径风格规范化字符串中的路径"""
        if os.name == 'nt':
            return text.replace('/', '\\')
        return text.replace('\\', '/')

def resource_path(relative_path):
    """处理PyInstaller的临时资源路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class EPUBConverterGUI:
    def __init__(self, root):
        self.root = root
        # 设置窗口图标
        try:
            icon_path = resource_path('book.ico')
            root.iconbitmap(icon_path)
        except Exception as e:
            print(f"Error loading icon: {e}")  # 调试输出
        root.title("EPUB to TXT Converter")
        root.geometry("800x600")

        self.epub_path = tk.StringVar()
        self.output_dir = tk.StringVar()
        self.merge_var = tk.BooleanVar()

        self.create_widgets()
        sys.stdout = RedirectedOutput(self.output_area)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # 第一行：EPUB文件输入
        input_frame = ttk.Frame(main_frame)
        input_frame.grid(row=0, column=0, sticky="ew", pady=5)

        ttk.Label(input_frame, text="EPUB File:").pack(side=tk.LEFT, padx=5)
        entry = ttk.Entry(input_frame, textvariable=self.epub_path, width=50)
        entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        # 自动规范化输入路径
        entry.bind("<FocusOut>", lambda e: self.epub_path.set(self.normalize_path(self.epub_path.get())))

        ttk.Button(input_frame, text="Browse", command=self.browse_epub).pack(side=tk.LEFT, padx=5)

        # 第二行：输出目录
        output_frame = ttk.Frame(main_frame)
        output_frame.grid(row=1, column=0, sticky="ew", pady=5)

        ttk.Label(output_frame, text="Output Dir:").pack(side=tk.LEFT, padx=5)
        output_entry = ttk.Entry(output_frame, textvariable=self.output_dir, width=50)
        output_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        # 自动规范化输出路径
        output_entry.bind("<FocusOut>", lambda e: self.output_dir.set(self.normalize_path(self.output_dir.get())))

        ttk.Button(output_frame, text="Choose", command=self.choose_output_dir).pack(side=tk.LEFT, padx=5)

        # 第三行：参数和按钮
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=2, column=0, sticky="ew", pady=5)

        ttk.Checkbutton(action_frame, text="Merge Files", variable=self.merge_var).pack(side=tk.LEFT, padx=5)
        ttk.Button(action_frame, text="Start Conversion", command=self.start_conversion).pack(side=tk.LEFT, padx=5)

        # 日志区域
        self.output_area = scrolledtext.ScrolledText(main_frame, wrap=tk.WORD)
        self.output_area.grid(row=3, column=0, sticky="nsew", pady=10)

        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)

    @staticmethod
    def normalize_path(path):
        """规范化路径到当前系统格式"""
        if not path:
            return path
        return os.path.normpath(path.strip())

    def browse_epub(self):
        filename = filedialog.askopenfilename(filetypes=[("EPUB files", "*.epub")])
        if filename:
            # 规范化路径并更新输入路径
            normalized_path = self.normalize_path(filename)
            self.epub_path.set(normalized_path)

            # 强制生成新的默认输出路径
            epub_dir = os.path.dirname(normalized_path)
            base_name = os.path.splitext(os.path.basename(normalized_path))[0]
            default_output = os.path.normpath(os.path.join(epub_dir, base_name))
            self.output_dir.set(default_output)  # 直接覆盖原有输出路径

    def choose_output_dir(self):
        dirname = filedialog.askdirectory()
        if dirname:
            self.output_dir.set(self.normalize_path(dirname))

    def start_conversion(self):
        # 最终规范化路径参数
        epub_file = self.normalize_path(self.epub_path.get())
        output_dir = self.normalize_path(self.output_dir.get()) or None
        merge = self.merge_var.get()

        if not epub_file:
            print("Error: Please select an EPUB file.")
            return

        threading.Thread(
            target=convert_epub_to_txt,
            args=(epub_file, output_dir, merge),
            daemon=True
        ).start()

def main_gui():
    root = tk.Tk()
    app = EPUBConverterGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main_gui()
