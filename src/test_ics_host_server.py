from http.server import BaseHTTPRequestHandler, HTTPServer
import time
from urllib.parse import urlparse, parse_qs
# auf flask umstellen
import requests

# BASE_URL = "https://campus.kit.edu/sp/webcal/"

URL = "http://localhost:5000"

hostName = "localhost"
serverPort = 8080


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        print("request recieved")

        request = self.requestline
        request = request[request.index(" ")+1:request.rindex(" ")]

        params = {}

        if "?" in request:
            request = request[request.index("?")+1:]

            params = parse_qs(request)

        print(params)

        response = requests.get(URL)

        ics_file = response.content.decode("utf-8")

        # change file

        print("sending response")

        self.send_response(200)
        self.send_header("Content-type", "text/calendar")
        self.end_headers()

        self.wfile.write(ics_file.encode("utf-8"))


if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))

    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")

