# renderer.py

import pygame

class Renderer:
    def __init__(self, width, height):
        pygame.init()
        self.screen = pygame.display.set_mode((width, height))
        self.clock = pygame.time.Clock()
        self.running = True

    def draw_finger_trajectory(self, trajectories):
        for trajectory in trajectories:
            if trajectory['status'] == 3:  # Finger touch
                pygame.draw.lines(self.screen, (255, 0, 0), False, trajectory['points'], 2)
                for point in trajectory['points']:
                    pygame.draw.circle(self.screen, (255, 0, 0), point, 4, 1)
            elif trajectory['status'] == 2:  # Large touch
                pygame.draw.lines(self.screen, (0, 0, 255), False, trajectory['points'], 6)
                pygame.draw.polygon(self.screen, (0, 0, 255, 128), trajectory['filled_area'])
                for point in trajectory['points']:
                    pygame.draw.circle(self.screen, (0, 0, 255), point, 15)

    def update_display(self):
        pygame.display.flip()

    def clear_screen(self):
        self.screen.fill((255, 255, 255))

    def run(self, trajectories):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            self.clear_screen()
            self.draw_finger_trajectory(trajectories)
            self.update_display()
            self.clock.tick(130)

        pygame.quit()
