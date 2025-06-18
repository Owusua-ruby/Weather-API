from os import getcwd, path

import pandas as pd
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from icecream import ic

from Configurations.config import DEBUG
from utils.helpers import prepare_data

app = FastAPI(title="TAHMO Weather App API", debug=DEBUG)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/api/data", description="Get the last 24hours data recorded")
def data(station):  # The station should be: "TA00001 | Lela Primary School"
    try:
        code, _ = station.split("|")
        data = prepare_data(code.strip())
    except ValueError:
        return JSONResponse(
            {
                "status": "error",
                "message": f"{station} is in wrong format: code | station_name",
            }
        )

    if data is None:
        return JSONResponse(
            {
                "status": "error",
                "message": f"No data available for the station: {station}",
            }
        )
    return JSONResponse({"status": "success", "data": data})


@app.get("/api/get-stations")
def all_stations():
    file_data = pd.read_csv(path.join(getcwd(), "utils/stations.csv"))
    codes = file_data["code"].to_list()
    latitudes = file_data["latitude"].to_list()
    longitudes = file_data["longitude"].to_list()
    names = file_data["name"].to_list()
    station_data = [
        [code, name, latitude, longitude]
        for code, name, latitude, longitude in zip(codes, names, latitudes, longitudes)
    ]
    return station_data
