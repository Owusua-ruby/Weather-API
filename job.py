import logging
import os
import time
from zoneinfo import ZoneInfo

from apscheduler.schedulers.background import BlockingScheduler

from utils.helpers import get_stations

get_stations()

cwdir = os.getcwd()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    filename=os.path.join(cwdir, "utils/api_logs.log"),
)


scheduler = BlockingScheduler(timezone=ZoneInfo("UTC"))
scheduler.add_job(
    get_stations,
    trigger="cron",
    hour=0,
    minute=0,
    id="get_stations",
    misfire_grace_time=60,
)
scheduler.start()
