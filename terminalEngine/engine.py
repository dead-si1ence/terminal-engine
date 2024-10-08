import time
import os
import sys
import select
import threading
import math
import termios
import tty
import atexit
import random


class TerminalEngine:
    def __init__(self, width, height, tick_rate=60, max_fps=60):
        self.width = width
        self.height = height
        self.buffer = [[" " for _ in range(width)] for _ in range(height)]
        self.prev_buffer = [[" " for _ in range(width)] for _ in range(height)]
        self.running = False
        self.tick_rate = tick_rate
        self.max_fps = max_fps
        self.tick_duration = 1.0 / tick_rate
        self.frame_duration = 1.0 / max_fps
        self.keys_pressed = set()
        self.keys_released = set()
        self.input_thread = None
        self.old_settings = termios.tcgetattr(sys.stdin)

    def clear_screen(self):
        os.system("cls" if os.name == "nt" else "clear")

    def draw_pixel(self, x, y, char):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.buffer[y][x] = char

    def draw_text(self, x, y, text):
        for i, char in enumerate(text):
            self.draw_pixel(x + i, y, char)

    def render(self):
        output = []
        for y in range(self.height):
            for x in range(self.width):
                if self.buffer[y][x] != self.prev_buffer[y][x]:
                    output.append(f"\033[{y+1};{x+1}H{self.buffer[y][x]}")
                    self.prev_buffer[y][x] = self.buffer[y][x]
        sys.stdout.write("".join(output))
        sys.stdout.flush()

    def input_handler(self):
        while self.running:
            if os.name == "nt":
                import msvcrt

                if msvcrt.kbhit():
                    key = msvcrt.getch().decode("utf-8").lower()
                    self.keys_pressed.add(key)
            else:
                rlist, _, _ = select.select([sys.stdin], [], [], 0.1)
                if rlist:
                    key = sys.stdin.read(1).lower()
                    self.keys_pressed.add(key)
            time.sleep(0.01)

    def start_input_thread(self):
        self.input_thread = threading.Thread(target=self.input_handler)
        self.input_thread.daemon = True
        self.input_thread.start()

    def stop_input_thread(self):
        self.running = False
        if self.input_thread:
            self.input_thread.join()

    def is_key_pressed(self, key):
        return key in self.keys_pressed

    def is_key_released(self, key):
        return key in self.keys_released

    def clear_key_states(self):
        self.keys_released = self.keys_pressed
        self.keys_pressed = set()

    def update(self, dt):
        pass

    def set_raw_mode(self):
        if os.name != "nt":
            tty.setraw(sys.stdin.fileno())

    def restore_terminal(self):
        if os.name != "nt":
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self.old_settings)

    def run(self):
        self.running = True
        self.clear_screen()
        print("\033[?25l", end="", flush=True)  # Hide cursor

        self.set_raw_mode()
        atexit.register(self.restore_terminal)

        self.start_input_thread()

        previous_time = time.perf_counter()
        lag = 0.0

        try:
            while self.running:
                current_time = time.perf_counter()
                elapsed = current_time - previous_time
                previous_time = current_time
                lag += elapsed

                while lag >= self.tick_duration:
                    self.update(self.tick_duration)
                    lag -= self.tick_duration

                self.render()
                self.clear_key_states()

                frame_end = time.perf_counter()
                frame_elapsed = frame_end - current_time
                if frame_elapsed < self.frame_duration:
                    time.sleep(self.frame_duration - frame_elapsed)
        finally:
            self.stop_input_thread()
            self.restore_terminal()
            print("\033[?25h", end="", flush=True)  # Show cursor


def debug(status=False):
    print("NAME: ", __name__)
    print("FILE: ", __file__)
    print("DIR: ", os.path.dirname(os.path.abspath(__file__)))
    print("CWD: ", os.getcwd())
    print("OS: ", os.name)
    print("ARGV: ", sys.argv)
    print("ENV: ", os.environ)
    print("PID: ", os.getpid())
    print("PPID: ", os.getppid())
    print("UID: ", os.getuid())
    print("GID: ", os.getgid())
    print("EUID: ", os.geteuid())
    print("EGID: ", os.getegid())
    print("TERMINAL SIZE: ", os.get_terminal_size())


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

def main():
    game = TetrisGame(40, 40)
    debug(False)
    game.run()


if __name__ == "__main__":
    main()
