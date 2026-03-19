# trajectory/renderer.py
import pygame

# Simple renderer functions that accept trajectories in the form:
# { finger_id: [FingerPoint, ...], ... }
# and a coord_to_screen(x,y) callable to map data coords to screen coords.

def render_trajectories(screen, trajectories, coord_to_screen, finger_colors=None):
    if finger_colors is None:
        finger_colors = [
            (255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 165, 0), (128, 0, 128),
            (165, 42, 42), (255, 192, 203), (128, 128, 128), (128, 128, 0), (0, 255, 255),
        ]

    for fid, points in trajectories.items():
        if not points:
            continue

        # Determine visible slice: by default render all provided points
        visible_points = points
        color = finger_colors[fid % len(finger_colors)]

        # Determine current status from last point
        current_status = visible_points[-1].status if visible_points else 3
        is_large = current_status in (0, 2)

        if is_large:
            # large: thick polyline + filled (semi-transparent) overlay + large circle
            if len(visible_points) > 1:
                pts = [coord_to_screen(p.x, p.y) for p in visible_points]
                for i in range(len(pts) - 1):
                    pygame.draw.line(screen, color, pts[i], pts[i+1], 6)

                # semi-transparent overlay
                if len(pts) > 2:
                    surf = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
                    pygame.draw.lines(surf, (*color, 80), False, pts, 6)
                    screen.blit(surf, (0,0))

            # current point
            cur = visible_points[-1]
            x, y = coord_to_screen(cur.x, cur.y)
            pygame.draw.circle(screen, color, (x, y), 15)

        else:
            # finger: thin polyline + small hollow circle
            if len(visible_points) > 1:
                for i in range(len(visible_points) - 1):
                    p1 = visible_points[i]
                    p2 = visible_points[i + 1]
                    x1, y1 = coord_to_screen(p1.x, p1.y)
                    x2, y2 = coord_to_screen(p2.x, p2.y)
                    pygame.draw.line(screen, color, (x1, y1), (x2, y2), 2)

            cur = visible_points[-1]
            x, y = coord_to_screen(cur.x, cur.y)
            # hollow circle
            status_color = (255,0,0) if cur.status==3 else (128,128,128)
            pygame.draw.circle(screen, status_color, (x, y), 8, 2)


def render_legend(screen, trajectories, font, finger_colors=None, top_right=(800,60)):
    if finger_colors is None:
        finger_colors = [
            (255, 0, 0), (0, 0, 255), (0, 255, 0), (255, 165, 0), (128, 0, 128),
            (165, 42, 42), (255, 192, 203), (128, 128, 128), (128, 128, 0), (0, 255, 255),
        ]
    x, y = top_right
    for fid in sorted(trajectories.keys()):
        color = finger_colors[fid % len(finger_colors)]
        text = font.render(f'F{fid}: {len(trajectories[fid])} pts', True, color)
        screen.blit(text, (x, y))
        y += 24