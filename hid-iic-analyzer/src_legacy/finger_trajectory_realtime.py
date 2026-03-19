import pygame
import sys
from parser import parse_data_file
from renderer import render_trajectory

# 初始化Pygame
pygame.init()

# 设置窗口参数
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Finger Trajectory Analyzer")

# 设置时钟
clock = pygame.time.Clock()

# 主程序
def main(data_file):
    # 解析数据文件
    frames = parse_data_file(data_file)
    current_frame = 0
    playback_speed = 130  # 默认播放速度

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE or event.key == pygame.K_RIGHT:
                    current_frame = min(current_frame + 1, len(frames) - 1)
                elif event.key == pygame.K_LEFT:
                    current_frame = max(current_frame - 1, 0)
                elif event.key == pygame.K_r:
                    current_frame = 0
                elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                    playback_speed = min(playback_speed + 10, 500)
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    playback_speed = max(playback_speed - 10, 10)
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

        # 清屏
        screen.fill((255, 255, 255))

        # 渲染当前帧的轨迹
        render_trajectory(screen, frames[current_frame])

        # 更新显示
        pygame.display.flip()

        # 控制帧率
        clock.tick(playback_speed)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 finger_trajectory_realtime.py <data_file.txt>")
        sys.exit(1)

    main(sys.argv[1])
