# host your own file for testing purposes only

from http.server import BaseHTTPRequestHandler, HTTPServer
import time

hostName = "localhost"
serverPort = 5000


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        with open("appointments.ics", "r") as f:
            self.send_response(200)
            self.send_header("Content-type", "text/calendar")
            self.end_headers()
            self.wfile.write(f.read().encode("utf-8"))


def main():
    web_server = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        web_server.serve_forever()
    except KeyboardInterrupt:
        pass

    web_server.server_close()
    print("Server stopped.")


if __name__ == "__main__":
    main()
