import socketserver

class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        data=self.request[0].strip()
        soc=self.request[1]
        print(f'got {data}')

if __name__ == "__main__":
    HOST = "192.168.0.195"
    #HOST = "scourge"
    PORT = 6700

    with socketserver.UDPServer((HOST,PORT), Handler) as server:
        server.serve_forever()

