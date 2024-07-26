from engine import TerminalEngine


class MyGame(TerminalEngine):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.player_x = width // 2
        self.player_y = height // 2

    def update(self, dt):
        if self.is_key_pressed("q"):
            self.running = False

        if self.is_key_pressed("w"):
            self.player_y -= 1
        if self.is_key_pressed("s"):
            self.player_y += 1
        if self.is_key_pressed("a"):
            self.player_x -= 1
        if self.is_key_pressed("d"):
            self.player_x += 1

        self.player_x = max(0, min(self.width - 1, self.player_x))
        self.player_y = max(0, min(self.height - 1, self.player_y))

        self.buffer = [[" " for _ in range(self.width)] for _ in range(self.height)]
        self.draw_pixel(self.player_x, self.player_y, "@")
        self.draw_text(0, 0, "Use WASD to move, Q to quit")


if __name__ == "__main__":
    game = MyGame(40, 20)
    game.run()
