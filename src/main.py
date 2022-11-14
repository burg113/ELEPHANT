from flask import Flask, render_template

import logging
import logging.handlers
import confs, v0

log_file_handler = logging.handlers.RotatingFileHandler(f"{confs.LOG_FILE}", maxBytes=5*1024*1024, backupCount=3)
logging.basicConfig(
    level=confs.LOG_LEVEL,
    format=confs.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        log_file_handler
    ]
)

app = Flask(__name__)
app.register_blueprint(v0.app, url_prefix=f'{confs.APP_BASEPATH }/v0')

@app.route("/")
def index():
    return render_template("index.html", APP_NAME=confs.APP_NAME, APP_URL=confs.APP_URL)

def main() -> None:
    print(
"""
 _______  __       _______ .______    __    __       ___      .__   __. .___________.
|   ____||  |     |   ____||   _  \  |  |  |  |     /   \     |  \ |  | |           |
|  |__   |  |     |  |__   |  |_)  | |  |__|  |    /  ^  \    |   \|  | `---|  |----`
|   __|  |  |     |   __|  |   ___/  |   __   |   /  /_\  \   |  . `  |     |  |     
|  |____ |  `----.|  |____ |  |      |  |  |  |  /  _____  \  |  |\   |     |  |     
|_______||_______||_______|| _|      |__|  |__| /__/     \__\ |__| \__|     |__|     
""")
    app.run(debug=confs.APP_DEBUG)


if __name__ == "__main__":
    main()