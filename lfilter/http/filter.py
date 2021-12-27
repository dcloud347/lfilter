import socket


class Filter:

    def __init__(self, host=socket.gethostname(), port=None, buffer_size=None, targets=None):
        self.host = host
        if isinstance(port, int) and 0 < port <= 65535:
            self.port = port
        else:
            raise ValueError("port错误", port)
        if isinstance(buffer_size, int) and 0 < buffer_size:
            self.buffer_size = buffer_size
        else:
            raise ValueError("buffer错误", buffer_size)
        if isinstance(targets, list):
            self.targets = targets
        else:
            raise ValueError("targets错误", targets)

    @classmethod
    def filter(cls):

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((cls.host, cls.port))
