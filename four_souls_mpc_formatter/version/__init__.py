APP_NAME = "Four Souls MPC Formatter"

VERSION = {
    "major": 1,
    "minor": 0,
    "patch": 0,
}

DATE = {
    "month": 2,
    "day": 21,
    "year": 2025,
}


def get_version():
    return f"{VERSION['major']}.{VERSION['minor']}.{VERSION['patch']}"


def get_release_date():
    return f"{DATE['year']}-{DATE['month']:02}-{DATE['day']:02}"


def get_header_text():
    return f"{APP_NAME} v{get_version()}, released on {get_release_date()}"
