import http.server
import os
from urllib.parse import parse_qs, urlparse
import socket
from datetime import datetime
import pymongo
import json
import sys
import socketserver


class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        url_path = urlparse(self.path).path

        if url_path.startswith('/app/'):
            self.path = os.path.join('static', self.path[len('/app/'):])
        elif url_path == '/':
            self.path = 'app/index.html'
        elif url_path == '/message':
            self.path = 'app/message.html'
        else:
            self.path = 'app' + self.path

        try:
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        except IOError:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def do_POST(self):
        if self.path == '/message':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            parsed_data = parse_qs(post_data.decode())
            message = json.dumps(parsed_data)
            self.send_to_socket(message)
            self.send_response(303)
            self.send_header('Location', '/message')
            self.end_headers()
        else:
            self.send_error(404, 'File Not Found: %s' % self.path)

    def send_to_socket(self, data):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(('socket-server', 5000))
            s.sendall(data.encode())
            s.close()
        except ConnectionRefusedError:
            # Виведення в лог або повернення помилки користувачеві
            print("Could not connect to socket server.")
            self.send_error(
                503, 'Service Unavailable: Socket server is not available')


def run_http_server():
    server_address = ('', 3000)
    httpd = http.server.HTTPServer(server_address, MyHttpRequestHandler)
    httpd.serve_forever()


def run_socket_server():
    client = pymongo.MongoClient("mongodb://mongodb:27017/")
    db = client["mydatabase"]
    collection = db["messages"]

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('socket-server', 5000))
    server_socket.listen(5)
    print("Socket server listening on port 5000")

    while True:
        conn, addr = server_socket.accept()
        with conn:
            print("Connected by", addr)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                data_dict = json.loads(data.decode())
                processed_data = {k: v[0] if isinstance(
                    v, list) else v for k, v in data_dict.items()}

                # Оновлення дати на потрібний формат
                processed_data['date'] = datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S.%f")
                collection.insert_one(processed_data)
                print(f"Saved to MongoDB: {processed_data}")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'socket':
        run_socket_server()
    else:
        run_http_server()
