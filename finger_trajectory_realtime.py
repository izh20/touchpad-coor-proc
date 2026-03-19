#!/usr/bin/env python3
"""
手指包数据轨迹可视化工具 - Pygame实时渲染版本
以130Hz速度渲染手指轨迹
"""

import pygame
import sys
from collections import defaultdict
from trajectory.parser import FingerDataParser, FingerPoint
import argparse

# 坐标包配置
PACKET_SIZE = 47           # 每包47字节
FINGER_REPORT_ID = 0x2F    # 手指包起始标识

FINGER_SLOTS = [3, 11, 19, 27, 35]

# 屏幕配置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 900
FPS = 130  # 130Hz渲染


# Parser moved to trajectory.parser; import FingerDataParser, FingerPoint above


class TrajectoryRenderer:
    """轨迹渲染器"""

    # 颜色定义
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    GRAY = (128, 128, 128)
    BG_COLOR = (30, 30, 40)

    # 手指颜色 (10个手指)
    FINGER_COLORS = [
        (255, 0, 0),      # 红
        (0, 0, 255),      # 蓝
        (0, 255, 0),      # 绿
        (255, 165, 0),    # 橙
        (128, 0, 128),     # 紫
        (165, 42, 42),    # 棕
        (255, 192, 203),  # 粉
        (128, 128, 128),  # 灰
        (128, 128, 0),    # 橄榄
        (0, 255, 255),    # 青
    ]

    # 状态颜色
    STATUS_COLORS = {
        3: (255, 0, 0),    # PRESS - 红色
        1: (0, 255, 0),    # RELEASE - 绿色
        2: (0, 0, 255),    # HOVER - 蓝色
        0: (128, 128, 128), # UNKNOWN - 灰色
    }

    def __init__(self, trajectories):
        pygame.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fps = FPS
        pygame.display.set_caption(f'Finger Trajectory Viewer - {self.fps}Hz')
        self.clock = pygame.time.Clock()

        self.trajectories = trajectories
        self.current_frame = 0
        self.max_frames = max(len(pts) for pts in trajectories.values()) if trajectories else 0

        # 跟踪已释放的手指，在渲染时清除其轨迹
        self.visible_start_indices = {}
        self.visible_end_indices = {}

        # 播放控制：播放/暂停
        self.playing = True

        # 坐标范围 (用于缩放)
        all_points = []
        for pts in trajectories.values():
            all_points.extend(pts)

        if all_points:
            self.x_min = min(p.x for p in all_points)
            self.x_max = max(p.x for p in all_points)
            self.y_min = min(p.y for p in all_points)
            self.y_max = max(p.y for p in all_points)
        else:
            self.x_min, self.x_max = 0, 4000
            self.y_min, self.y_max = 0, 2000

        # 添加边距
        x_margin = (self.x_max - self.x_min) * 0.1
        y_margin = (self.y_max - self.y_min) * 0.1
        self.x_min -= x_margin
        self.x_max += x_margin
        self.y_min -= y_margin
        self.y_max += y_margin

        # 字体
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

        # 控制说明
        self.show_controls = True
        

    def coord_to_screen(self, x, y):
        """将数据坐标转换为屏幕坐标"""
        screen_x = int((x - self.x_min) / (self.x_max - self.x_min) * (SCREEN_WIDTH - 100)) + 50
        screen_y = int((self.y_max - y) / (self.y_max - self.y_min) * (SCREEN_HEIGHT - 150)) + 50
        return screen_x, screen_y

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_SPACE:
                    # 空格键切换播放/暂停
                    self.playing = not self.playing
                    # 更新标题以反映暂停状态
                    state = 'Paused' if not self.playing else f'{self.fps}Hz'
                    pygame.display.set_caption(f'Finger Trajectory Viewer - {state}')
                elif event.key == pygame.K_RIGHT:
                    # 逐帧前进（按键触发）
                    if self.current_frame < self.max_frames - 1:
                        self.current_frame += 1
                    else:
                        self.current_frame = 0
                elif event.key == pygame.K_r:
                    # R键重置
                    self.current_frame = 0
                    self.visible_start_indices = {}
                    self.visible_end_indices = {}
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    # 加速
                    self.fps = min(self.fps + 10, 500)
                    pygame.display.set_caption(f'Finger Trajectory Viewer - {self.fps}Hz')
                    self.clock = pygame.time.Clock()
                elif event.key == pygame.K_MINUS:
                    # 减速
                    self.fps = max(self.fps - 10, 10)
                    pygame.display.set_caption(f'Finger Trajectory Viewer - {self.fps}Hz')
                    self.clock = pygame.time.Clock()
        return True

    def update(self):
        """更新状态"""
        # 自动播放（仅在播放状态时推进帧）
        if self.playing:
            if self.current_frame < self.max_frames - 1:
                self.current_frame += 1
            else:
                self.current_frame = 0

        # 检查当前帧的手指释放
        self.check_releases()

    def check_releases(self):
        """检查当前帧的手指可见性"""
        self.visible_start_indices = {}
        self.visible_end_indices = {}

        for finger_id, points in self.trajectories.items():
            if not points:
                self.visible_start_indices[finger_id] = 0
                self.visible_end_indices[finger_id] = 0
                continue

            # 计算在当前帧范围内的 end_idx（当前帧之前的所有点）
            end_idx = min(self.current_frame + 1, len(points))

            # 在 [0, end_idx-1] 范围内向后找最后一个 release
            last_release_idx = -1
            for i in range(end_idx - 1, -1, -1):
                if points[i].status in (0, 1):
                    last_release_idx = i
                    break

            # 起始索引为最后一次 release 之后的第一个 touch
            start_idx = 0
            if last_release_idx >= 0:
                found = False
                for i in range(last_release_idx + 1, end_idx):
                    if points[i].status in (2, 3):
                        start_idx = i
                        found = True
                        break
                if not found:
                    # release 之后到当前帧没有新的 touch，则无可见点
                    start_idx = end_idx

            # 设置可见范围
            if end_idx <= start_idx:
                self.visible_start_indices[finger_id] = 0
                self.visible_end_indices[finger_id] = 0
            else:
                self.visible_start_indices[finger_id] = start_idx
                self.visible_end_indices[finger_id] = end_idx

    def draw(self):
        """绘制画面"""
        self.screen.fill(self.BG_COLOR)

        # 左上角：当前帧 / 总帧数
        total_frames = max(1, self.max_frames)
        frame_text = self.font.render(f'Frame {self.current_frame}/{total_frames}', True, self.WHITE)
        self.screen.blit(frame_text, (10, 10))

        # 绘制坐标轴
        pygame.draw.line(self.screen, self.GRAY, (50, SCREEN_HEIGHT - 50), (SCREEN_WIDTH - 50, SCREEN_HEIGHT - 50), 2)  # X轴
        pygame.draw.line(self.screen, self.GRAY, (50, SCREEN_HEIGHT - 50), (50, 50), 2)  # Y轴

        # 绘制坐标标签
        x_label = self.font.render(f'X: {self.x_min:.0f} - {self.x_max:.0f}', True, self.GRAY)
        y_label = self.font.render(f'Y: {self.y_min:.0f} - {self.y_max:.0f}', True, self.GRAY)
        self.screen.blit(x_label, (SCREEN_WIDTH - 150, SCREEN_HEIGHT - 30))
        self.screen.blit(y_label, (60, 20))

        # 绘制每个手指的轨迹
        for finger_id, points in self.trajectories.items():
            if not points:
                continue

            # 获取该手指在当前帧的可见范围
            start_idx = self.visible_start_indices.get(finger_id, 0)
            end_idx = self.visible_end_indices.get(finger_id, len(points))

            # 获取可见点
            if start_idx >= len(points) or end_idx <= start_idx:
                continue

            visible_points = points[start_idx:end_idx]
            if not visible_points:
                continue

            if len(visible_points) < 1:
                continue

            color = self.FINGER_COLORS[finger_id % len(self.FINGER_COLORS)]

            # 判断是大面积还是手指 - 根据状态判断
            # 状态3=手指touch, 状态2=大面积touch
            # 状态1=手指release, 状态0=大面积release
            current_status = visible_points[-1].status
            is_large_area = current_status in (0, 2)  # 大面积touch或release

            if is_large_area:
                # 大面积：粗线 + 填充轨迹区域
                if len(visible_points) > 1:
                    # 绘制粗轨迹线（6px）
                    for i in range(len(visible_points) - 1):
                        p1 = visible_points[i]
                        p2 = visible_points[i + 1]
                        x1, y1 = self.coord_to_screen(p1.x, p1.y)
                        x2, y2 = self.coord_to_screen(p2.x, p2.y)
                        pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 6)

                    # 填充轨迹区域（半透明）
                    if len(visible_points) > 2:
                        trail_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                        trail_points = [self.coord_to_screen(p.x, p.y) for p in visible_points]
                        pygame.draw.lines(trail_surface, (*color, 80), False, trail_points, 6)
                        self.screen.blit(trail_surface, (0, 0))

                # 大面积当前点：大实心圆
                current = visible_points[-1]
                x, y = self.coord_to_screen(current.x, current.y)
                pygame.draw.circle(self.screen, color, (x, y), 15)

                # 大面积标签
                label = self.font.render(f'AREA{finger_id}', True, color)
                self.screen.blit(label, (x + 18, y - 18))

            else:
                # 手指：细线 + 小空心点
                if len(visible_points) > 1:
                    for i in range(len(visible_points) - 1):
                        p1 = visible_points[i]
                        p2 = visible_points[i + 1]
                        x1, y1 = self.coord_to_screen(p1.x, p1.y)
                        x2, y2 = self.coord_to_screen(p2.x, p2.y)
                        pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), 2)

                # 手指当前点
                current = visible_points[-1]
                x, y = self.coord_to_screen(current.x, current.y)
                status_color = self.STATUS_COLORS.get(current.status, self.GRAY)
                # 小空心圆 (8px，线宽2)
                pygame.draw.circle(self.screen, status_color, (x, y), 8, 2)

                # 手指ID标签
                label = self.font.render(f'F{finger_id}', True, color)
                self.screen.blit(label, (x + 10, y - 10))

            pass

        # 右上角：轨迹图例，避免遮挡主体区域
        legend_x = SCREEN_WIDTH - 300
        legend_y = 60
        for finger_id in sorted(self.trajectories.keys()):
            color = self.FINGER_COLORS[finger_id % len(self.FINGER_COLORS)]
            count = len(self.trajectories[finger_id])
            statuses = [p.status for p in self.trajectories[finger_id]]
            has_large = 2 in statuses or 0 in statuses
            label = f'AREA{finger_id}' if has_large else f'Finger {finger_id}'
            text = self.font.render(f'{label}: {count} pts', True, color)
            self.screen.blit(text, (legend_x, legend_y))
            legend_y += 25

        # 右下角：状态说明
        status_x = SCREEN_WIDTH - 300
        status_y = SCREEN_HEIGHT - 140
        status_legend = [
            (3, 'Finger Touch', (255, 0, 0)),
            (2, 'Large Touch', (0, 0, 255)),
            (1, 'Finger Release', (0, 255, 0)),
            (0, 'Large Release', (128, 128, 128)),
        ]
        for status, sname, color in status_legend:
            text = self.font.render(sname, True, color)
            pygame.draw.circle(self.screen, color, (status_x, status_y + 8), 6)
            self.screen.blit(text, (status_x + 20, status_y))
            status_y += 25

        # 左下角：坐标范围和控制说明
        if self.show_controls:
            controls = [
                f'X: {self.x_min:.0f} - {self.x_max:.0f}',
                f'Y: {self.y_min:.0f} - {self.y_max:.0f}',
                '',
                'SPACE: Play/Pause',
                'RIGHT: Next Frame',
                'LEFT: Previous Frame',
                'R: Reset',
                '+/-: Speed',
                'ESC: Quit'
            ]
            cy = SCREEN_HEIGHT - 170
            for ctrl in controls:
                text = self.font.render(ctrl, True, self.GRAY)
                self.screen.blit(text, (10, cy))
                cy += 20

        # FPS（稍下方，避免与帧计数重合）
        fps_text = self.font.render(f'FPS: {self.fps}', True, self.WHITE)
        self.screen.blit(fps_text, (10, 40))

        pygame.display.flip()

    def run(self):
        """运行主循环"""
        running = True
        while running:
            running = self.handle_events()
            if not running:
                break

            self.update()
            self.draw()
            self.clock.tick(self.fps)

        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description='Finger Trajectory Realtime Viewer (Pygame)')
    parser.add_argument('input_file', help='Input CSV file path')
    args = parser.parse_args()

    print(f"Parsing file: {args.input_file}")

    parser_obj = FingerDataParser()
    trajectories, total_packets = parser_obj.process_csv_data(args.input_file)

    print(f"Total packets: {total_packets}")
    print(f"Trajectories found:")
    for fid, pts in sorted(trajectories.items()):
        print(f"  Finger {fid}: {len(pts)} points")

    if not trajectories:
        print("No trajectory data found!")
        return

    print("\nStarting 130Hz trajectory viewer...")
    print("Controls:")
    print("  SPACE/RIGHT: Next frame")
    print("  LEFT: Previous frame")
    print("  R: Reset")
    print("  +/-: Adjust speed")
    print("  ESC: Quit")

    renderer = TrajectoryRenderer(trajectories)
    renderer.run()


if __name__ == '__main__':
    main()
