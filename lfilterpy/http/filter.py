import socket
import select
import sys
import _thread
import time


class Filter:

    def __init__(self, port=None, targets=None, file=None):
        if isinstance(port, int) and 0 < port <= 65535:
            self.port = port
        else:
            raise ValueError("port错误", port)
        if isinstance(targets, list):
            self.targets = targets
        else:
            raise ValueError("targets错误", targets)
        self.proxy = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.proxy.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.proxy.bind(('127.0.0.1', self.port))
        self.proxy.listen(10)
        self.input = [self.proxy]
        self.file = file

    def get_data(self, domain, url):
        suburl = url[url.find(domain) + len(domain):]
        sock = socket.socket()
        try:
            sock.connect((domain, 80))  # 连接网站 ，发出一个HTTP请求
        except ConnectionRefusedError:
            print("连接失败!!!")
            self.input.remove(self.sock)
        except socket.gaierror:
            sock.connect(("www."+domain, 80))
        request_url = 'GET {0} HTTP/1.0\r\nHost: {1}\r\n\r\n'.format(suburl, domain)
        sock.send(request_url.encode())
        sock.settimeout(15)
        response = b''
        try:
            chunk = sock.recv(2048)
            while chunk:  # 循环接收数据，因为一次接收不完整
                response += chunk
                chunk = sock.recv(2048)
        except TimeoutError or socket.timeout:
            print("请求超时")
        except ConnectionResetError:
            print("请求中断")
        sock.close()
        return response

    def process_req(self):
        c, location = self.proxy.accept()  # 建立客户端连接
        self.input += [self.proxy]
        request = c.recv(2048 * 4)
        data = str(request.decode())
        if request and data:
            method = data[0:data.find(' ')].strip()
            url = data[data.find(' '):data.find("HTTP") - 1].strip()
            domain = data[data.find('Host:') + 6:data.find("\n", data.find('Host:'))]
            domain = domain.strip()
            if domain in self.targets:
                try:
                    content = open(self.file, "r",encoding="utf-8")
                except FileNotFoundError:
                    print("文件未找到")
                    sys.exit(1)
                c.send(content.read().encode())
            else:
                if method != "CONNECT":
                    response = self.get_data(domain, url)
                    try:
                        c.sendall(response)
                    except BrokenPipeError:
                        pass
        c.close()

    def start_new_process(self):
        try:
            _thread.start_new_thread(self.process_req, ())
        except RuntimeError:
            time.sleep(3)
            self.start_new_process()

    def proxy_sys(self):
        while True:
            readable, _, _ = select.select(self.input, [], [])
            for self.sock in readable:
                if self.sock is self.proxy:
                    self.start_new_process()

    def start(self):
        try:
            print('service start successfully!')
            self.proxy_sys()
        except KeyboardInterrupt:
            sys.exit(1)
