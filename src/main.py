from flask import Flask, request, abort, make_response
from flask.typing import ResponseReturnValue
from werkzeug.wrappers import Response, Request
from werkzeug.exceptions import HTTPException

import logging
import logging.handlers
import requests
from urllib.parse import urlparse

LOG_FILE = ""
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# BEGIN Log configs
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(LOG_FORMAT)
if LOG_FILE:
    log_file_handler = logging.handlers.RotatingFileHandler(
        f"{LOG_FILE}", maxBytes=5*1024*1024, backupCount=3)
    # logging.FileHandler(f"{LOG_FILE}")
    log_file_handler.setFormatter(log_formatter)
    log.addHandler(log_file_handler)

log_stream_handler = logging.StreamHandler()
log_stream_handler.setFormatter(log_formatter)
log.addHandler(log_stream_handler)


app = Flask(__name__)

# BEGIN Error Handler
@app.errorhandler(HTTPException)
def page_not_found(e):
    log.warning(e)
    return e.name, e.code

# @app.errorhandler(HTTPException)
# def handle_http_exception(e: HTTPException) -> ResponseReturnValue:
#
#     log.warning(e)
#
#     if request.path.startswith("/api"):
#         # Start with the response represented by the error
#         resp = e.get_response()
#
#         import json
#         # jsonify the response
#         resp = make_response(
#             json.dumps(
#                 {
#                     "name": e.name,
#                     "err_msg": e.description
#                 }
#             )
#         )
#         resp.headers["Content-Type"] = "application/json"
#
#         return resp
#     else:
#         return e


# BEGIN App routes
@app.route("/v1")
def api_v1() -> ResponseReturnValue:
    url = request.args.get("cal")

    if not url:
        abort(404, "Error: No Calendar URL found")

    if not check_cal_url(url):
        abort(403, "Error: Not an allowed Calendar origin")

    cal = fetch_cal(url)

    replacements = get_replacement_list(request)

    new_cal = cal_handler(cal, replacements=replacements)
    resp = make_response(new_cal)
    return add_http_headers(resp)


# BEGIN Helper functions
def check_cal_url(org_url: str) -> bool:

    sources_whitelist = {
        "campus.kit.edu": {
            "scheme": ["http", "https", "webcals"],
            "path": ["/sp/webcal/"],
        }
    }

    url = urlparse(org_url)
    if url.hostname not in sources_whitelist:
        log.debug(f"Hostname not whitelisted {url=}")
        return False

    source_options = sources_whitelist[url.hostname]
    if source_options["scheme"] and url.scheme not in source_options["scheme"]:
        log.debug(f"Scheme not whitelisted {url=}")
        return False

    if source_options["path"]:
        for path in source_options["path"]:
            if url.path.startswith(path):
                break
        else:
            log.debug(f"Path not whitelisted {url=}")
            return False

    log.debug(f"URL passed all checks {url=}")
    return True


def fetch_cal(url: str) -> str:
    try:
        a = requests.get(url)
        log.info(f"Fetched {url=}")
    except Exception as e:
        log.error(f"{e}")
        abort(500)

    return a.text

# TODO: Extract replacements from URI, standard needed
def get_replacement_list(request: Request) -> list[list[str]]:
    return list(list())


def cal_handler(cal: str,
                replacements: list[list[str]] = list(list())
                ) -> str:
    # replacements = [[
    #     "NAME:KIT-Termine", "NAME:Proxy-KIT-Termine"
    # ]]

    for i in replacements:
        cal = cal.replace(i[0], i[1])

    return cal


def add_http_headers(resp: Response, filename: str = "Proxy-Calendar") -> Response:
    # resp.headers["Content-Type"] = "text/plain"  # For debugging

    resp.headers["Content-Type"] = "text/calendar"
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


def main() -> None:
    app.run(debug=True)


def tests() -> None:
    log.debug(check_cal_url("https://campus.kit.edu/sp/webcal/IU1b24BcgM"))
    log.debug(check_cal_url("http://campus.kit.edu/sp/webcal/IU1b24BcgM"))
    log.debug(check_cal_url(
        "webcals://campus.kit.edu/sp/webcal/IU1b24BcgM?tguid=0xB7532209C5264C53A99D9128A9F9A321"))
    log.debug(check_cal_url("https://google.com"))

    # Eigenen URL parser machen? Auf keinen fall https://stackoverflow.com/a/10988764
    # check_cal_url("http://netloc/path;someparam=some;otherparam=other?query1=val1&query2=val2#frag")
    # check_cal_url("http://some.page.pl/nothing.py;someparam=some;otherparam=other?query1=val1&query2=val2#frag")


if __name__ == "__main__":
    main()
    # tests()
