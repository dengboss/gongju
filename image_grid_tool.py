import tkinter as tk
from tkinter import ttk, filedialog, messagebox, colorchooser
from PIL import Image, ImageTk
import os
from typing import List, Tuple, Optional

class ImageGridTool:
    def __init__(self, root):
        self.root = root
        self.root.title("图片拼接工具")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f0f0')
        
        # 初始化变量
        self.images: List[Image.Image] = []
        self.image_paths: List[str] = []
        self.grid_layout = tk.StringVar(value="9")
        self.canvas_width = tk.IntVar(value=600)
        self.canvas_height = tk.IntVar(value=600)
        self.keep_aspect_ratio = tk.BooleanVar(value=False)  # 锁定宽高比
        self.locked_aspect_ratio = 1.0  # 锁定的宽高比
        self.image_margin = tk.IntVar(value=5)  # 图片边距
        self.preset_var = tk.StringVar(value="自定义")  # 预设尺寸选择
        self.bg_color = "#FFFFFF"
        self.preview_image = None
        
        self.setup_ui()
        self.update_preview()
    
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 配置主框架的列权重，左侧固定宽度，右侧自适应
        main_frame.columnconfigure(0, weight=0, minsize=320)  # 左侧固定宽度
        main_frame.columnconfigure(1, weight=1)  # 右侧自适应
        main_frame.rowconfigure(0, weight=1)
        
        # 左侧控制面板 - 固定宽度
        left_frame = ttk.Frame(main_frame, width=320)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left_frame.grid_propagate(False)  # 防止框架收缩
        
        # 右侧预览面板 - 自适应
        right_frame = ttk.Frame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        
        self.setup_control_panel(left_frame)
        self.setup_preview_panel(right_frame)
    
    def setup_control_panel(self, parent):
        # 图片导入区域
        import_frame = ttk.LabelFrame(parent, text="图片导入", padding=10)
        import_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(import_frame, text="选择图片", command=self.select_images).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(import_frame, text="清空图片", command=self.clear_images).pack(fill=tk.X)
        
        # 图片列表
        self.image_listbox = tk.Listbox(import_frame, height=4)
        self.image_listbox.pack(fill=tk.X, pady=(10, 0))
        
        # 布局设置区域
        layout_frame = ttk.LabelFrame(parent, text="布局设置", padding=10)
        layout_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(layout_frame, text="网格布局:").pack(anchor=tk.W, pady=(0, 5))
        
        # 横向排列的单选按钮
        layout_radio_frame = ttk.Frame(layout_frame)
        layout_radio_frame.pack(fill=tk.X)
        
        layout_options = [("2x2 (4格)", "4"), ("2x3 (6格)", "6"), ("3x3 (9格)", "9")]
        for i, (text, value) in enumerate(layout_options):
            ttk.Radiobutton(layout_radio_frame, text=text, variable=self.grid_layout, 
                          value=value, command=self.update_preview).pack(side=tk.LEFT, padx=(0, 15))
        
        # 尺寸设置区域
        size_frame = ttk.LabelFrame(parent, text="尺寸设置", padding=10)
        size_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 常用尺寸下拉选择
        ttk.Label(size_frame, text="常用尺寸:").pack(anchor=tk.W, pady=(0, 5))
        
        preset_frame = ttk.Frame(size_frame)
        preset_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.preset_var = tk.StringVar(value="自定义")
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var, 
                                        state="readonly", width=25)
        self.preset_combo['values'] = (
            "自定义",
            "9:16 (1242×2208)",
            "1:1 (800×800)", 
            "16:9 (1920×1080)",
            "4:3 (1440×1080)",
            "3:4 (1242×1656)"
        )
        self.preset_combo.pack(side=tk.LEFT)
        self.preset_combo.bind('<<ComboboxSelected>>', self.on_preset_selected)
        
        # 自定义尺寸标签
        ttk.Label(size_frame, text="自定义尺寸:").pack(anchor=tk.W, pady=(10, 0))
        
        # 宽度设置
        width_input_frame = ttk.Frame(size_frame)
        width_input_frame.pack(fill=tk.X, pady=(5, 5))
        ttk.Label(width_input_frame, text="宽度:", width=6).pack(side=tk.LEFT)
        self.width_entry = ttk.Entry(width_input_frame, textvariable=self.canvas_width, width=8)
        self.width_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.width_entry.bind('<FocusOut>', self.on_entry_change)
        self.width_entry.bind('<Return>', self.on_entry_change)
        self.width_entry.bind('<FocusIn>', self.on_entry_focus_in)
        ttk.Label(width_input_frame, text="像素").pack(side=tk.LEFT)
        
        # 高度设置
        height_input_frame = ttk.Frame(size_frame)
        height_input_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(height_input_frame, text="高度:", width=6).pack(side=tk.LEFT)
        self.height_entry = ttk.Entry(height_input_frame, textvariable=self.canvas_height, width=8)
        self.height_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.height_entry.bind('<FocusOut>', self.on_entry_change)
        self.height_entry.bind('<Return>', self.on_entry_change)
        self.height_entry.bind('<FocusIn>', self.on_entry_focus_in)
        ttk.Label(height_input_frame, text="像素").pack(side=tk.LEFT)
        
        # 等比例缩放选项
        ttk.Checkbutton(size_frame, text="锁定宽高比", variable=self.keep_aspect_ratio,
                       command=self.on_aspect_ratio_change).pack(anchor=tk.W, pady=(5, 0))
        
        # 图片边距设置
        margin_frame = ttk.LabelFrame(parent, text="图片边距", padding=10)
        margin_frame.pack(fill=tk.X, pady=(0, 10))
        
        margin_input_frame = ttk.Frame(margin_frame)
        margin_input_frame.pack(fill=tk.X)
        ttk.Label(margin_input_frame, text="边距:", width=6).pack(side=tk.LEFT)
        self.margin_entry = ttk.Entry(margin_input_frame, textvariable=self.image_margin, width=8)
        self.margin_entry.pack(side=tk.LEFT, padx=(5, 5))
        self.margin_entry.bind('<FocusOut>', self.on_margin_change)
        self.margin_entry.bind('<Return>', self.on_margin_change)
        ttk.Label(margin_input_frame, text="像素").pack(side=tk.LEFT)
        
        # 背景颜色设置
        color_frame = ttk.LabelFrame(parent, text="背景颜色", padding=10)
        color_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.color_button = tk.Button(color_frame, text="选择背景颜色", 
                                    bg=self.bg_color, command=self.choose_color)
        self.color_button.pack(fill=tk.X)
        
        # 操作按钮
        action_frame = ttk.LabelFrame(parent, text="操作", padding=10)
        action_frame.pack(fill=tk.X)
        
        ttk.Button(action_frame, text="保存图片", command=self.save_image).pack(fill=tk.X, pady=(0, 5))
        ttk.Button(action_frame, text="重置设置", command=self.reset_settings).pack(fill=tk.X)
    
    def setup_preview_panel(self, parent):
        preview_frame = ttk.LabelFrame(parent, text="实时预览", padding="10")
        preview_frame.pack(fill=tk.BOTH, expand=True)
        
        self.preview_canvas = tk.Canvas(preview_frame, width=600, height=600, bg="white", relief=tk.SUNKEN, bd=1)
        self.preview_canvas.pack()
    
    def select_images(self):
        file_paths = filedialog.askopenfilenames(
            title="选择图片文件",
            filetypes=[("图片文件", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff")]
        )
        
        if file_paths:
            for file_path in file_paths:
                if file_path not in self.image_paths:
                    try:
                        img = Image.open(file_path)
                        self.images.append(img)
                        self.image_paths.append(file_path)
                        self.image_listbox.insert(tk.END, os.path.basename(file_path))
                    except Exception as e:
                        messagebox.showerror("错误", f"无法加载图片 {file_path}: {str(e)}")
            
            self.update_preview()
    
    def clear_images(self):
        self.images.clear()
        self.image_paths.clear()
        self.image_listbox.delete(0, tk.END)
        self.update_preview()
    
    def choose_color(self):
        color = colorchooser.askcolor(title="选择背景颜色", color=self.bg_color)
        if color[1]:
            self.bg_color = color[1]
            self.color_button.configure(bg=self.bg_color)
            self.update_preview()
    
    def on_size_change(self, value):
        self.update_preview()
    
    def on_entry_change(self, event):
        """处理输入框变化事件"""
        try:
            # 重置预设选择为自定义
            self.preset_var.set("自定义")
            
            # 验证输入值的范围
            width = self.canvas_width.get()
            height = self.canvas_height.get()
            
            # 限制范围
            if width < 100:
                self.canvas_width.set(100)
                width = 100
            elif width > 2000:
                self.canvas_width.set(2000)
                width = 2000
                
            if height < 100:
                self.canvas_height.set(100)
                height = 100
            elif height > 2000:
                self.canvas_height.set(2000)
                height = 2000
            
            # 如果启用锁定宽高比
            if self.keep_aspect_ratio.get():
                widget = event.widget
                if widget == self.width_entry:
                    # 根据宽度和锁定的宽高比调整高度
                    new_height = int(width / self.locked_aspect_ratio)
                    if new_height < 100:
                        new_height = 100
                    elif new_height > 2000:
                        new_height = 2000
                    self.canvas_height.set(new_height)
                elif widget == self.height_entry:
                    # 根据高度和锁定的宽高比调整宽度
                    new_width = int(height * self.locked_aspect_ratio)
                    if new_width < 100:
                        new_width = 100
                    elif new_width > 2000:
                        new_width = 2000
                    self.canvas_width.set(new_width)
                
            self.update_preview()
        except tk.TclError:
            # 如果输入无效，忽略
            pass
    
    def on_entry_focus_in(self, event):
        """输入框获得焦点时选中所有文本"""
        event.widget.select_range(0, tk.END)
    
    def on_aspect_ratio_change(self):
        """锁定宽高比选项变化时的处理"""
        if self.keep_aspect_ratio.get():
            # 启用锁定宽高比时，记录当前的宽高比
            width = self.canvas_width.get()
            height = self.canvas_height.get()
            if height > 0:
                self.locked_aspect_ratio = width / height
            else:
                self.locked_aspect_ratio = 1.0
    
    def on_margin_change(self, event):
        """处理边距输入框变化事件"""
        try:
            margin = self.image_margin.get()
            # 限制边距范围
            if margin < 0:
                self.image_margin.set(0)
            elif margin > 50:
                self.image_margin.set(50)
            self.update_preview()
        except tk.TclError:
            # 如果输入无效，忽略
            pass
    
    def on_preset_selected(self, event):
        """处理预设尺寸下拉选择事件"""
        selected = self.preset_var.get()
        
        preset_sizes = {
            "9:16 (1242×2208)": (1242, 2208),
            "1:1 (800×800)": (800, 800),
            "16:9 (1920×1080)": (1920, 1080),
            "4:3 (1440×1080)": (1440, 1080),
            "3:4 (1242×1656)": (1242, 1656)
        }
        
        if selected in preset_sizes:
            width, height = preset_sizes[selected]
            self.canvas_width.set(width)
            self.canvas_height.set(height)
            # 如果启用了锁定宽高比，更新锁定的比例
            if self.keep_aspect_ratio.get():
                self.locked_aspect_ratio = width / height
            self.update_preview()
    
    def get_grid_dimensions(self) -> Tuple[int, int]:
        """获取网格尺寸 (行数, 列数)"""
        layout = self.grid_layout.get()
        if layout == "4":
            return (2, 2)  # 2行2列
        elif layout == "6":
            return (3, 2)  # 3行2列 (2个图片一行，分3行)
        else:  # layout == "9"
            return (3, 3)  # 3行3列
    
    def create_grid_image(self) -> Optional[Image.Image]:
        if not self.images:
            return None
        
        canvas_w = self.canvas_width.get()
        canvas_h = self.canvas_height.get()
        rows, cols = self.get_grid_dimensions()
        margin = self.image_margin.get()
        
        # 创建背景画布
        result_image = Image.new('RGB', (canvas_w, canvas_h), self.bg_color)
        
        # 计算每个格子的尺寸（考虑边距）
        cell_width = canvas_w // cols
        cell_height = canvas_h // rows
        
        # 实际图片区域尺寸（减去边距）
        img_area_width = cell_width - 2 * margin
        img_area_height = cell_height - 2 * margin
        
        # 确保图片区域不会太小
        if img_area_width <= 0 or img_area_height <= 0:
            img_area_width = max(cell_width - 4, 10)
            img_area_height = max(cell_height - 4, 10)
        
        # 放置图片
        for i, img in enumerate(self.images[:rows * cols]):
            row = i // cols
            col = i % cols
            
            # 调整图片尺寸以适应格子（考虑边距）
            img_resized = img.copy()
            img_resized.thumbnail((img_area_width, img_area_height), Image.Resampling.LANCZOS)
            
            # 计算居中位置（考虑边距）
            x = col * cell_width + margin + (img_area_width - img_resized.width) // 2
            y = row * cell_height + margin + (img_area_height - img_resized.height) // 2
            
            # 粘贴图片
            result_image.paste(img_resized, (x, y))
        
        return result_image
    
    def update_preview(self):
        """更新预览"""
        if not self.images:
            self.preview_canvas.delete("all")
            return
        
        try:
            # 创建拼接图片
            grid_image = self.create_grid_image()
            if grid_image is None:
                return
            
            # 保存原始图片用于导出
            self.preview_image = grid_image.copy()
            
            # 缩放到预览尺寸
            preview_size = (600, 600)
            grid_image.thumbnail(preview_size, Image.Resampling.LANCZOS)
            
            # 转换为PhotoImage并显示
            photo = ImageTk.PhotoImage(grid_image)
            
            # 清除画布并显示新图片
            self.preview_canvas.delete("all")
            canvas_width = self.preview_canvas.winfo_width()
            canvas_height = self.preview_canvas.winfo_height()
            
            if canvas_width > 1 and canvas_height > 1:  # 确保画布已初始化
                x = (canvas_width - photo.width()) // 2
                y = (canvas_height - photo.height()) // 2
                self.preview_canvas.create_image(x, y, anchor=tk.NW, image=photo)
                self.preview_canvas.image = photo  # 保持引用
            
        except Exception as e:
            print(f"预览更新错误: {e}")
            self.preview_canvas.delete("all")
    
    def save_image(self):
        grid_image = self.create_grid_image()
        
        if not grid_image:
            messagebox.showwarning("警告", "请先选择图片")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="保存图片",
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png"), ("JPEG文件", "*.jpg"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                grid_image.save(file_path)
                messagebox.showinfo("成功", f"图片已保存到: {file_path}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")
    
    def reset_settings(self):
        self.grid_layout.set("9")
        self.canvas_width.set(600)
        self.canvas_height.set(600)
        self.keep_aspect_ratio.set(False)
        self.locked_aspect_ratio = 1.0
        self.image_margin.set(5)
        self.preset_var.set("自定义")
        self.bg_color = "#FFFFFF"
        self.color_button.configure(bg=self.bg_color)
        self.update_preview()

def main():
    root = tk.Tk()
    app = ImageGridTool(root)
    root.mainloop()

if __name__ == "__main__":
    main()