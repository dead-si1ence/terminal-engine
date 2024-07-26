from engine import TerminalEngine
import time
import random

class TetrisGame(TerminalEngine):
    def __init__(self, width, height):
        super().__init__(width, height)
        self.board_width = 20
        self.board_height = 20
        self.board = [[' ' for _ in range(self.board_width)] for _ in range(self.board_height)]
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.game_over = False
        self.drop_interval = 1.0
        self.last_drop_time = time.time()

        self.shapes = [
            [[1, 1, 1, 1]],
            [[1, 1], [1, 1]],
            [[1, 1, 1], [0, 1, 0]],
            [[1, 1, 1], [1, 0, 0]],
            [[1, 1, 1], [0, 0, 1]],
            [[1, 1, 0], [0, 1, 1]],
            [[0, 1, 1], [1, 1, 0]]
        ]
        self.colors = ['I', 'O', 'T', 'L', 'J', 'S', 'Z']

    def new_piece(self):
        if not self.next_piece:
            self.next_piece = self.random_piece()
        self.current_piece = self.next_piece
        self.next_piece = self.random_piece()
        self.current_x = self.board_width // 2 - len(self.current_piece[0]) // 2
        self.current_y = 0

        if self.collision():
            self.game_over = True

    def random_piece(self):
        shape = random.choice(self.shapes)
        color = self.colors[self.shapes.index(shape)]
        return [list(row) for row in shape], color

    def collision(self):
        for y, row in enumerate(self.current_piece[0]):
            for x, cell in enumerate(row):
                if cell:
                    if (self.current_y + y >= self.board_height or
                        self.current_x + x < 0 or
                        self.current_x + x >= self.board_width or
                        self.board[self.current_y + y][self.current_x + x] != ' '):
                        return True
        return False

    def merge_piece(self):
        for y, row in enumerate(self.current_piece[0]):
            for x, cell in enumerate(row):
                if cell:
                    self.board[self.current_y + y][self.current_x + x] = self.current_piece[1]

    def rotate_piece(self):
        rotated = list(zip(*self.current_piece[0][::-1]))
        old_piece = self.current_piece
        self.current_piece = (rotated, self.current_piece[1])
        if self.collision():
            self.current_piece = old_piece

    def move_piece(self, dx):
        self.current_x += dx
        if self.collision():
            self.current_x -= dx

    def drop_piece(self):
        self.current_y += 1
        if self.collision():
            self.current_y -= 1
            self.merge_piece()
            self.new_piece()
            self.clear_lines()

    def clear_lines(self):
        lines_to_clear = [i for i, row in enumerate(self.board) if all(cell != ' ' for cell in row)]
        for line in lines_to_clear:
            del self.board[line]
            self.board.insert(0, [' ' for _ in range(self.board_width)])
        
        cleared = len(lines_to_clear)
        self.lines_cleared += cleared
        self.score += (cleared ** 2) * 100
        self.level = self.lines_cleared // 10 + 1
        self.drop_interval = max(0.1, 1.0 - (self.level - 1) * 0.1)

    def draw_board(self):
        for y, row in enumerate(self.board):
            for x, cell in enumerate(row):
                self.draw_pixel(x + 1, y + 1, cell if cell != ' ' else '.')

        if self.current_piece:
            for y, row in enumerate(self.current_piece[0]):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_pixel(self.current_x + x + 1, self.current_y + y + 1, self.current_piece[1])

    def draw_next_piece(self):
        if self.next_piece:
            for y, row in enumerate(self.next_piece[0]):
                for x, cell in enumerate(row):
                    if cell:
                        self.draw_pixel(self.board_width + 5 + x, 5 + y, self.next_piece[1])

    def update(self, dt):
        if self.game_over:
            self.draw_text(self.width // 2 - 4, self.height // 2, "GAME OVER")
            self.draw_text(self.width // 2 - 8, self.height // 2 + 1, "Press 'R' to restart")
            if self.is_key_pressed('r'):
                self.__init__(self.width, self.height)
            return

        if self.is_key_pressed('q'):
            self.running = False

        if self.is_key_pressed('a'):
            self.move_piece(-1)
        if self.is_key_pressed('d'):
            self.move_piece(1)
        if self.is_key_pressed('s'):
            self.drop_piece()
        if self.is_key_pressed('w'):
            self.rotate_piece()

        current_time = time.time()
        if current_time - self.last_drop_time > self.drop_interval:
            self.drop_piece()
            self.last_drop_time = current_time

        self.buffer = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        self.draw_board()
        self.draw_next_piece()
        self.draw_text(self.board_width + 3, 1, f"Score: {self.score}")
        self.draw_text(self.board_width + 3, 2, f"Level: {self.level}")
        self.draw_text(self.board_width + 3, 3, f"Lines: {self.lines_cleared}")
        self.draw_text(self.board_width + 3, 4, "Next:")
        self.draw_text(0, self.board_height + 2, "A: Left, D: Right, W: Rotate, S: Drop, Q: Quit")

    def run(self):
        self.new_piece()
        super().run()

if __name__ == "__main__":
    game = TetrisGame(40, 24)
    game.run()