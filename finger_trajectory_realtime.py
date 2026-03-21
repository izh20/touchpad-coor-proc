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

    def __init__(self, trajectories, xmin=None, xmax=None, ymin=None, ymax=None, packet_scantimes=None):
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
        # 支持外部指定分辨率/边界（xmin/xmax/ymin/ymax），若未指定则自动计算
        self.x_min = xmin
        self.x_max = xmax
        self.y_min = ymin
        self.y_max = ymax

        if None in (self.x_min, self.x_max, self.y_min, self.y_max):
            all_points = []
            for pts in trajectories.values():
                all_points.extend(pts)

            if all_points:
                auto_x_min = min(p.x for p in all_points)
                auto_x_max = max(p.x for p in all_points)
                auto_y_min = min(p.y for p in all_points)
                auto_y_max = max(p.y for p in all_points)
            else:
                auto_x_min, auto_x_max = 0, 4000
                auto_y_min, auto_y_max = 0, 2000

            # 对于未传入的项使用自动计算值
            if self.x_min is None:
                self.x_min = auto_x_min
            if self.x_max is None:
                self.x_max = auto_x_max
            if self.y_min is None:
                self.y_min = auto_y_min
            if self.y_max is None:
                self.y_max = auto_y_max

        # 校验并确保范围有效
        try:
            if self.x_min >= self.x_max:
                print('Warning: xmin >= xmax, ignoring custom X bounds and falling back to auto')
                # 重新计算 auto
                all_points = []
                for pts in trajectories.values():
                    all_points.extend(pts)
                if all_points:
                    self.x_min = min(p.x for p in all_points)
                    self.x_max = max(p.x for p in all_points)
                else:
                    self.x_min, self.x_max = 0, 4000
            if self.y_min >= self.y_max:
                print('Warning: ymin >= ymax, ignoring custom Y bounds and falling back to auto')
                all_points = []
                for pts in trajectories.values():
                    all_points.extend(pts)
                if all_points:
                    self.y_min = min(p.y for p in all_points)
                    self.y_max = max(p.y for p in all_points)
                else:
                    self.y_min, self.y_max = 0, 2000
        except Exception:
            # 任何异常时回退到默认安全范围
            self.x_min, self.x_max = 0, 4000
            self.y_min, self.y_max = 0, 2000

        # 添加边距
        x_margin = (self.x_max - self.x_min) * 0.1 if (self.x_max - self.x_min) != 0 else 1
        y_margin = (self.y_max - self.y_min) * 0.1 if (self.y_max - self.y_min) != 0 else 1
        self.x_min -= x_margin
        self.x_max += x_margin
        self.y_min -= y_margin
        self.y_max += y_margin

        # 字体
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)

        # 控制说明
        self.show_controls = True
        # 每包 scantime 映射: packet_index -> scantime (u16)
        self.packet_scantimes = packet_scantimes or {}
        # scantime 显示模式：False=基于可见点，True=基于数据起始包（便于调试）
        self.force_earliest_packet_mode = False
        

    def coord_to_screen(self, x, y):
        """将数据坐标转换为屏幕坐标"""
        # 防止除以零
        x_span = (self.x_max - self.x_min) if (self.x_max - self.x_min) != 0 else 1
        y_span = (self.y_max - self.y_min) if (self.y_max - self.y_min) != 0 else 1
        screen_x = int((x - self.x_min) / x_span * (SCREEN_WIDTH - 100)) + 50
        # 映射调整：使得数据坐标 Y 增大时屏幕坐标 Y 也增大（向下）
        screen_y = int((y - self.y_min) / y_span * (SCREEN_HEIGHT - 150)) + 50
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
                elif event.key == pygame.K_LEFT:
                    # 逐帧后退（按键触发）
                    if self.current_frame > 0:
                        self.current_frame -= 1
                    else:
                        # 回到最后一帧，保持与右键对称行为
                        self.current_frame = max(0, self.max_frames - 1)
                elif event.key == pygame.K_r:
                    # R键重置
                    self.current_frame = 0
                    self.visible_start_indices = {}
                    self.visible_end_indices = {}
                elif event.key == pygame.K_k:
                    # 切换 scantime 显示模式（可见点或最早包），便于调试 key 状态
                    self.force_earliest_packet_mode = not self.force_earliest_packet_mode
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

        # 选择用于显示 scantime 的 packet_index：
        # 默认采用当前可见点中最大的 packet_index；按 `k` 切换为最早包（调试用）
        display_packet_index = None
        if self.force_earliest_packet_mode:
            # 使用数据中最早的 packet_index（若存在）
            if self.packet_scantimes:
                display_packet_index = min(self.packet_scantimes.keys())
        else:
            for fid, pts in self.trajectories.items():
                start_idx = self.visible_start_indices.get(fid, 0)
                end_idx = self.visible_end_indices.get(fid, 0)
                if end_idx > start_idx and end_idx <= len(pts):
                    display_packet_index = max(display_packet_index or 0, pts[end_idx - 1].packet_index)

        # 显示对应的 scantime（若存在）——使用可见点的 packet_index 映射
        scantime_val = self.packet_scantimes.get(display_packet_index) if display_packet_index is not None else None
        if isinstance(scantime_val, tuple) and (len(scantime_val) >= 2):
            low, high = scantime_val[0], scantime_val[1]
            # little-endian u16
            scantime_u16 = low | (high << 8)
            # 可能的手指个数字段与按键状态
            finger_cnt = scantime_val[2] if len(scantime_val) >= 3 else None
            key_state = scantime_val[3] if len(scantime_val) >= 4 else None
            if finger_cnt is None:
                base_str = f'ScanTime: {scantime_u16}'
            else:
                base_str = f'ScanTime: {scantime_u16}  Fingers: {finger_cnt}'
            base_text = self.font.render(base_str, True, self.WHITE)
            self.screen.blit(base_text, (10, 34))
            # 显示当前使用的 packet index 以便排查
            mode_text = 'Mode: EARLIEST' if self.force_earliest_packet_mode else 'Mode: VISIBLE'
            self.screen.blit(self.font.render(mode_text, True, self.GRAY), (10, 58))
            # 若按键按下 (1)，高亮显示 Key: DOWN
            if key_state == 1:
                key_text = self.font.render('Key: DOWN', True, (255, 50, 50))
                x_off = 10 + self.font.size(base_str)[0] + 8
                self.screen.blit(key_text, (x_off, 34))
        else:
            base_text = self.font.render('ScanTime: -', True, self.WHITE)
            self.screen.blit(base_text, (10, 34))
        # 左上角下方：每个 ID 的当前坐标（基于当前帧前最后一个点）
        coords_x = 10
        # 将坐标列表下移，避免与 FPS/ScanTime 重叠
        coords_y = 90
        for finger_id in sorted(self.trajectories.keys()):
            pts = self.trajectories.get(finger_id, [])
            # 仅显示当前可见范围内的坐标
            start_idx = self.visible_start_indices.get(finger_id, 0)
            end_idx = self.visible_end_indices.get(finger_id, 0)
            if end_idx > start_idx and end_idx <= len(pts):
                cur = pts[end_idx - 1]
                # 仅显示数据坐标（十进制）
                coord_line = f'F{finger_id}: X:{cur.x} Y:{cur.y}'
            else:
                # 若当前 ID 在本帧不可见，则跳过显示
                continue

            color = self.FINGER_COLORS[finger_id % len(self.FINGER_COLORS)]
            text = self.font.render(coord_line, True, color)
            self.screen.blit(text, (coords_x, coords_y))
            coords_y += 20

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

        # FPS（放在左上较下方）
        fps_text = self.font.render(f'FPS: {self.fps}', True, self.WHITE)
        self.screen.blit(fps_text, (10, 58))

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
    parser.add_argument('--xmin', type=float, help='Optional: set minimum X value for axis')
    parser.add_argument('--xmax', type=float, help='Optional: set maximum X value for axis')
    parser.add_argument('--ymin', type=float, help='Optional: set minimum Y value for axis')
    parser.add_argument('--ymax', type=float, help='Optional: set maximum Y value for axis')
    args = parser.parse_args()

    print(f"Parsing file: {args.input_file}")

    parser_obj = FingerDataParser()
    trajectories, total_packets, packet_scantimes = parser_obj.process_csv_data(args.input_file)

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

    # 传递可选的自定义边界到渲染器
    renderer = TrajectoryRenderer(trajectories, xmin=args.xmin, xmax=args.xmax, ymin=args.ymin, ymax=args.ymax, packet_scantimes=packet_scantimes)
    renderer.run()


if __name__ == '__main__':
    main()
