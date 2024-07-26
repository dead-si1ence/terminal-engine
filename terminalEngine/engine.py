import time
import os
import sys
import select
import threading
import math
import termios
import tty
import atexit


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


def debug():
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


def main():
    debug()


if __name__ == "__main__":
    main()
