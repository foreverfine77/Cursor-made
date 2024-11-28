import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QTextEdit, QPushButton, QLabel, QMessageBox, QListWidget, QDialog, QLineEdit)
from PyQt6.QtCore import Qt, QSize, QPropertyAnimation, QEasingCurve, QPoint, QTimer
from PyQt6.QtGui import QFont, QKeyEvent, QIcon, QPixmap, QPainter, QRegion

def get_resource_path(relative_path):
    """获取资源文件的路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

class CustomMessageBox(QMessageBox):
    def __init__(self, parent=None, title="", text="", icon=QMessageBox.Icon.Information):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setText(text)
        self.setIcon(icon)
        
        # 设置样式
        self.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                padding: 10px;
            }
        """)
        
    def add_buttons(self, buttons=None):
        """添加自定义按钮"""
        if buttons is None:
            buttons = ["确定"]  # 使用中文字符串而不是 Unicode 转义序列
            
        for text in buttons:
            btn = self.addButton(text, QMessageBox.ButtonRole.AcceptRole)
            if text in ["删除", "确定删除"]:
                btn.setStyleSheet(delete_button_style)
            else:
                btn.setStyleSheet(button_style)
        return self.exec()

class QuestionInput(QTextEdit):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setPlaceholderText("请输入您的问题...")
        self.setMaximumHeight(100)
        self.setStyleSheet("""
            QTextEdit {
                border: 2px solid #4a4a4a;
                border-radius: 10px;
                padding: 5px;
                background-color: rgba(255, 255, 255, 220);
                color: #333;
                font-size: 14px;
            }
        """)
        
    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Return and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            self.callback()
        else:
            super().keyPressEvent(event)

class KnowledgeAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_knowledge_base()
        
    def init_ui(self):
        """初始界面"""
        # 设置程序图标
        icon_path = "assistant_icon.png"
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        # 定义按钮样式
        global search_button_style, button_style, delete_button_style
        
        search_button_style = """
            QPushButton {
                background-color: #2D1B69;
                color: white;
                border: 2px solid white;
                border-radius: 15px;
                padding: 10px 30px;
                font-size: 16px;
                min-width: 150px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D2B79;
                border-color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #1D0B59;
            }
        """
        
        button_style = """
            QPushButton {
                background-color: #2D1B69;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D2B79;
                border-color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #1D0B59;
            }
        """
        
        delete_button_style = """
            QPushButton {
                background-color: #c0392b;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e74c3c;
                border-color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """
        
        self.setWindowTitle("小通 - 通信知识助手")
        self.setMinimumSize(QSize(1000, 700))
        
        # 设置主窗口样式
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
        """)
        
        # 创建主部件和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 添加水印标签
        watermark_label = QLabel(self)
        watermark_pixmap = QPixmap("shuiyin.png")
        # 设置水印大小为80x80像素（更小的尺寸）
        watermark_pixmap = watermark_pixmap.scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        watermark_label.setPixmap(watermark_pixmap)
        watermark_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        # 设置水印透明度和样式
        watermark_label.setStyleSheet("QLabel { background: transparent; }")
        watermark_label.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        # 设置水印位置（与小通图标对齐，右上角）
        watermark_label.setGeometry(
            self.width() - watermark_pixmap.width() - 30,  # 调整右边距
            30,  # 调整上边距，与小通对齐
            watermark_pixmap.width(),
            watermark_pixmap.height()
        )
        
        # 确保水印随窗口大小变化而调整位置
        def resizeEvent(event):
            super(QMainWindow, self).resizeEvent(event)
            watermark_label.setGeometry(
                self.width() - watermark_pixmap.width() - 30,
                30,
                watermark_pixmap.width(),
                watermark_pixmap.height()
            )
        
        self.resizeEvent = resizeEvent
        
        # 创建左侧布局
        left_layout = QVBoxLayout()
        
        # 添加助手图像
        assistant_label = QLabel()
        if os.path.exists(icon_path):
            # 创建圆形图标
            original_pixmap = QIcon(icon_path).pixmap(QSize(150, 150))
            
            # 创建圆形遮罩
            mask = QPixmap(original_pixmap.size())
            mask.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(mask)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setBrush(Qt.GlobalColor.white)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(mask.rect())
            painter.end()
            
            # 应用遮罩并添加半透明效果
            rounded_pixmap = QPixmap(original_pixmap.size())
            rounded_pixmap.fill(Qt.GlobalColor.transparent)
            
            painter = QPainter(rounded_pixmap)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setClipRegion(QRegion(mask.rect(), QRegion.RegionType.Ellipse))
            
            # 绘制图标
            painter.drawPixmap(0, 0, original_pixmap)
            painter.end()
            
            assistant_label.setPixmap(rounded_pixmap)
        
        assistant_label.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 10px;
            }
        """)
        assistant_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 创建快捷问题按钮组
        button_group = QWidget()
        button_layout = QVBoxLayout(button_group)
        button_group.setStyleSheet("""
            QWidget {
                background-color: rgba(255, 255, 255, 0.05);
                border-radius: 20px;
                margin: 10px;
            }
        """)
        
        # 添加常用问题按钮
        common_questions = [
            ("📚 基础概念", "什么是通信"),
            ("🔄 调制解调", "什么是调制"),
            ("🔍 采样定理", "什么是采样"),
            ("📊 信噪比", "什么是信噪比"),
            ("🔐 编码技术", "什么是编码")
        ]
        
        for icon, question in common_questions:
            btn = QPushButton(f"{icon} {question}")
            btn.setStyleSheet(button_style)
            btn.clicked.connect(lambda checked, q=question: self.quick_search(q))
            button_layout.addWidget(btn)
            
        # 添加功能按钮
        notes_button = QPushButton("📝 我的笔记")
        notes_button.setStyleSheet(button_style)
        notes_button.clicked.connect(self.show_notes)
        button_layout.addWidget(notes_button)
        
        manage_knowledge_button = QPushButton("📚 知识管理")
        manage_knowledge_button.setStyleSheet(button_style)
        manage_knowledge_button.clicked.connect(self.manage_knowledge)
        button_layout.addWidget(manage_knowledge_button)
        
        # 添加到左侧布局
        left_layout.addWidget(assistant_label)
        left_layout.addWidget(button_group)
        left_layout.addStretch()
        
        # 创建右侧布局
        right_layout = QVBoxLayout()
        
        # 添加标题
        title = QLabel("小通 - 通信知识助手")
        title.setFont(QFont("Microsoft YaHei", 28, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("color: white; margin: 20px;")
        right_layout.addWidget(title)
        
        # 添加问题输入
        self.question_input = QuestionInput(self.handle_question)
        right_layout.addWidget(self.question_input)
        
        # 添加搜索按钮
        search_button = QPushButton("搜索")
        search_button.setStyleSheet(search_button_style)
        search_button.clicked.connect(self.handle_question)
        right_layout.addWidget(search_button, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # 添加答案显示区域
        self.answer_display = QTextEdit()
        self.answer_display.setReadOnly(True)
        self.answer_display.setPlaceholderText("答案将在这里显示...")
        self.answer_display.setStyleSheet("""
            QTextEdit {
                border: 2px solid #4a4a4a;
                border-radius: 10px;
                padding: 10px;
                background-color: rgba(255, 255, 255, 220);
                color: #333;
                font-size: 14px;
            }
        """)
        right_layout.addWidget(self.answer_display)
        
        # 设置布局比例
        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 3)
        
        # 设置边距
        right_layout.setContentsMargins(20, 20, 20, 20)
        right_layout.setSpacing(15)

        # 为小通图标添加呼吸效果
        self.breath_animation = QPropertyAnimation(assistant_label, b"pos")
        self.breath_animation.setDuration(2000)  # 2秒一个周期
        self.breath_animation.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        def update_breath():
            start_pos = assistant_label.pos()
            self.breath_animation.setStartValue(start_pos)
            self.breath_animation.setEndValue(QPoint(start_pos.x(), start_pos.y() + 10))
            self.breath_animation.start()
            # 动画结束后反向运动
            self.breath_animation.finished.connect(
                lambda: self.breath_animation.setDirection(
                    QPropertyAnimation.Direction.Backward 
                    if self.breath_animation.direction() == QPropertyAnimation.Direction.Forward 
                    else QPropertyAnimation.Direction.Forward
                )
            )
        
        # 启动呼吸动画
        update_breath()
        self.breath_animation.finished.connect(lambda: self.breath_animation.start())
        
        # 为水印添加渐变效果
        self.watermark_opacity = QPropertyAnimation(watermark_label, b"windowOpacity")
        self.watermark_opacity.setDuration(3000)  # 3秒一个周期
        self.watermark_opacity.setStartValue(0.3)
        self.watermark_opacity.setEndValue(0.8)
        self.watermark_opacity.setEasingCurve(QEasingCurve.Type.InOutSine)
        
        def update_watermark():
            self.watermark_opacity.start()
            self.watermark_opacity.finished.connect(
                lambda: self.watermark_opacity.setDirection(
                    QPropertyAnimation.Direction.Backward 
                    if self.watermark_opacity.direction() == QPropertyAnimation.Direction.Forward 
                    else QPropertyAnimation.Direction.Forward
                )
            )
        
        # 启动水印动画
        update_watermark()
        self.watermark_opacity.finished.connect(lambda: self.watermark_opacity.start())
        
        # 为按钮添加悬停缩放效果
        def setup_button_animation(button):
            def on_enter(e):
                # 创建大小动画
                animation = QPropertyAnimation(button, b"minimumSize")
                animation.setDuration(100)
                animation.setStartValue(button.size())
                animation.setEndValue(QSize(int(button.size().width() * 1.1), 
                                          int(button.size().height() * 1.1)))
                animation.start()

            def on_leave(e):
                # 创建大小动画
                animation = QPropertyAnimation(button, b"minimumSize")
                animation.setDuration(100)
                animation.setStartValue(button.size())
                animation.setEndValue(QSize(int(button.size().width() / 1.1), 
                                          int(button.size().height() / 1.1)))
                animation.start()

            button.enterEvent = on_enter
            button.leaveEvent = on_leave
        
        # 为所有按钮添加动画效果
        for button in self.findChildren(QPushButton):
            setup_button_animation(button)

    def load_knowledge_base(self):
        """加载知识库"""
        try:
            with open('knowledge_base.json', 'r', encoding='utf-8') as file:
                self.knowledge_base = json.load(file)
                print(f"成功加载知识库，共 {len(self.knowledge_base)} 条记录")
        except FileNotFoundError:
            QMessageBox.warning(self, "警告", "找不到知识库文件！")
            self.knowledge_base = {}
        except json.JSONDecodeError:
            QMessageBox.critical(self, "错误", "知识库文件格式错误！")
            self.knowledge_base = {}
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载知识库时出错：{str(e)}")
            self.knowledge_base = {}
            
    def handle_question(self):
        """处理问题"""
        question = self.question_input.toPlainText().strip()
        if not question:
            self.answer_display.setText("请输入问题！")
            return
            
        answer = self.search_answer(question)
        self.answer_display.setText(answer)
        self.question_input.clear()
        
    def search_answer(self, question):
        """搜索答案"""
        question = question.lower()
        
        # 精确匹配
        if question in self.knowledge_base:
            return self.knowledge_base[question]
            
        # 关键词匹配
        for key in self.knowledge_base:
            if question in key.lower() or key.lower() in question:
                return self.knowledge_base[key]
                
        # 模糊匹配
        best_match = None
        highest_similarity = 0.3
        
        for key in self.knowledge_base:
            similarity = self.calculate_similarity(question, key.lower())
            if similarity > highest_similarity:
                highest_similarity = similarity
                best_match = key
                
        if best_match:
            return self.knowledge_base[best_match]
            
        return "抱歉，我还不知道这个问题的答案。\n\n建议：\n1. 换个方式提问\n2. 使用更简单的关键词\n3. 确保问题与通信原理相关"
        
    def calculate_similarity(self, str1, str2):
        """计算字符串相似度"""
        set1 = set(str1)
        set2 = set(str2)
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        return intersection / union if union else 0

    def show_notes(self):
        """显示笔记对话框"""
        dialog = NotesDialog(self)
        dialog.exec()
        
    def manage_knowledge(self):
        """显示知识管理对话框"""
        dialog = ManageKnowledgeDialog(self.knowledge_base, self)
        if dialog.exec():
            self.save_knowledge_base()

    def quick_search(self, question):
        """快速搜索功能"""
        answer = self.search_answer(question)
        self.answer_display.setText(answer)

    def save_knowledge_base(self):
        """保存知识库"""
        try:
            with open('knowledge_base.json', 'w', encoding='utf-8') as file:
                json.dump(self.knowledge_base, file, ensure_ascii=False, indent=4)
            print("知识库保存成功")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存知识库时出错：{str(e)}")

class NotesDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("我的笔记")
        self.setMinimumSize(800, 600)
        
        # 初始化笔记
        try:
            with open('notes.json', 'r', encoding='utf-8') as file:
                self.notes = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            self.notes = {}

        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
            QTextEdit, QLineEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 添加标题
        title = QLabel("✍️ 添加新笔记")
        title.setStyleSheet("font-size: 24px; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 添加笔记标题输入
        title_label = QLabel("📝 笔记标题")
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("请输入笔记标题...")
        layout.addWidget(title_label)
        layout.addWidget(self.title_edit)

        # 添加笔记内容输入
        content_label = QLabel("📄 笔记内容")
        self.content_edit = QTextEdit()
        self.content_edit.setPlaceholderText("请输入笔记内容...")
        layout.addWidget(content_label)
        layout.addWidget(self.content_edit)

        # 修按钮样式部分
        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)
        
        save_button = QPushButton("💾 保存笔记")
        save_button.setStyleSheet(button_style)
        save_button.clicked.connect(self.save_note)
        
        view_button = QPushButton("📚 查看所有笔记")
        view_button.setStyleSheet(button_style)
        view_button.clicked.connect(self.view_notes)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(view_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

    def save_note(self):
        """保存笔记"""
        title = self.title_edit.text().strip()
        content = self.content_edit.toPlainText().strip()
        
        if not title or not content:
            msg = CustomMessageBox(self, "警告", "标题和内容不能为空！", QMessageBox.Icon.Warning)
            msg.add_buttons()
            return
        
        self.notes[title] = content
        
        try:
            with open('notes.json', 'w', encoding='utf-8') as file:
                json.dump(self.notes, file, ensure_ascii=False, indent=4)
            msg = CustomMessageBox(self, "成功", "笔记保存成功！")
            msg.add_buttons()
            self.title_edit.clear()
            self.content_edit.clear()
        except Exception as e:
            msg = CustomMessageBox(self, "错误", f"保存笔记时出错：{str(e)}", QMessageBox.Icon.Critical)
            msg.add_buttons()

    def view_notes(self):
        """查看所有笔记"""
        viewer = NotesViewer(self.notes, self)
        viewer.exec()

class NotesViewer(QDialog):
    def __init__(self, notes, parent=None):
        super().__init__(parent)
        self.setWindowTitle("所有笔记")
        self.setMinimumSize(1000, 600)
        self.notes = notes

        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
            QListWidget {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QListWidget::item {
                color: white;
                padding: 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 5px;
            }
            QListWidget::item:selected {
                color: white;
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                font-weight: bold;
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #00b894;
                color: white;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 120px;
            }
            QPushButton:hover {
                background-color: #00a187;
            }
            QPushButton#backButton {
                background-color: transparent;
                border: 1px solid rgba(255, 255, 255, 0.3);
                color: white;
                padding: 5px 15px;
                min-width: 80px;
            }
            QPushButton#backButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
                margin: 10px;
            }
        """)

        # 创建主布局
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)

        # 修改顶部布局
        top_layout = QHBoxLayout()
        
        # 添加返回按钮
        back_button = QPushButton("← 返回")
        back_button.setObjectName("backButton")
        back_button.setStyleSheet(button_style)
        back_button.clicked.connect(self.close)
        back_button.setFixedWidth(120)
        top_layout.addWidget(back_button)
        
        # 添加标题
        title_label = QLabel("📚 我的笔记")
        title_label.setStyleSheet("font-size: 24px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(title_label)
        
        # 添加删除按钮
        delete_button = QPushButton("🗑️ 删除笔记")
        delete_button.setStyleSheet(delete_button_style)
        delete_button.clicked.connect(self.delete_note)
        delete_button.setFixedWidth(120)
        top_layout.addWidget(delete_button)
        
        main_layout.addLayout(top_layout)

        # 添加内容区域
        content_layout = QHBoxLayout()
        
        # 左侧布局
        left_layout = QVBoxLayout()
        notes_label = QLabel("📝 笔记列表")
        left_layout.addWidget(notes_label)
        
        # 笔记列表
        self.notes_list = QListWidget()
        self.notes_list.addItems(self.notes.keys())
        self.notes_list.currentItemChanged.connect(self.show_note)
        left_layout.addWidget(self.notes_list)
        
        content_layout.addLayout(left_layout, 1)

        # 右侧布局
        right_layout = QVBoxLayout()
        content_label = QLabel("📄 笔记内容")
        right_layout.addWidget(content_label)
        
        # 笔记内容显示
        self.note_display = QTextEdit()
        self.note_display.setReadOnly(True)
        self.note_display.setPlaceholderText("请从左侧选择要查看的笔记...")
        right_layout.addWidget(self.note_display)
        
        content_layout.addLayout(right_layout, 2)
        
        main_layout.addLayout(content_layout)

    def show_note(self, current, previous):
        """显示选中的笔记内容"""
        if current:
            title = current.text()
            self.note_display.setText(self.notes[title])

    def delete_note(self):
        """删除笔记"""
        current_item = self.notes_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "警告", "请先选择要删除的笔记！")
            return

        title = current_item.text()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认删除")
        msg_box.setText(f"确定要删除笔记「{title}」吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        # 添加自定义按钮并设置样式
        msg_box.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                background-color: #2D1B69;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D2B79;
            }
            QPushButton:pressed {
                background-color: #1D0B59;
            }
        """)
        
        # 添加自定义按钮
        delete_button = msg_box.addButton("确定删除", QMessageBox.ButtonRole.YesRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(cancel_button)

        msg_box.exec()
        
        if msg_box.clickedButton() == delete_button:
            try:
                # 从字典中删除
                del self.notes[title]
                # 保存到文件
                with open('notes.json', 'w', encoding='utf-8') as file:
                    json.dump(self.notes, file, ensure_ascii=False, indent=4)
                # 从列表控件中移除
                self.notes_list.takeItem(self.notes_list.row(current_item))
                # 清空显示区域
                self.note_display.clear()
                # 更新父窗口的笔记数据
                if isinstance(self.parent(), NotesDialog):
                    self.parent().notes = self.notes
                
                # 显示删除成功提示（使用自定义样式）
                success_box = QMessageBox(self)
                success_box.setWindowTitle("成功")
                success_box.setText("笔记已删除！")
                success_box.setIcon(QMessageBox.Icon.Information)
                
                # 置样式
                success_box.setStyleSheet("""
                    QMessageBox {
                        background: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 1,
                            stop: 0 #1a0033,
                            stop: 0.5 #2d004d,
                            stop: 1 #400066
                        );
                    }
                    QMessageBox QLabel {
                        color: white;
                        font-size: 14px;
                        padding: 10px;
                    }
                    QPushButton {
                        background-color: #2D1B69;
                        color: white;
                        border: 2px solid white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-size: 14px;
                        min-width: 120px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #3D2B79;
                    }
                    QPushButton:pressed {
                        background-color: #1D0B59;
                    }
                """)
                
                # 添加确定按钮
                ok_button = success_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                success_box.setDefaultButton(ok_button)
                
                success_box.exec()
                
            except Exception as e:
                error_msg = QMessageBox(self)
                error_msg.setWindowTitle("错误")
                error_msg.setText(f"删除笔记时出错：{str(e)}")
                error_msg.setIcon(QMessageBox.Icon.Critical)
                error_msg.setStyleSheet("""
                    QMessageBox {
                        background: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 1,
                            stop: 0 #1a0033,
                            stop: 0.5 #2d004d,
                            stop: 1 #400066
                        );
                    }
                    QMessageBox QLabel {
                        color: white;
                        font-size: 14px;
                        padding: 10px;
                    }
                    QPushButton {
                        background-color: #2D1B69;
                        color: white;
                        border: 2px solid white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-size: 14px;
                        min-width: 120px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #3D2B79;
                    }
                    QPushButton:pressed {
                        background-color: #1D0B59;
                    }
                """)
                ok_button = error_msg.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                error_msg.setDefaultButton(ok_button)
                error_msg.exec()

class ManageKnowledgeDialog(QDialog):
    def __init__(self, knowledge_base, parent=None):
        super().__init__(parent)
        self.knowledge_base = knowledge_base
        self.setWindowTitle("知识管理")
        self.setMinimumSize(1000, 600)
        
        # 设置样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
            QListWidget {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 16px;
            }
            QListWidget::item {
                color: white;
                padding: 10px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 5px;
                font-size: 16px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 15px;
                font-size: 16px;
                line-height: 1.5;
            }
            QLabel {
                color: white;
                font-size: 18px;
                font-weight: bold;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # 顶部布局
        top_layout = QHBoxLayout()
        
        # 添加返回按钮
        back_button = QPushButton("← 返回")
        back_button.setStyleSheet(button_style)
        back_button.clicked.connect(self.accept)
        back_button.setFixedWidth(120)
        top_layout.addWidget(back_button)
        
        # 添加标题
        title = QLabel("📚 知识管理")
        title.setStyleSheet("font-size: 24px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        top_layout.addWidget(title)
        
        # 添加删除按钮
        delete_button = QPushButton("🗑️ 删除知识")
        delete_button.setStyleSheet(delete_button_style)
        delete_button.clicked.connect(self.delete_knowledge)
        delete_button.setFixedWidth(120)
        top_layout.addWidget(delete_button)
        
        layout.addLayout(top_layout)

        # 内容布局
        content_layout = QHBoxLayout()
        
        # 左侧布局
        left_layout = QVBoxLayout()
        question_label = QLabel("❓ 问题列表")
        left_layout.addWidget(question_label)
        
        # 问题列表
        self.question_list = QListWidget()
        self.question_list.addItems(self.knowledge_base.keys())
        self.question_list.currentItemChanged.connect(self.show_answer)
        left_layout.addWidget(self.question_list)
        
        content_layout.addLayout(left_layout, 1)

        # 右侧布局
        right_layout = QVBoxLayout()
        answer_label = QLabel("💡 答案内容")
        right_layout.addWidget(answer_label)
        
        # 答案显示
        self.answer_display = QTextEdit()
        self.answer_display.setReadOnly(True)
        self.answer_display.setPlaceholderText("请从左侧选择要查看的问题...")
        right_layout.addWidget(self.answer_display)
        
        content_layout.addLayout(right_layout, 2)
        layout.addLayout(content_layout)

        # 底部按钮布局
        button_layout = QHBoxLayout()
        
        add_button = QPushButton("➕ 添加知识")
        add_button.setStyleSheet(button_style)
        add_button.clicked.connect(self.add_knowledge)
        
        button_layout.addStretch()
        button_layout.addWidget(add_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

    def show_answer(self, current, previous):
        """显示选中的答案"""
        if current:
            question = current.text()
            self.answer_display.setText(self.knowledge_base[question])

    def add_knowledge(self):
        """添加新知识"""
        dialog = AddKnowledgeDialog(self)
        if dialog.exec():
            question = dialog.question_edit.toPlainText().strip()
            answer = dialog.answer_edit.toPlainText().strip()
            
            if not question or not answer:
                msg = CustomMessageBox(self, "警", "问题和答案不能为空！", QMessageBox.Icon.Warning)
                msg.add_buttons()
                return
            
            if question in self.knowledge_base:
                msg = CustomMessageBox(
                    self, 
                    "确认更新", 
                    f"问题「{question}」已存在，是否要更新答案？",
                    QMessageBox.Icon.Question
                )
                if msg.add_buttons(["更新", "取消"]) != 0:
                    return
            
            self.knowledge_base[question] = answer
            if question not in [self.question_list.item(i).text() for i in range(self.question_list.count())]:
                self.question_list.addItem(question)
            msg = CustomMessageBox(self, "成功", "知识点已保存！")
            msg.add_buttons()

    def delete_knowledge(self):
        """删除知识"""
        current_item = self.question_list.currentItem()
        if not current_item:
            warning_box = QMessageBox(self)
            warning_box.setWindowTitle("警告")
            warning_box.setText("请先选择要删除的知识！")
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setStyleSheet("""
                QMessageBox {
                    background: qlineargradient(
                        x1: 0, y1: 0, x2: 1, y2: 1,
                        stop: 0 #1a0033,
                        stop: 0.5 #2d004d,
                        stop: 1 #400066
                    );
                }
                QMessageBox QLabel {
                    color: white;
                    font-size: 14px;
                    padding: 10px;
                }
                QPushButton {
                    background-color: #2D1B69;
                    color: white;
                    border: 2px solid white;
                    border-radius: 10px;
                    padding: 10px 20px;
                    font-size: 14px;
                    min-width: 120px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #3D2B79;
                }
                QPushButton:pressed {
                    background-color: #1D0B59;
                }
            """)
            ok_button = warning_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
            warning_box.setDefaultButton(ok_button)
            warning_box.exec()
            return

        question = current_item.text()
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("确认删除")
        msg_box.setText(f"确定要删除知识「{question}」吗？")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setStyleSheet("""
            QMessageBox {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
            QMessageBox QLabel {
                color: white;
                font-size: 14px;
                padding: 10px;
            }
            QPushButton {
                background-color: #2D1B69;
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 14px;
                min-width: 120px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3D2B79;
            }
            QPushButton:pressed {
                background-color: #1D0B59;
            }
        """)
        
        delete_button = msg_box.addButton("确定删除", QMessageBox.ButtonRole.YesRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.ButtonRole.NoRole)
        msg_box.setDefaultButton(cancel_button)

        msg_box.exec()
        
        if msg_box.clickedButton() == delete_button:
            try:
                # 从知识库中删除
                del self.knowledge_base[question]
                # 更新父窗口的知识库
                if isinstance(self.parent(), KnowledgeAssistant):
                    self.parent().knowledge_base = self.knowledge_base
                # 从列表控件中移除
                self.question_list.takeItem(self.question_list.row(current_item))
                # 清空显示区域
                self.answer_display.clear()
                # 保存到文件
                with open('knowledge_base.json', 'w', encoding='utf-8') as file:
                    json.dump(self.knowledge_base, file, ensure_ascii=False, indent=4)
                
                # 显示成功提示
                success_box = QMessageBox(self)
                success_box.setWindowTitle("成功")
                success_box.setText("知识已删除！")
                success_box.setIcon(QMessageBox.Icon.Information)
                success_box.setStyleSheet("""
                    QMessageBox {
                        background: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 1,
                            stop: 0 #1a0033,
                            stop: 0.5 #2d004d,
                            stop: 1 #400066
                        );
                    }
                    QMessageBox QLabel {
                        color: white;
                        font-size: 14px;
                        padding: 10px;
                    }
                    QPushButton {
                        background-color: #2D1B69;
                        color: white;
                        border: 2px solid white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-size: 14px;
                        min-width: 120px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #3D2B79;
                    }
                    QPushButton:pressed {
                        background-color: #1D0B59;
                    }
                """)
                ok_button = success_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                success_box.setDefaultButton(ok_button)
                success_box.exec()
                    
            except Exception as e:
                error_box = QMessageBox(self)
                error_box.setWindowTitle("错误")
                error_box.setText(f"删除知识时出错：{str(e)}")
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setStyleSheet("""
                    QMessageBox {
                        background: qlineargradient(
                            x1: 0, y1: 0, x2: 1, y2: 1,
                            stop: 0 #1a0033,
                            stop: 0.5 #2d004d,
                            stop: 1 #400066
                        );
                    }
                    QMessageBox QLabel {
                        color: white;
                        font-size: 14px;
                        padding: 10px;
                    }
                    QPushButton {
                        background-color: #2D1B69;
                        color: white;
                        border: 2px solid white;
                        border-radius: 10px;
                        padding: 10px 20px;
                        font-size: 14px;
                        min-width: 120px;
                        font-weight: bold;
                    }
                    QPushButton:hover {
                        background-color: #3D2B79;
                    }
                    QPushButton:pressed {
                        background-color: #1D0B59;
                    }
                """)
                ok_button = error_box.addButton("确定", QMessageBox.ButtonRole.AcceptRole)
                error_box.setDefaultButton(ok_button)
                error_box.exec()

class AddKnowledgeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("补充知识")
        self.setMinimumSize(800, 600)
        
        # 设置对话框样式
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(
                    x1: 0, y1: 0, x2: 1, y2: 1,
                    stop: 0 #1a0033,
                    stop: 0.5 #2d004d,
                    stop: 1 #400066
                );
            }
            QTextEdit {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                border: 2px solid white;
                border-radius: 10px;
                padding: 10px;
                font-size: 14px;
            }
            QLabel {
                color: white;
                font-size: 16px;
                font-weight: bold;
                margin-bottom: 5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)

        # 添加标题
        title = QLabel("➕ 补充知识")
        title.setStyleSheet("font-size: 24px; margin-bottom: 20px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # 添加问题输入
        question_label = QLabel("❓ 问题")
        self.question_edit = QTextEdit()
        self.question_edit.setPlaceholderText("请输入问题...")
        self.question_edit.setMaximumHeight(100)
        layout.addWidget(question_label)
        layout.addWidget(self.question_edit)

        # 添加答案输入
        answer_label = QLabel("💡 答案")
        self.answer_edit = QTextEdit()
        self.answer_edit.setPlaceholderText("请输��答案...")
        layout.addWidget(answer_label)
        layout.addWidget(self.answer_edit)

        # 添加按钮
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("💾 保存")
        save_button.setStyleSheet(button_style)
        save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("❌ 取消")
        cancel_button.setStyleSheet(button_style)
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        button_layout.addStretch()
        
        layout.addLayout(button_layout)

def main():
    """程序入口"""
    try:
        app = QApplication(sys.argv)
        window = KnowledgeAssistant()
        window.show()
        sys.exit(app.exec())
    except Exception as e:
        print(f"程序运行出错：{str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 