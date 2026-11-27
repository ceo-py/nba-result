# find_tz.py — run with: python3 find_tz.py
import os
from datetime import datetime
from zoneinfo import ZoneInfo


def system_tz_name() -> str | None:
    # 1. TZ env var — how Docker and most VPS panels set it
    tz = os.environ.get("TZ")
    if tz:
        return tz

    # 2. /etc/localtime symlink — standard Linux
    link = os.path.realpath("/etc/localtime")
    if "zoneinfo/" in link:
        return link.split("zoneinfo/", 1)[1]

    # 3. plain-text zone files, varies by distro
    for path in ("/etc/timezone", "/var/db/zoneinfo", "/etc/sysconfig/clock"):
        try:
            with open(path) as f:
                name = f.read().strip().split("=")[-1]
            if name:
                return name
        except OSError:
            continue
    return None


name = system_tz_name()
print("IANA name :", name)

tz = ZoneInfo(name) if name else None
now = datetime.now(tz)
print("now       :", now.strftime("%Y-%m-%d %H:%M:%S %Z%z"))
print("offset    :", now.utcoffset(), "| DST:", now.dst())

if tz:
    for month, label in ((1, "January"), (7, "July")):
        probe = datetime(2026, month, 15, 8, 30, tzinfo=tz)
        print(f"08:30 in {label:8}: {probe.utcoffset()} {probe.tzname()}")
