import threading


class videoBuffer:
    def __init__(self, size=100):
        self.buffer = [None] * size
        self.cursor = 0
        self.size = size
        self.lock = threading.Lock()

    def add_frame(self, frame):
        self.lock.acquire()
        self.buffer[self.cursor] = frame
        self.cursor = (self.cursor + 1) % self.size
        self.lock.release()

    def get_frame(self):
        return self.buffer[self.cursor -1]
