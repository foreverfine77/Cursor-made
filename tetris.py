import pygame
import random
import os
import json
from colors import COLORS
from shapes import SHAPES
import win32gui
import win32con
import win32api

# 初始化游戏设置
BLOCK_SIZE = 20  # 方块大小
GRID_WIDTH = 10  # 游戏区域宽度
GRID_HEIGHT = 20  # 改回20，使游戏区域更高
INFO_WIDTH = 10  # 信息区域宽度（与游戏区域等宽）
SCREEN_WIDTH = BLOCK_SIZE * (GRID_WIDTH + INFO_WIDTH)  # 400像素
SCREEN_HEIGHT = SCREEN_WIDTH  # 400像素，保持窗口为正方形

class Button:
    def __init__(self, x, y, width, height, text, color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.is_hovered = False
        
        # 设置中文字体
        font_path = None
        possible_fonts = [
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/simsun.ttc",   # 宋体
            "C:/Windows/Fonts/msyh.ttc"      # 微软雅黑
        ]
        
        for path in possible_fonts:
            if os.path.exists(path):
                font_path = path
                break
        
        try:
            if font_path:
                self.font = pygame.font.Font(font_path, 14)  # 按钮字体改小到14
            else:
                self.font = pygame.font.Font(None, 14)
        except:
            self.font = pygame.font.Font(None, 14)
        
    def draw(self, screen):
        # 绘制按钮背景
        color = (80, 80, 80) if self.is_hovered else (60, 60, 60)
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, self.color, self.rect, 1)  # 边框宽度改为1
        
        # 绘制按钮文字
        text_surface = self.font.render(self.text, True, self.color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return True
        return False

class Tetris:
    def __init__(self):
        pygame.init()
        
        # 设置窗口样式为工具窗口
        os.environ['SDL_VIDEO_WINDOW_POS'] = '0,0'
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA | pygame.NOFRAME)
        pygame.display.set_caption('俄罗斯方块')
        
        # 初始化字体
        font_path = None
        possible_fonts = [
            "C:/Windows/Fonts/simhei.ttf",  # 黑体
            "C:/Windows/Fonts/simsun.ttc",   # 宋体
            "C:/Windows/Fonts/msyh.ttc"      # 微软雅黑
        ]
        
        for path in possible_fonts:
            if os.path.exists(path):
                font_path = path
                break
        
        try:
            if font_path:
                self.font = pygame.font.Font(font_path, 16)  # 普通文字大小
                self.large_font = pygame.font.Font(font_path, 28)  # 大文字大小
            else:
                self.font = pygame.font.Font(None, 16)
                self.large_font = pygame.font.Font(None, 28)
        except:
            self.font = pygame.font.Font(None, 16)
            self.large_font = pygame.font.Font(None, 28)
        
        # 获取窗口句柄
        self.hwnd = win32gui.GetForegroundWindow()
        
        # 设置窗口样式
        style = win32gui.GetWindowLong(self.hwnd, win32con.GWL_EXSTYLE)
        style = style | win32con.WS_EX_LAYERED | win32con.WS_EX_TOOLWINDOW
        win32gui.SetWindowLong(self.hwnd, win32con.GWL_EXSTYLE, style)
        
        # 设置窗口透明度
        win32gui.SetLayeredWindowAttributes(self.hwnd, 0, 180, win32con.LWA_ALPHA)
        
        # 设置窗口位置为底层
        win32gui.SetWindowPos(self.hwnd, win32con.HWND_BOTTOM, 0, 0, 0, 0,
                             win32con.SWP_NOMOVE | win32con.SWP_NOSIZE)
        
        self.clock = pygame.time.Clock()
        
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.next_piece = self.create_piece()
        self.current_piece = self.get_next_piece()
        self.game_over = False
        self.score = 0
        self.high_score = self.load_high_score()
        self.level = 1
        self.lines_cleared_total = 0
        self.combo = 0  # 连续消行次数
        self.paused = False
        
        # 调整按钮大小和位置
        button_width = 70
        button_height = 20
        button_margin = 2
        
        # 计算右侧区域的中心位置
        right_panel_width = SCREEN_WIDTH - (GRID_WIDTH * BLOCK_SIZE)
        right_panel_center = (GRID_WIDTH * BLOCK_SIZE) + (right_panel_width // 2)
        
        # 创建退出按钮（最上方）
        self.exit_button = Button(
            right_panel_center - (button_width // 2),
            SCREEN_HEIGHT - button_height * 4.5,  # 调整位置
            button_width,
            button_height,
            "退出游戏"
        )
        
        # 创建暂停按钮
        self.pause_button = Button(
            right_panel_center - (button_width // 2),
            SCREEN_HEIGHT - button_height * 3,  # 调整位置
            button_width,
            button_height,
            "暂停"
        )
        
        # 创建重新开始按钮
        self.restart_button = Button(
            right_panel_center - (button_width // 2),
            SCREEN_HEIGHT - button_height * 1.5,  # 调整位置
            button_width,
            button_height,
            "重新开始"
        )
    
    def load_high_score(self):
        """从文件加载最高分"""
        try:
            if os.path.exists('highscore.json'):
                with open('highscore.json', 'r') as f:
                    return json.load(f)['high_score']
        except:
            pass
        return 0
    
    def save_high_score(self):
        """保存最高分到文件"""
        with open('highscore.json', 'w') as f:
            json.dump({'high_score': self.high_score}, f)
    
    def update_score(self, lines_cleared):
        """更新分数、等级和连击"""
        if lines_cleared == 0:
            self.combo = 0  # 重置连击
            return
        
        # 基础分数
        base_points = {
            1: 100,   # 消除1行
            2: 300,   # 消除2行
            3: 500,   # 消除3行
            4: 800    # 消除4行
        }
        
        # 计算分数基础分 × 当前等级 × 连击加成）
        combo_bonus = 1 + (self.combo * 0.1)  # 每次连击增加10%分数
        points = base_points[lines_cleared] * self.level * combo_bonus
        self.score += int(points)
        
        # 更新连击数
        self.combo += 1
        
        # 更新总消行数和等级
        self.lines_cleared_total += lines_cleared
        self.level = (self.lines_cleared_total // 10) + 1  # 每10行升一级
        
        # 更新最高分
        if self.score > self.high_score:
            self.high_score = self.score
            self.save_high_score()
    
    def get_fall_speed(self):
        """根据等级返回下落速度（毫秒）"""
        return max(50, 500 - ((self.level - 1) * 40))  # 每升一级加快40毫秒，最快50毫秒
    
    def create_piece(self):
        """创建一个新的方块"""
        shape = random.choice(SHAPES)
        return {
            'shape': shape,
            'x': GRID_WIDTH // 2 - len(shape[0]) // 2,
            'y': 0,
            'color': random.randint(1, len(COLORS)-1)
        }
    
    def get_next_piece(self):
        """获取下一个方块，并创建新的下一个方块"""
        current = self.next_piece
        self.next_piece = self.create_piece()
        return current
    
    def valid_move(self, piece, x, y):
        for i, row in enumerate(piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    new_x = piece['x'] + j + x
                    new_y = piece['y'] + i + y
                    if (new_x < 0 or new_x >= GRID_WIDTH or 
                        new_y >= GRID_HEIGHT or 
                        (new_y >= 0 and self.grid[new_y][new_x])):
                        return False
        return True
    
    def run(self):
        last_time = pygame.time.get_ticks()
        dragging = False
        offset_x = offset_y = 0
        
        while True:
            current_time = pygame.time.get_ticks()
            delta_time = current_time - last_time
            fall_speed = self.get_fall_speed()
            
            # 获取鼠标位置和按键状态
            mouse_pos = pygame.mouse.get_pos()
            mouse_buttons = pygame.mouse.get_pressed()
            
            # 处理拖动
            if mouse_buttons[0]:  # 左键按下
                if not dragging:
                    # 开始拖动
                    dragging = True
                    mouse_x, mouse_y = win32gui.GetCursorPos()
                    window_x, window_y, _, _ = win32gui.GetWindowRect(self.hwnd)
                    offset_x = window_x - mouse_x
                    offset_y = window_y - mouse_y
                    # 拖动时临时提升到顶层
                    win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST,
                                        window_x, window_y, 0, 0,
                                        win32con.SWP_NOSIZE)
                else:
                    # 继续拖动
                    mouse_x, mouse_y = win32gui.GetCursorPos()
                    new_x = mouse_x + offset_x
                    new_y = mouse_y + offset_y
                    win32gui.SetWindowPos(self.hwnd, win32con.HWND_TOPMOST,
                                        new_x, new_y, 0, 0,
                                        win32con.SWP_NOSIZE)
            else:
                # 释放拖动
                if dragging:
                    dragging = False
                    window_x, window_y, _, _ = win32gui.GetWindowRect(self.hwnd)
                    win32gui.SetWindowPos(self.hwnd, win32con.HWND_BOTTOM,
                                        window_x, window_y, 0, 0,
                                        win32con.SWP_NOSIZE)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return
                
                # 处理按钮事件（只在非拖动状态下）
                if not dragging:
                    # 退出按钮
                    if self.exit_button.handle_event(event):
                        pygame.quit()
                        return
                    
                    # 暂停按钮
                    if self.pause_button.handle_event(event):
                        self.paused = not self.paused
                        if self.paused:
                            pause_time = pygame.time.get_ticks()
                        else:
                            last_time = pygame.time.get_ticks() - delta_time
                    
                    # 重新开始按钮
                    if self.restart_button.handle_event(event):
                        self.reset_game()
                        last_time = pygame.time.get_ticks()
                        continue
                
                # 键盘事件处理
                if event.type == pygame.KEYDOWN and not self.paused and not self.game_over:
                    if event.key == pygame.K_LEFT:
                        if self.valid_move(self.current_piece, -1, 0):
                            self.current_piece['x'] -= 1
                    elif event.key == pygame.K_RIGHT:
                        if self.valid_move(self.current_piece, 1, 0):
                            self.current_piece['x'] += 1
                    elif event.key == pygame.K_DOWN:
                        if self.valid_move(self.current_piece, 0, 1):
                            self.current_piece['y'] += 1
                    elif event.key == pygame.K_UP:
                        self.rotate_piece()
            
            # 游戏逻辑更新
            if not self.paused and not self.game_over:
                if delta_time >= fall_speed:
                    if self.valid_move(self.current_piece, 0, 1):
                        self.current_piece['y'] += 1
                    else:
                        self.lock_piece()
                    last_time = current_time
            
            # 更新显示
            self.draw()
            pygame.display.flip()
            self.clock.tick(60)
    
    def draw(self):
        # 清空屏幕为完全透明
        self.screen.fill((0,0,0,0))
        
        # 创建毛玻璃效果背景（移除圆角）
        glass_effect = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        glass_effect.fill((255, 255, 255, 15))  # 填充半透明白色
        
        # 添加网格线增强毛玻璃效果
        grid_size = 4
        for x in range(0, SCREEN_WIDTH, grid_size):
            pygame.draw.line(glass_effect, (255, 255, 255, 5), (x, 0), (x, SCREEN_HEIGHT))
        for y in range(0, SCREEN_HEIGHT, grid_size):
            pygame.draw.line(glass_effect, (255, 255, 255, 5), (0, y), (SCREEN_WIDTH, y))
        
        self.screen.blit(glass_effect, (0, 0))
        
        # 移除垂直偏移，使游戏区域占满左边
        game_area_height = SCREEN_HEIGHT  # 游戏区域高度等于屏幕高度
        y_offset = 0  # 不再需要偏移
        
        # 绘制游戏区域边框
        border_color = (255, 255, 255, 30)
        pygame.draw.rect(self.screen, border_color, 
                        (0, y_offset, GRID_WIDTH * BLOCK_SIZE, game_area_height), 1)
        
        # 绘制已固定的方块
        visible_start = max(0, GRID_HEIGHT - SCREEN_HEIGHT // BLOCK_SIZE)
        for y, row in enumerate(self.grid[visible_start:]):
            for x, cell in enumerate(row):
                if cell:
                    color = list(COLORS[cell])
                    if len(color) == 3:
                        color.append(180)
                    pygame.draw.rect(self.screen, color,
                                   (x * BLOCK_SIZE, y * BLOCK_SIZE + y_offset,
                                    BLOCK_SIZE-1, BLOCK_SIZE-1))
        
        # 绘制当前方块
        if not self.game_over:
            for i, row in enumerate(self.current_piece['shape']):
                for j, cell in enumerate(row):
                    if cell:
                        x = (self.current_piece['x'] + j) * BLOCK_SIZE
                        y = (self.current_piece['y'] + i) * BLOCK_SIZE + y_offset
                        color = list(COLORS[self.current_piece['color']])
                        if len(color) == 3:
                            color.append(180)
                        pygame.draw.rect(self.screen, color,
                                       (x, y, BLOCK_SIZE-1, BLOCK_SIZE-1))
        
        # 计算右侧面板的宽度和中心位置
        info_panel_width = SCREEN_WIDTH - (GRID_WIDTH * BLOCK_SIZE)
        info_center_x = GRID_WIDTH * BLOCK_SIZE + (info_panel_width // 2)
        
        # 绘制游戏信息（居中对齐）
        texts = [
            ("分数", str(self.score)),
            ("最高分", str(self.high_score)),
            ("等级", str(self.level)),
            ("消除行数", str(self.lines_cleared_total))
        ]
        
        if self.combo > 1:
            texts.append(("连击", str(self.combo)))
        
        # 调整文本间距
        line_spacing = 20
        current_y = BLOCK_SIZE
        
        # 绘制游戏信息（居中）
        for i, (label, value) in enumerate(texts):
            text = f"{label}: {value}"
            text_surface = self.font.render(text, True, (255, 255, 255, 200))
            text_rect = text_surface.get_rect(centerx=info_center_x)
            text_rect.y = current_y + (i * line_spacing)
            self.screen.blit(text_surface, text_rect)
        
        # 更新当前Y位置
        current_y += len(texts) * line_spacing + 20
        
        # 绘制下一个方块预览（居中）
        next_text = self.font.render("下一个:", True, (255, 255, 255, 200))
        next_rect = next_text.get_rect(centerx=info_center_x)
        next_rect.y = current_y
        self.screen.blit(next_text, next_rect)
        
        # 调整预览方块位置（居中）
        preview_y = current_y + 25
        shape_width = len(self.next_piece['shape'][0]) * BLOCK_SIZE
        preview_x = info_center_x - (shape_width // 2)
        
        # 绘制预览方块
        for i, row in enumerate(self.next_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    x = preview_x + j * BLOCK_SIZE
                    y = preview_y + i * BLOCK_SIZE
                    color = list(COLORS[self.next_piece['color']])
                    if len(color) == 3:
                        color.append(180)
                    pygame.draw.rect(self.screen, color,
                                   (x, y, BLOCK_SIZE-1, BLOCK_SIZE-1))
        
        # 更新当前Y位置（为操作提示留出空间）
        current_y = preview_y + 60
        
        # 添加按键提示（使用更小的字体）
        try:
            # 尝试使用与主字体相同的字体文件
            font_path = None
            possible_fonts = [
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "C:/Windows/Fonts/simsun.ttc",   # 宋体
                "C:/Windows/Fonts/msyh.ttc"      # 微软雅黑
            ]
            
            for path in possible_fonts:
                if os.path.exists(path):
                    font_path = path
                    break
            
            if font_path:
                small_font = pygame.font.Font(font_path, 14)  # 创建更小的字体
            else:
                small_font = pygame.font.Font(None, 14)
        except:
            small_font = pygame.font.Font(None, 14)
        
        # 绘制操作提示（居中）
        controls_text = small_font.render("操作提示:", True, (255, 255, 255, 200))
        controls_rect = controls_text.get_rect(centerx=info_center_x)
        controls_rect.y = current_y
        self.screen.blit(controls_text, controls_rect)
        
        # 操作提示内容（居中）
        control_texts = [
            "↑ - 顺时旋转",
            "↓ - 加速下落",
            "← - 向左移动",
            "→ - 向右移动"
        ]
        
        # 减小操作提示的行间距
        for i, text in enumerate(control_texts):
            control_surface = small_font.render(text, True, (255, 255, 255, 200))
            control_rect = control_surface.get_rect(centerx=info_center_x)
            control_rect.y = current_y + 20 + (i * 15)
            self.screen.blit(control_surface, control_rect)
        
        # 游戏结束和暂停状态的文字
        if self.game_over:
            # 调整半透明背景的颜色
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(160)  # 增加透明度使效果更明显
            s.fill((20, 20, 20))  # 使用更深的灰色
            self.screen.blit(s, (0, 0))
            
            game_over_text = self.large_font.render("游戏结束!", True, (255, 255, 255))
            restart_text = self.font.render("点击重新开始再次挑战", True, (255, 255, 255))
            
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            
            self.screen.blit(game_over_text, text_rect)
            self.screen.blit(restart_text, restart_rect)
        
        if self.paused:
            # 添加半透明背景
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            s.set_alpha(128)
            s.fill((0, 0, 0))
            self.screen.blit(s, (0, 0))
            
            pause_text = self.large_font.render("已暂停", True, (255, 255, 255))
            continue_text = self.font.render("再次点击按钮继续游戏", True, (255, 255, 255))
            
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 30))
            continue_rect = continue_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
            
            self.screen.blit(pause_text, text_rect)
            self.screen.blit(continue_text, continue_rect)
        
        # 绘制所有按钮
        self.exit_button.draw(self.screen)
        self.pause_button.draw(self.screen)
        self.restart_button.draw(self.screen)
    
    def lock_piece(self):
        """当方块落地时，将其锁定到网格中并获取下一个方块"""
        # 检查是否触顶
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    if self.current_piece['y'] + i < 0:
                        self.game_over = True
                        return
                    self.grid[self.current_piece['y'] + i][self.current_piece['x'] + j] = self.current_piece['color']
        
        # 检查并清除完整的行
        lines_cleared = self.clear_lines()
        self.update_score(lines_cleared)
        
        # 创建新方块，检查是否有足够空间放置
        self.current_piece = self.get_next_piece()
        
        # 检查新方块的初始位置是否有效
        for i, row in enumerate(self.current_piece['shape']):
            for j, cell in enumerate(row):
                if cell:
                    # 如果新方块的初始位置已经被占用，说明游戏结束
                    if self.grid[self.current_piece['y'] + i][self.current_piece['x'] + j]:
                        self.game_over = True
                        return
    
    def clear_lines(self):
        """清除完整的行并返回清除的行数"""
        lines_cleared = 0
        y = GRID_HEIGHT - 1
        while y >= 0:
            if all(self.grid[y]):
                lines_cleared += 1
                # 将上面的所有行向下移动
                for y2 in range(y, 0, -1):
                    self.grid[y2] = self.grid[y2-1][:]
                # 添加新的空行
                self.grid[0] = [0] * GRID_WIDTH
            else:
                y -= 1
        return lines_cleared
    
    def reset_game(self):
        """重置游戏状态"""
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.next_piece = self.create_piece()
        self.current_piece = self.get_next_piece()
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared_total = 0
        self.combo = 0
        self.paused = False
    
    def rotate_piece(self):
        """旋转当前方块"""
        # 获取当前方块的形状
        shape = self.current_piece['shape']
        # 计算旋转后的新形状（90度顺时针旋转）
        new_shape = [[shape[y][x] for y in range(len(shape)-1, -1, -1)]
                     for x in range(len(shape[0]))]
        
        # 暂存当前形状
        old_shape = self.current_piece['shape']
        # 尝试旋转
        self.current_piece['shape'] = new_shape
        
        # 如果旋转后的位置无效，则恢复原来的形状
        if not self.valid_move(self.current_piece, 0, 0):
            self.current_piece['shape'] = old_shape

if __name__ == '__main__':
    game = Tetris()
    game.run() 