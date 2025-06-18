from datetime import datetime
from os import getcwd, path

import pandas as pd
import pytz
import requests
from dateutil import parser
from icecream import ic

from Configurations.config import (
    FORFECAST_API_KEY,
    TAHMO_API_PASSWORD,
    TAHMO_API_USERNAME,
)


def get_measurements(code):
    response = make_request(f"measurements/v2/stations/{code}/measurements/controlled")
    if response is None:
        return None
    try:
        columns = response["results"][0]["series"][0]["columns"]
        values = response["results"][0]["series"][0]["values"]
    except KeyError:
        return {"status": "error", "message": "Measurement data not available"}
    time_index = columns.index("time")
    variable_index = columns.index("variable")
    code_index = columns.index("station")
    value_index = columns.index("value")
    shortcodes = {
        "ap": [],
        "pr": [],
        "ra": [],
        "rh": [],
        "te": [],
        "wd": [],
        "wg": [],
        "ws": [],
    }
    for value in values:
        if value[variable_index] in shortcodes.keys():
            # Only append non-None values
            if value[value_index] is not None:
                shortcodes[value[variable_index]].append(value[value_index])
    
    # Handle precipitation sum
    precip = round(sum(shortcodes["pr"]), 2) if shortcodes["pr"] else 0.0
    shortcodes["pr"] = precip
    
    # Handle other measurements, providing defaults for empty lists or None values
    for key, value_list in shortcodes.items():
        if key == "pr":
            continue
        if value_list:  # If list is not empty
            try:
                last_value = value_list[-1]  # Get the last value instead of pop()
                shortcodes[key] = round(last_value, 2) if last_value is not None else 0.0
            except (TypeError, ValueError):
                shortcodes[key] = 0.0
        else:
            shortcodes[key] = 0.0  # Default value for empty lists
    return {
        "values": shortcodes,
        "last_report": values[-1][time_index],
        "code": values[0][code_index],
    }


def get_stations():
    """Get all stations available. It is treated as job to run once a day to get all stations data"""
    response = make_request("assets/v2/stations")
    data = response["data"]

    station_data = {
        "code": [],
        "status": [],
        "name": [],
        "latitude": [],
        "longitude": [],
        "altitude": [],
        "installation_height": [],
        "timezone": [],
    }
    for dt in data:
        if dt["status"] != 1:
            continue
        station_data["code"].append(dt["code"])
        station_data["status"].append(dt["status"])
        station_data["name"].append(dt["location"]["name"])
        station_data["latitude"].append(dt["location"]["latitude"])
        station_data["longitude"].append(dt["location"]["longitude"])
        station_data["altitude"].append(dt["location"]["elevationmsl"])
        station_data["timezone"].append(dt["location"]["timezone"])
        station_data["installation_height"].append(dt["elevationground"])
    df = pd.DataFrame(station_data).sort_values("code")
    df.set_index("code", inplace=True)
    df.to_csv(path.join(getcwd(), "utils/stations.csv"))


def get_station(code):
    df = pd.read_csv(path.join(getcwd(), "utils/stations.csv"), index_col=0)
    try:
        station_data = df.loc[f"{code}"].to_dict()
        return station_data
    except KeyError:
        return None


def get_forecast(code):
    station = get_station(code)
    response = make_request(
        f"?lat={station['latitude']}&lon={station['longitude']}&apikey={FORFECAST_API_KEY}",
        "forecast",
    )

    if "error" in response and response["error"]:
        return response
    data_day = response["data_day"]
    time = data_day["time"]
    precipitation = data_day["precipitation"]
    forecast_data = [[tm, value] for tm, value in zip(time, precipitation)]
    return forecast_data


def make_request(endpoint, type="observation"):
    if type == "forecast":
        url = f"https://my.meteoblue.com/packages/basic-1h_basic-day/{endpoint}"
        response = requests.get(url)
        return response.json()

    response = requests.get(
        f"https://datahub.tahmo.org/services/{endpoint}",
        auth=(TAHMO_API_USERNAME, TAHMO_API_PASSWORD),
    )
    if response.status_code > 200:
        return None
    return response.json()


def prepare_data(code):
    station_data = get_station(code)
    measurements = get_measurements(code)
    if station_data is None or measurements is None:
        return None
    # Check if measurements returned an error status
    if isinstance(measurements, dict) and "status" in measurements and measurements["status"] == "error":
        return None
    observations = {**station_data, **measurements}
    last_report = parser.isoparse(observations["last_report"]).replace(tzinfo=None)
    tz_utc = pytz.utc
    tz_local = pytz.timezone(observations["timezone"])

    station_local_time_tzname = tz_local.localize(last_report).tzname()
    station_local_time = tz_local.localize(last_report).astimezone(pytz.utc)

    utc_time = tz_utc.localize(last_report)

    observations["station_local_reported_time"] = (
        station_local_time.strftime("%b %d, %Y") + f" ({station_local_time_tzname})"
    )
    observations["utc_reported_time"] = (
        utc_time.strftime("%b %d, %Y") + f" ({utc_time.tzname()})"
    )
    observations["last_report"] = observations["last_report"]

    forecasts = get_forecast(code)

    ic({"observations": observations, "forecasts": forecasts})

    return {"observations": observations, "forecasts": forecasts}
