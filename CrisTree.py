import pygame
import math
import random

# --- 初始化设置 ---
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Python 3D 粒子光影圣诞树 (Ultimate Ver.)")
clock = pygame.time.Clock()

# 颜色定义 (R, G, B)
BLACK = (0, 0, 5)        # 极深的午夜蓝背景
GOLD = (255, 223, 0)     # 金色光芒
WHITE = (255, 255, 255)  # 雪花
GREEN_LEAF = (34, 139, 34) # 树叶基础色
RED_LIGHT = (255, 50, 50)  # 红灯装饰
CYAN_LIGHT = (50, 255, 255) # 青光

# --- 核心类：3D 点 ---
class Point3D:
    def __init__(self, x, y, z, color, size, type="leaf"):
        self.x = x
        self.y = y
        self.z = z
        self.base_x = x
        self.base_z = z
        self.color = color
        self.size = size
        self.type = type # 'leaf', 'star', 'snow', 'light'
        self.blink_offset = random.random() * 100

    def project(self, angle, fov=300, viewer_distance=400):
        """ 将 3D 坐标投影到 2D 屏幕 """
        # 1. 绕 Y 轴旋转
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        
        # 旋转后的坐标
        rot_x = self.base_x * cos_a - self.base_z * sin_a
        rot_z = self.base_x * sin_a + self.base_z * cos_a + self.z # +self.z 是为了保留一些上下起伏的动态(如果是雪花)
        
        # 对于非雪花物体，z 坐标通常是静态的
        if self.type != "snow":
            rot_z = self.base_x * sin_a + self.base_z * cos_a

        # 2. 透视投影
        scale = fov / (viewer_distance + rot_z)
        x_2d = rot_x * scale + WIDTH / 2
        y_2d = self.y * scale + HEIGHT / 2 - 50 # -50 是为了把树往下移一点
        
        return int(x_2d), int(y_2d), scale, rot_z

# --- 生成圣诞树粒子 ---
particles = []

# 1. 生成树体 (圆锥螺旋结构)
layers = 80 # 层数
for i in range(layers):
    y = -200 + i * 5 # 从上往下
    radius = i * 2.5 # 半径逐渐变大
    
    # 每层生成的粒子数
    count = int(radius * 1.5) + 5
    for j in range(count):
        angle = (j / count) * math.pi * 2 + (i * 0.5) # 螺旋错位
        r_random = radius * random.uniform(0.8, 1.2) # 让树有点毛茸茸的感觉
        
        px = math.cos(angle) * r_random
        pz = math.sin(angle) * r_random
        
        # 颜色随机变化，增加质感
        c_var = random.randint(0, 50)
        color = (34, 139 + c_var, 34)
        
        # 偶尔生成彩灯装饰 (10% 概率)
        p_type = "leaf"
        size = 2
        if random.random() < 0.08:
            p_type = "light"
            size = 4
            color = random.choice([RED_LIGHT, GOLD, CYAN_LIGHT])
        
        particles.append(Point3D(px, y, pz, color, size, p_type))

# 2. 生成顶部星星
# 星星由多个高亮粒子组成一个球体/星体
for _ in range(50):
    particles.append(Point3D(random.uniform(-10, 10), -220 + random.uniform(-10, 10), random.uniform(-10, 10), GOLD, 3, "star"))

# --- 生成雪花 ---
snowflakes = []
for _ in range(200):
    x = random.randint(-400, 400)
    y = random.randint(-400, 400)
    z = random.randint(-200, 200)
    snowflakes.append(Point3D(x, y, z, WHITE, random.randint(1, 3), "snow"))


# --- 绘制辅助函数：发光效果 ---
def draw_glowing_circle(surface, color, center, radius, alpha_base=100):
    """ 绘制带有光晕的圆点 """
    # 核心亮部
    pygame.draw.circle(surface, color, center, radius)
    
    # 外部光晕 (利用带 Alpha 通道的 Surface)
    glow_surf = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
    
    # 光晕颜色 (原色 + 透明度)
    r, g, b = color
    # 绘制三层光晕
    pygame.draw.circle(glow_surf, (r, g, b, alpha_base // 2), (radius * 3, radius * 3), radius * 3)
    pygame.draw.circle(glow_surf, (r, g, b, alpha_base), (radius * 3, radius * 3), radius * 1.5)
    
    # 使用混合模式 BLEND_ADD (颜色减淡/叠加)，模拟发光
    surface.blit(glow_surf, (center[0] - radius * 3, center[1] - radius * 3), special_flags=pygame.BLEND_ADD)

# --- 主循环 ---
angle = 0
running = True

font = pygame.font.SysFont("Arial", 40, bold=True)

while running:
    clock.tick(60) # 锁定 60 帧
    screen.fill(BLACK) # 清屏
    
    # 处理退出
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    angle += 0.01 # 旋转速度

    # 对所有粒子进行排序：Z轴深度的粒子先画（画家算法），防止透视错误
    # 我们需要先计算这一帧所有粒子的投影深度
    to_draw = []
    
    # 1. 处理树和灯
    for p in particles:
        x, y, scale, z_depth = p.project(angle)
        to_draw.append((z_depth, p, x, y, scale))
        
    # 2. 处理雪花 (让雪花下落)
    for s in snowflakes:
        s.y += 1.5 # 下落速度
        if s.y > 300: # 到底重置
            s.y = -300
            s.x = random.randint(-400, 400)
            s.base_x = s.x # 更新 base 以便旋转计算正确
            
        x, y, scale, z_depth = s.project(angle) # 雪花也参与旋转，更有空间感
        to_draw.append((z_depth, s, x, y, scale))

    # 3. 排序 (Z 越大越远，越小越近。我们从远到近画)
    to_draw.sort(key=lambda item: item[0], reverse=True)

    # 4. 绘制
    for z_depth, p, x, y, scale in to_draw:
        size = max(1, int(p.size * scale))
        
        if p.type == "leaf":
            # 树叶稍微暗一点，做背景
            col = tuple(max(0, min(255, int(c * (scale * 0.8)))) for c in p.color) # 简单的深度雾效
            pygame.draw.circle(screen, col, (x, y), size)
            
        elif p.type == "light":
            # 彩灯闪烁
            blink = math.sin(pygame.time.get_ticks() * 0.005 + p.blink_offset)
            if blink > 0:
                # 高亮绘制
                draw_glowing_circle(screen, p.color, (x, y), size, alpha_base=50)
            else:
                pygame.draw.circle(screen, (50, 50, 50), (x, y), size) # 灭灯状态
        
        elif p.type == "star":
            # 星星始终高亮，并且稍微大一点
            draw_glowing_circle(screen, GOLD, (x, y), size + 2, alpha_base=80)
            
        elif p.type == "snow":
            pygame.draw.circle(screen, WHITE, (x, y), size)

    # 绘制底部文字光影
    text_surf = font.render("Merry Christmas", True, (255, 50, 50))
    glow_text = font.render("Merry Christmas", True, (100, 0, 0))
    # 简单的文字阴影/发光位移
    screen.blit(glow_text, (WIDTH//2 - text_surf.get_width()//2 + 2, 522))
    screen.blit(text_surf, (WIDTH//2 - text_surf.get_width()//2, 520))

    pygame.display.flip()

pygame.quit()