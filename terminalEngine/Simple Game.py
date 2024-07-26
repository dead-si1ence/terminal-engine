from engine import TerminalEngine
import math


class SimpleGame(TerminalEngine):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.player_x = width / 2
        self.player_y = height / 2
        self.player_vx = 0
        self.player_vy = 0
        self.acceleration = 50
        self.max_speed = 20
        self.friction = 10

    def update(self, dt):
        if self.is_key_pressed('q'):
            self.running = False

        if self.is_key_pressed('w'): self.player_vy -= self.acceleration * dt
        if self.is_key_pressed('s'): self.player_vy += self.acceleration * dt
        if self.is_key_pressed('a'): self.player_vx -= self.acceleration * dt
        if self.is_key_pressed('d'): self.player_vx += self.acceleration * dt

        if not self.is_key_pressed('w') and not self.is_key_pressed('s'):
            self.player_vy -= math.copysign(min(abs(self.player_vy), self.friction * dt), self.player_vy)
        if not self.is_key_pressed('a') and not self.is_key_pressed('d'):
            self.player_vx -= math.copysign(min(abs(self.player_vx), self.friction * dt), self.player_vx)

        speed = math.sqrt(self.player_vx**2 + self.player_vy**2)
        if speed > self.max_speed:
            self.player_vx = (self.player_vx / speed) * self.max_speed
            self.player_vy = (self.player_vy / speed) * self.max_speed

        self.player_x += self.player_vx * dt
        self.player_y += self.player_vy * dt

        self.player_x = max(0, min(self.width - 1, self.player_x))
        self.player_y = max(0, min(self.height - 1, self.player_y))

        self.buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.draw_pixel(int(self.player_x), int(self.player_y), '@')

        speed = math.sqrt(self.player_vx**2 + self.player_vy**2)
        self.draw_text(0, 0, f"Speed: {speed:.2f}")
        self.draw_text(0, 1, f"Pos: ({self.player_x:.2f}, {self.player_y:.2f})")
        self.draw_text(0, 2, "Use WASD to move, Q to quit")

if __name__ == "__main__":
    game = SimpleGame(40, 20)
    game.run()