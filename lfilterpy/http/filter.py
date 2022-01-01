import socket
import select
import sys
import _thread
import time
from urllib.parse import urlparse


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
        self.sock = None

    @classmethod
    def send_and_receive(cls, request, sock):
        try:
            sock.sendall(request)
        except BrokenPipeError:
            pass
        sock.settimeout(15)
        response = b''
        try:
            chunk = sock.recv(2048)
            while chunk:  # 循环接收数据，因为一次接收不完整
                response += chunk
                chunk = sock.recv(2048)
        except (TimeoutError, socket.timeout):
            print("请求超时")
        except ConnectionResetError:
            print("请求中断")
        sock.close()
        return response

    def get_connection(self, domain, port):
        sock = socket.socket()
        try:
            sock.connect((domain, port))  # 连接网站 ，发出一个HTTP请求
        except ConnectionRefusedError:
            print("连接失败!!!")
            self.input.remove(self.sock)
        except socket.gaierror:
            sock.connect(("www." + domain, port))
        return sock

    @classmethod
    def get_data_get(cls, url, domain):
        suburl = url[url.find(domain) + len(domain):]
        request = 'GET {0} HTTP/1.0\r\nHost: {1}\r\n\r\n'.format(suburl, domain)
        return request

    def process_https(self, c, domain, port):
        request = c.recv(2048 * 4)
        print("request", request)
        if request:
            sock = self.get_connection(domain, port)
            response = self.send_and_receive(request, sock)
            return response

    def process_req(self):
        c, location = self.proxy.accept()
        self.input += [self.proxy]
        request = c.recv(2048 * 4)
        if request:
            data = str(request.decode("utf8"))
            method = data[0:data.find(' ')].strip()
            if method != "CONNECT":
                domain = data[data.find('Host:') + 6:data.find("\n", data.find('Host:'))].strip()
                if method == "GET":
                    if domain in self.targets:
                        try:
                            content = open(self.file, "r", encoding="utf-8")
                        except FileNotFoundError:
                            raise FileNotFoundError("文件未找到")
                        c.send(content.read().encode())
                        c.close()
                        return
                    else:
                        url = data[data.find(' '):data.find("HTTP") - 1].strip()
                        protocol = urlparse(url)[0]
                        if protocol == "https":
                            port = 443
                        elif protocol == "http":
                            port = 80
                        request = self.get_data_get(url, domain)
                sock = self.get_connection(domain, port)
                response = self.send_and_receive(request.encode(), sock)
            else:
                domain = data[data.find(' '):data.find("HTTP") - 1].strip().split(":")[0]
                port = int(data[data.find(' '):data.find("HTTP") - 1].strip().split(":")[1])
                sock = self.get_connection(domain, port)
                response = 'HTTP/1.0 200 Connection established\r\nProxy-agent: Netscape-Proxy/1.1\r\n\r\n'.encode(
                    "gbk")
                try:
                    c.sendall(response)
                except BrokenPipeError:
                    pass
                c.settimeout(15)
                request = c.recv(2048 * 4)
                response = self.send_and_receive(request, sock)
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
