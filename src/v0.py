from datetime import datetime, timedelta
from icalendar import Calendar, Event
from hyperlink import parse
import requests
from werkzeug.exceptions import HTTPException
from werkzeug.wrappers import Response, Request
from flask.typing import ResponseReturnValue
from flask import Blueprint, request, abort, make_response
from confs import *
import logging
log = logging.getLogger(__name__)

CUSTOM_HEADER_HTTP_CODE = "X-HTTP-CODE"

app = Blueprint('v0', __name__)


# Begin handers
@app.after_request
def add_http_headers(resp: Response, filename: str = f"{APP_NAME}-Proxy-Calendar", content_type: str = "text/plain") -> Response:
    resp.headers["Content-Type"] = f"{content_type}; Charset=utf-8"
    # resp.headers["Content-Disposition"] = f"attachment; filename={filename}"
    if CUSTOM_HEADER_HTTP_CODE not in resp.headers:
        resp.headers[CUSTOM_HEADER_HTTP_CODE] = resp.status_code
    return resp

# BEGIN Error Handler
@app.errorhandler(HTTPException)
def page_not_found(e):
    log.warning(e)
    resp = cal_errors(e)
    return resp

# BEGIN App routes
@app.route("/")
def api_v1() -> ResponseReturnValue:

    # all_headers = str(request.headers).replace("\n", "")
    # log.debug(f"Request from {all_headers}")

    url = request.args.get("cal")

    if not url:
        abort(404, "No Calendar URL in query string found")

    if not check_cal_url(url, CONFIG_ORIGIN_WHITELIST):
        abort(403, "Not an allowed Calendar origin")

    cal = fetch_cal(url)

    replacements = get_replacement_list(request)

    new_cal = cal_handler(cal, replacements=replacements)
    resp = make_response(new_cal)
    return resp


# BEGIN Helper functions
def check_cal_url(org_url: str, whitelist: dict) -> bool:

    url = parse(org_url)
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
        ical = cal_inject_headers(ical)
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


def cal_inject_headers(cal: Calendar) -> Calendar:
    cal["X-WR-CALNAME"] = cal["NAME"] or f"{APP_NAME} - Default Name"
    cal["URL"] = APP_URL
    cal["REFRESH-INTERVAl;VALUE=DURATION"] = "PT30M"  # Update every 30 min
    return cal


def cal_errors(e: HTTPException) -> Response:
    ev = Event()
    ev.add("DTSTART", datetime.today().date())
    ev.add("DTEND", datetime.today().date() + timedelta(days=365))
    ev.add("SUMMARY", f"{APP_NAME}, {e.code} - {e.name}")
    ev.add("DESCRIPTION", e.description)

    cal = Calendar()
    cal.add("NAME", f"{APP_NAME} Error")
    cal.add_component(component=ev)
    cal = cal_inject_headers(cal)

    resp = make_response(
        cal.to_ical(), 200  # e.code
    )
    resp.headers[CUSTOM_HEADER_HTTP_CODE] = f"{e.code}"
    return resp
