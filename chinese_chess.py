import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGridLayout, QWidget, 
                            QPushButton, QMessageBox, QVBoxLayout, QHBoxLayout, 
                            QLabel, QSystemTrayIcon, QMenu, QAction, QStyle)
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QFont, QPainter, QPen, QColor

class ChessBoardWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(300, 500)  # 调整最小尺寸
        
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(QColor(0, 0, 0), 2)
        painter.setPen(pen)
        
        # 计算棋盘绘制区域
        board_width = self.width()
        board_height = self.height() - 50
        cell_size = min(board_width // 9, board_height // 10)
        margin_x = (board_width - cell_size * 8) // 2
        margin_y = 25
        
        # 绘制横线
        for i in range(10):
            y = margin_y + i * cell_size
            # 绘制完整横线
            painter.drawLine(margin_x, y, margin_x + cell_size * 8, y)
        
        # 绘制竖线
        for i in range(9):
            x = margin_x + i * cell_size
            # 上半部分
            painter.drawLine(x, margin_y, x, margin_y + cell_size * 4)
            # 下半部分
            painter.drawLine(x, margin_y + cell_size * 5, x, margin_y + cell_size * 9)
        
        # 绘制楚河汉界
        # 将浮点数坐标转换为整数
        x1 = int(margin_x + cell_size * 1.5)
        x2 = int(margin_x + cell_size * 5.5)
        y = int(margin_y + cell_size * 4.5)
        
        painter.drawText(x1, y, "楚河")
        painter.drawText(x2, y, "汉界")
        
        # 绘制九宫格斜线
        # 上方九宫格
        painter.drawLine(margin_x + cell_size * 3, margin_y,
                        margin_x + cell_size * 5, margin_y + cell_size * 2)
        painter.drawLine(margin_x + cell_size * 5, margin_y,
                        margin_x + cell_size * 3, margin_y + cell_size * 2)
        
        # 下方九宫格
        painter.drawLine(margin_x + cell_size * 3, margin_y + cell_size * 7,
                        margin_x + cell_size * 5, margin_y + cell_size * 9)
        painter.drawLine(margin_x + cell_size * 5, margin_y + cell_size * 7,
                        margin_x + cell_size * 3, margin_y + cell_size * 9)

class ChessBoard(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # 移除桌面小组件相关的窗口标志，使用普通窗口
        self.setWindowFlags(Qt.Window)  # 使用普通窗口标志
        
        # 初始化属性
        self.selected_piece = None
        self.is_red_turn = True  # 红方先走
        self.game_over = False   # 添加游戏结束标志
        self.move_history = []   # 添加移动历史记录
        
        # 初始化棋盘和按钮数组
        self.board = [['' for _ in range(9)] for _ in range(10)]
        self.buttons = [[None for _ in range(9)] for _ in range(10)]
        
        # 添加计时相关的属性
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.current_turn_time = 0  # 当前回合用时（秒）
        
        # 初始化UI
        self.initUI()
        self.start_timer()
        
        # 修改窗口样式
        self.setStyleSheet('''
            QMainWindow {
                background-color: #F0E4D0;
            }
        ''')
        
        # 设置固定大小
        self.setFixedSize(300, 450)

    def initUI(self):
        # 创建主窗口部件
        main_widget = QWidget(self)
        self.setCentralWidget(main_widget)
        
        # 修改容器尺寸和布局
        board_container = QWidget()
        board_container.setFixedSize(300, 350)  # 增加容器高度
        
        # 创建棋盘背景部件
        board_background = ChessBoardWidget(board_container)
        board_background.setGeometry(0, 0, 300, 350)
        
        # 创建棋盘部件并设置为透明背景
        board_widget = QWidget(board_container)
        board_widget.setGeometry(0, 0, 300, 350)
        
        # 计算棋子位置 - 使用相同的计算逻辑
        board_width = 300
        board_height = 300  # 实际棋盘区域高度
        cell_size = min(board_width // 9, board_height // 10)
        margin_x = (board_width - cell_size * 8) // 2
        margin_y = 25
        
        # 创建棋盘按钮
        for row in range(10):
            for col in range(9):
                button = QPushButton('', board_widget)
                button_size = int(cell_size * 0.8)
                button.setFixedSize(button_size, button_size)
                button.setFont(QFont('SimSun', int(cell_size * 0.4)))
                button.setStyleSheet('''
                    QPushButton { 
                        background: transparent;
                        border: none;
                        color: transparent;
                    }
                    QPushButton:hover { 
                        background: transparent;
                        border: none;
                    }
                    QPushButton:pressed { 
                        background: transparent;
                        border: none;
                    }
                    QPushButton:focus { 
                        outline: none;
                        border: none;
                    }
                ''')
                button.clicked.connect(lambda _, r=row, c=col: self.on_click(r, c))
                
                # 算棋子位置
                x = int(margin_x + col * cell_size - (button_size // 2))
                y = int(margin_y + row * cell_size - (button_size // 2))
                button.move(x, y)
                
                self.buttons[row][col] = button
        
        # 修改控制面板布局
        control_panel = QWidget()
        control_panel_layout = QHBoxLayout(control_panel)
        control_panel_layout.setContentsMargins(5, 5, 5, 5)  # 统一边距
        control_panel_layout.setSpacing(10)  # 减小间距
        
        # 设置统一的样式
        control_style = '''
            QWidget {
                color: #8B4513;
                font-family: SimSun;
                font-size: 11pt;
                font-weight: bold;
                background-color: rgba(255, 248, 220, 200);
                border: 2px solid #8B4513;
                border-radius: 15px;
                padding: 3px;  /* 减小内边距 */
                min-width: 70px;  /* 减小最小宽度 */
                min-height: 25px;
            }
            QPushButton:hover {
                background-color: rgba(255, 222, 173, 220);
            }
            QPushButton:pressed {
                background-color: rgba(222, 184, 135, 220);
            }
        '''
        
        # 添加悔棋按钮
        undo_button = QPushButton('悔棋', self)
        undo_button.setFixedSize(70, 25)  # 统一大小
        undo_button.setStyleSheet(control_style)
        undo_button.clicked.connect(self.undo_move)
        
        # 添加当前回合时间显示
        self.turn_time_label = QLabel('00:00')
        self.turn_time_label.setFixedSize(70, 25)  # 统一大小
        self.turn_time_label.setStyleSheet(control_style)
        self.turn_time_label.setAlignment(Qt.AlignCenter)
        
        # 添加重新开始按钮
        restart_button = QPushButton('重新开始', self)
        restart_button.setFixedSize(70, 25)  # 统一大小
        restart_button.setStyleSheet(control_style)
        restart_button.clicked.connect(self.restart_game)
        
        # 将所有控件添加到布局中，使用固定间距
        control_panel_layout.addStretch(1)
        control_panel_layout.addWidget(undo_button)
        control_panel_layout.addSpacing(5)  # 添加固定间距
        control_panel_layout.addWidget(self.turn_time_label)
        control_panel_layout.addSpacing(5)  # 添加固定间距
        control_panel_layout.addWidget(restart_button)
        control_panel_layout.addStretch(1)
        
        # 创建一个垂直布局来容纳棋盘和控制面板
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # 添加一个弹性空间，将控制面板推到顶部
        main_layout.addWidget(control_panel)
        main_layout.addWidget(board_container)
        
        # 设置窗口属性
        self.setWindowTitle('中国象棋')
        self.setFixedSize(300, 400)  # 适当增加窗口高度
        
        # 初始化棋盘
        self.init_board()
        self.update_board()

    def init_board(self):
        # 红方(下方)
        red_pieces = {
            9: ['车', '马', '相', '仕', '帅', '仕', '相', '马', '车'],
            7: ['', '炮', '', '', '', '', '', '炮', ''],  # 红炮在第7行第2列和第8列
            6: ['兵', '', '兵', '', '兵', '', '兵', '', '兵'],  # 红兵在第6行
        }
        
        # 黑方(上方)
        black_pieces = {
            0: ['車', '馬', '象', '士', '将', '士', '象', '馬', '車'],  # 修复了黑象的位置
            2: ['', '砲', '', '', '', '', '', '砲', ''],  # 黑炮在第2行第2列和第8列
            3: ['卒', '', '卒', '', '卒', '', '卒', '', '卒']  # 黑卒的位置
        }
        
        # 放置红方棋子
        for row, pieces in red_pieces.items():
            for col, piece in enumerate(pieces):
                if piece:
                    self.board[row][col] = piece
        
        # 放置黑方棋子
        for row, pieces in black_pieces.items():
            for col, piece in enumerate(pieces):
                if piece:
                    self.board[row][col] = piece

    def update_board(self):
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                self.buttons[row][col].setText(piece)
                self.update_button_style(self.buttons[row][col], row, col)

    def is_valid_move(self, start_row, start_col, end_row, end_col):
        piece = self.board[start_row][start_col]
        target = self.board[end_row][end_col]
        
        # 检查否吃自己的子
        if target:
            is_red_target = target in '车马相仕帅炮兵'
            is_red_piece = piece in '车马相仕帅炮兵'
            if is_red_target == is_red_piece:
                return False

        # 根据不同的棋子类型检查移动是否合法
        if piece in '车車':
            return self.is_valid_chariot_move(start_row, start_col, end_row, end_col)
        elif piece in '马馬':
            return self.is_valid_horse_move(start_row, start_col, end_row, end_col)
        elif piece in '相象':
            return self.is_valid_elephant_move(start_row, start_col, end_row, end_col)
        elif piece in '仕士':
            return self.is_valid_advisor_move(start_row, start_col, end_row, end_col)
        elif piece in '帅将':
            return self.is_valid_general_move(start_row, start_col, end_row, end_col)
        elif piece in '炮砲':
            return self.is_valid_cannon_move(start_row, start_col, end_row, end_col)
        elif piece in '兵卒':
            return self.is_valid_pawn_move(start_row, start_col, end_row, end_col)
        return False

    def is_valid_chariot_move(self, start_row, start_col, end_row, end_col):
        # 只能直移动
        if start_row != end_row and start_col != end_col:
            return False
            
        # 检查路径上是否有其他棋子
        if start_row == end_row:  # 横向移动
            min_col = min(start_col, end_col)
            max_col = max(start_col, end_col)
            for col in range(min_col + 1, max_col):
                if self.board[start_row][col]:
                    return False
        else:  # 纵向移动
            min_row = min(start_row, end_row)
            max_row = max(start_row, end_row)
            for row in range(min_row + 1, max_row):
                if self.board[row][start_col]:
                    return False
        return True

    def is_valid_horse_move(self, start_row, start_col, end_row, end_col):
        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)
        
        # 马走"日"字
        if not ((row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)):
            return False
            
        # 检查马脚
        if row_diff == 2:
            block_row = start_row + (1 if end_row > start_row else -1)
            if self.board[block_row][start_col]:
                return False
        else:
            block_col = start_col + (1 if end_col > start_col else -1)
            if self.board[start_row][block_col]:
                return False
        return True

    def is_valid_elephant_move(self, start_row, start_col, end_row, end_col):
        # 相/走田字，不能过河
        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)
        
        # 检查是否走"田"字
        if row_diff != 2 or col_diff != 2:
            return False
        
        # 检查是否过河
        is_red = self.board[start_row][start_col] == '相'
        if is_red and end_row < 5:  # 红相不能过河
            return False
        if not is_red and end_row > 4:  # 黑象不能过河
            return False
        
        # 检查象心是否被塞
        block_row = (start_row + end_row) // 2
        block_col = (start_col + end_col) // 2
        if self.board[block_row][block_col]:
            return False
        
        return True

    def is_valid_advisor_move(self, start_row, start_col, end_row, end_col):
        # 仕/士走斜线，限制在九宫格内
        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)
        
        # 检查是否走斜线一步
        if row_diff != 1 or col_diff != 1:
            return False
        
        # 检查是否在九宫格内
        is_red = self.board[start_row][start_col] == '仕'
        if is_red:
            if end_row < 7 or end_col < 3 or end_col > 5:  # 红仕限制在下方九宫格
                return False
        else:
            if end_row > 2 or end_col < 3 or end_col > 5:  # 黑士限制在上方九宫格
                return False
        
        return True

    def is_valid_general_move(self, start_row, start_col, end_row, end_col):
        # 帅/将走直线一步，限制在九宫格内
        row_diff = abs(end_row - start_row)
        col_diff = abs(end_col - start_col)
        
        # 检查是否走线一步
        if row_diff + col_diff != 1:
            return False
        
        # 查是否在九宫格内
        is_red = self.board[start_row][start_col] == '帅'
        if is_red:
            if end_row < 7 or end_col < 3 or end_col > 5:  # 红帅限制下方九宫格
                return False
        else:
            if end_row > 2 or end_col < 3 or end_col > 5:  # 黑将限制在上方九宫格
                return False
        
        return True

    def is_valid_cannon_move(self, start_row, start_col, end_row, end_col):
        # 炮的移动规则：直线移动，吃子时必须一个棋子
        if start_row != end_row and start_col != end_col:
            return False
        
        # 计算路径上的棋子数量
        pieces_in_path = 0
        if start_row == end_row:  # 横向移动
            min_col = min(start_col, end_col)
            max_col = max(start_col, end_col)
            for col in range(min_col + 1, max_col):
                if self.board[start_row][col]:
                    pieces_in_path += 1
        else:  # 纵向移动
            min_row = min(start_row, end_row)
            max_row = max(start_row, end_row)
            for row in range(min_row + 1, max_row):
                if self.board[row][start_col]:
                    pieces_in_path += 1
        
        # 判断移动否合法
        target = self.board[end_row][end_col]
        if target:  # 子时必须跳过一个棋子
            return pieces_in_path == 1
        else:  # 移动时不能有棋子阻挡
            return pieces_in_path == 0

    def is_valid_pawn_move(self, start_row, start_col, end_row, end_col):
        # 兵/卒只能向前走，过河后可以横走
        row_diff = end_row - start_row
        col_diff = abs(end_col - start_col)
        
        is_red = self.board[start_row][start_col] == '兵'
        
        # 检查动方向
        if is_red:
            if row_diff > 0:  # 红兵只能向上
                return False
        else:
            if row_diff < 0:  # 黑卒只能向下
                return False
        
        # 检查移动步数
        if abs(row_diff) + col_diff != 1:
            return False
        
        # 检查是否可以横走（过河后）
        if col_diff == 1:
            if is_red and start_row > 4:  # 红兵未过河
                return False
            if not is_red and start_row < 5:  # 黑卒未过河
                return False
        
        return True

    def check_game_over(self):
        # 检查将帅是否还棋盘上
        red_general_exists = False
        black_general_exists = False
        
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece == '帅':
                    red_general_exists = True
                elif piece == '将':
                    black_general_exists = True
                    
        # 判断胜负
        if not red_general_exists:
            self.game_over = True
            QMessageBox.information(self, '游戏结束', '黑方胜利！')
            return True
        elif not black_general_exists:
            self.game_over = True
            QMessageBox.information(self, '游戏结束', '红方胜利！')
            return True
        return False

    def undo_move(self):
        if not self.move_history or self.game_over:
            return
            
        # 获取上一步的移记录
        last_move = self.move_history.pop()
        start_pos, end_pos, captured_piece = last_move
        
        # 恢复棋子位置
        self.board[start_pos[0]][start_pos[1]] = self.board[end_pos[0]][end_pos[1]]
        self.board[end_pos[0]][end_pos[1]] = captured_piece
        
        # 切换回合
        self.is_red_turn = not self.is_red_turn
        
        # 更新棋盘显示
        self.update_board()

    def get_valid_moves(self, row, col):
        """获取指定置棋子的所有合法动位置"""
        valid_moves = []
        piece = self.board[row][col]
        if not piece:
            return valid_moves
        
        # 检查所有可能的位置
        for end_row in range(10):
            for end_col in range(9):
                if self.is_valid_move(row, col, end_row, end_col):
                    valid_moves.append((end_row, end_col))
                
        return valid_moves

    def highlight_valid_moves(self, moves):
        """高亮显示所有合法移动位置"""
        for row, col in moves:
            button = self.buttons[row][col]
            if self.board[row][col]:  # 如果目标位置有棋子
                button.setStyleSheet('''
                    QPushButton { 
                        color: %s;
                        background-color: rgba(255, 200, 200, 180); 
                        border: 2px solid #8B4513;
                        border-radius: %dpx;
                    }
                    QPushButton:hover { 
                        background-color: rgba(255, 200, 200, 180); 
                    }
                    QPushButton:pressed { 
                        background-color: rgba(255, 200, 200, 180); 
                    }
                ''' % (
                    'red' if self.board[row][col] in '车马相仕帅炮兵' else 'black',
                    button.width() // 2
                ))
            else:  # 如果目标位置为空
                button.setStyleSheet('''
                    QPushButton { 
                        background-color: rgba(144, 238, 144, 180);
                        border: 2px solid #8B4513;
                        border-radius: %dpx;
                    }
                    QPushButton:hover { 
                        background-color: rgba(144, 238, 144, 180);
                    }
                    QPushButton:pressed { 
                        background-color: rgba(144, 238, 144, 180);
                    }
                ''' % (button.width() // 2))

    def clear_highlights(self):
        """清除所有高亮显示"""
        for row in range(10):
            for col in range(9):
                piece = self.board[row][col]
                if piece in '车马相仕帅炮兵':
                    self.buttons[row][col].setStyleSheet('color: red;')
                elif piece in '車馬象士将砲卒':
                    self.buttons[row][col].setStyleSheet('color: black;')
                else:
                    self.buttons[row][col].setStyleSheet('')

    def on_click(self, row, col):
        if self.game_over:
            return
            
        current_piece = self.board[row][col]
        
        if self.selected_piece is None and current_piece:
            # 选择棋子
            is_red_piece = current_piece in '车马相仕帅炮兵'
            if (self.is_red_turn and is_red_piece) or (not self.is_red_turn and not is_red_piece):
                self.selected_piece = (row, col)
                # 高亮显示选中的棋子
                button = self.buttons[row][col]
                button.setStyleSheet('''
                    QPushButton { 
                        color: %s;
                        background-color: #FFE4B5; 
                        border: 2px solid #8B4513;
                        border-radius: %dpx;
                    }
                ''' % ('red' if is_red_piece else 'black', button.width() // 2))
                button.setText(current_piece)
                # 显示可移动位置
                valid_moves = self.get_valid_moves(row, col)
                self.highlight_valid_moves(valid_moves)
        
        elif self.selected_piece is not None:
            prev_row, prev_col = self.selected_piece
            
            if (row, col) == self.selected_piece:
                # 取消选择
                self.update_button_style(self.buttons[prev_row][prev_col], prev_row, prev_col)
                self.selected_piece = None
            
            elif self.is_valid_move(prev_row, prev_col, row, col):
                # 移动棋子
                captured_piece = self.board[row][col]
                self.move_history.append(((prev_row, prev_col), (row, col), captured_piece))
                
                self.board[row][col] = self.board[prev_row][prev_col]
                self.board[prev_row][prev_col] = ''
                self.selected_piece = None
                self.is_red_turn = not self.is_red_turn
                self.update_board()
                
                # 重置当前回合用时
                self.current_turn_time = 0
                
                if captured_piece in '帅将':
                    self.check_game_over()
            else:
                # 取消选择
                self.update_button_style(self.buttons[prev_row][prev_col], prev_row, prev_col)
                self.selected_piece = None

    def restart_game(self):
        reply = QMessageBox.question(self, '确重新开始', 
                                   '确定要重新开始游戏吗？',
                                   QMessageBox.Yes | QMessageBox.No,
                                   QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            # 重置游戏状态
            self.selected_piece = None
            self.is_red_turn = True
            self.game_over = False
            self.move_history.clear()
            
            # 重置计时器
            self.timer.stop()
            self.current_turn_time = 0
            self.timer.start()
            
            # 只更新当前回合时间显示
            self.turn_time_label.setText('00:00')
            
            # 清空棋盘
            self.board = [['' for _ in range(9)] for _ in range(10)]
            
            # 重新初始化棋盘
            self.init_board()
            self.update_board()
            
            # 清除所有按钮的背景色
            for row in range(10):
                for col in range(9):
                    self.update_button_style(self.buttons[row][col], row, col)

    def start_timer(self):
        """启动计时器"""
        self.timer.start(1000)  # 秒更新一次
        self.current_turn_time = 0

    def update_time(self):
        """更新时间显示"""
        if self.game_over:
            self.timer.stop()
            return
            
        self.current_turn_time += 1
        
        # 只更新当前回合时间
        self.turn_time_label.setText(self.format_turn_time(self.current_turn_time))

    def format_time(self, seconds):
        """格式化总时间显示"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f'{hours:02d}:{minutes:02d}:{seconds:02d}'

    def format_turn_time(self, seconds):
        """格式化回合时间显示"""
        minutes = seconds // 60
        seconds = seconds % 60
        return f'{minutes:02d}:{seconds:02d}'

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 重新计算棋盘和棋子大小
        self.update_layout()
    
    def update_layout(self):
        # 重新计算格子大小
        cell_size = min(self.width() // 9, self.height() // 10)
        margin_x = (self.width() - cell_size * 8) // 2
        margin_y = 25
        
        # 更新所有棋子按钮的大小和位置
        for row in range(10):
            for col in range(9):
                button = self.buttons[row][col]
                button_size = int(cell_size * 0.8)
                button.setFixedSize(button_size, button_size)
                button.setFont(QFont('SimSun', int(cell_size * 0.4)))
                
                x = int(margin_x + col * cell_size - (button_size // 2))
                y = int(margin_y + row * cell_size - (button_size // 2))
                button.move(x, y)
                
                # 更新按钮式
                self.update_button_style(button, row, col)

    def update_button_style(self, button, row, col):
        piece = self.board[row][col]
        button_size = button.width()
        
        if piece in '车马相仕帅炮兵':
            button.setStyleSheet('''
                QPushButton { 
                    color: red;
                    background-color: #F0E4D0; 
                    border: 2px solid #8B4513;
                    border-radius: %dpx;
                }
                QPushButton:hover { 
                    background-color: #F0E4D0; 
                }
                QPushButton:pressed { 
                    background-color: #F0E4D0; 
                }
            ''' % (button_size // 2))
            button.setText(piece)
        elif piece in '車馬象士将砲卒':
            button.setStyleSheet('''
                QPushButton { 
                    color: black;
                    background-color: #F0E4D0; 
                    border: 2px solid #8B4513;
                    border-radius: %dpx;
                }
                QPushButton:hover { 
                    background-color: #F0E4D0; 
                }
                QPushButton:pressed { 
                    background-color: #F0E4D0; 
                }
            ''' % (button_size // 2))
            button.setText(piece)
        else:  # 空位置完全透明且不显任何内容
            button.setStyleSheet('''
                QPushButton { 
                    background: transparent;
                    border: none;
                    color: transparent;
                    outline: none;
                }
                QPushButton:hover { 
                    background: transparent;
                    border: none;
                }
                QPushButton:pressed { 
                    background: transparent;
                    border: none;
                }
                QPushButton:focus { 
                    outline: none;
                    border: none;
                }
            ''')
            button.setText('')
            button.setFlat(True)  # 设置按钮为平面样式

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = ChessBoard()
    window.show()
    sys.exit(app.exec_()) 