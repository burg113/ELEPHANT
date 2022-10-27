from flask import Flask, request, abort, make_response
from flask.typing import ResponseReturnValue
from werkzeug.wrappers import Response, Request
from werkzeug.exceptions import HTTPException

import logging
import logging.handlers
import requests
from hyperlink import parse
from icalendar import Calendar, Event
from datetime import datetime, timedelta

APP_NAME = "ELEPHANT"
APP_VERSION = "0.0.1"
APP_URL = "https://github.com/burg113/ELEPHANT"
APP_DEBUG = True
LOG_FILE = "logs.log"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

CONFIG_ORIGIN_WHITELIST = {
    "campus.kit.edu": {
        "scheme": ["http", "https"],
        "path": ["/sp/webcal/"],
    }
}

# BEGIN Log configs
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
log_formatter = logging.Formatter(LOG_FORMAT)
if LOG_FILE:
    log_file_handler = logging.handlers.RotatingFileHandler(
        f"{LOG_FILE}", maxBytes=5*1024*1024, backupCount=3)
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
    resp = cal_errors(e)
    return resp

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
@app.route("/v0")
def api_v1() -> ResponseReturnValue:

    all_headers = str(request.headers).replace("\n", "")
    log.debug(f"Request from {all_headers}")

    url = request.args.get("cal")

    if not url:
        abort(404, "No Calendar URL found")

    if not check_cal_url(url, CONFIG_ORIGIN_WHITELIST):
        abort(403, "Not an allowed Calendar origin")

    cal = fetch_cal(url)

    replacements = get_replacement_list(request)

    new_cal = cal_handler(cal, replacements=replacements)
    resp = make_response(new_cal)
    return add_http_headers(resp)


# BEGIN Helper functions
def check_cal_url(org_url: str, whitelist: dict) -> bool:

    url = parse(org_url)
    print(url)
    if url.host not in whitelist:
        log.debug(f"Hostname not whitelisted {url=}")
        abort(403, f"Hostname not whitelisted, {url.host}")
        return False

    source_options = whitelist[url.host]
    if source_options["scheme"] and url.scheme not in source_options["scheme"]:
        log.debug(f"Scheme not whitelisted {url=}")
        abort(403, f"Scheme not whitelisted, {url.scheme}")
        return False

    url_path = "/" + "/".join(url.path)[:-1]
    if source_options["path"]:
        for path in source_options["path"]:
            if url_path.startswith(path):
                break
        else:
            log.debug(f"Path not whitelisted {url=}")
            abort(403, f"Path not whitelisted, {url_path}")
            return False

    log.debug(f"URL passed all checks {url=}")
    return True


def fetch_cal(url: str) -> str:
    try:
        r = requests.get(url, headers={"User-Agent": f"{APP_NAME}-Importer"})
        log.info(f"Fetched {url=}")
        if not r.ok:
            log.debug(f"Couldn't fetch {url}")
            abort(
                500, f"Couldn't fetch the calendar, HTTP status code {r.status_code}")
    except requests.exceptions.RequestException as e:
        log.error(f"{e}")
        abort(500, "There has been an error while fetching the Calendar")

    r.encoding = r.apparent_encoding
    return r.text


# TODO: Extract replacements from URI, standard needed
def get_replacement_list(request: Request) -> list[list[str]]:
    return list(list())


def cal_handler(cal: str,
                replacements: list[list[str]] = list(list())
                ) -> str:
    # replacements = [
    #     ["Übungen zu 0133200 (Ü)",
    #      "(Ü) Höhere Mathematik I (Analysis) für die Fachrichtung Informatik - Übungen"],
    #     ["Übungen zu 0133000 (Ü)",
    #      "(Ü) Lineare Algebra I für die Fachrichtung Informatik - Übungen"]
    # ]
    # Inject Custom Header
    try:
        ical = Calendar.from_ical(cal)
        ical["NAME"] = f"{APP_NAME} {ical['NAME']}"
        ical["URL"] = APP_URL
        ical["REFRESH-INTERVAl;VALUE=DURATION"] = "PT30M"  # Update every 30 min
        cal = str(ical.to_ical(), "utf-8")
    except ValueError as e:
        log.debug(f"Could not parse {cal}")
        abort(500, "There has been an error with parsing the Calender")

    for i in replacements:
        if len(i) == 2:
            cal = cal.replace(i[0], i[1])
        else:
            log.warn("Replacements list length not valid")

    return cal


def add_http_headers(resp: Response, filename: str = f"{APP_NAME}-Proxy-Calendar") -> Response:
    resp.headers["Content-Type"] = "text/plain; Charset=utf-8"  # For debugging

    # resp.headers["Content-Type"] = "text/calendar; Charset=utf-8"
    # resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    return resp


def cal_errors(e: HTTPException) -> Response:
    ev = Event()
    ev.add("DTSTART", datetime.today().date())
    ev.add("DTEND", datetime.today().date() + timedelta(days=365))
    ev.add("SUMMARY", f"{APP_NAME}, {e.code} - {e.name}")
    ev.add("DESCRIPTION", e.description)

    cal = Calendar()
    cal.add("NAME", f"{APP_NAME} Error")
    cal.add_component(component=ev)

    resp = make_response(
        cal.to_ical(), e.code
    )
    resp = add_http_headers(resp)
    return resp


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
    app.run(debug=APP_DEBUG)


if __name__ == "__main__":
    main()