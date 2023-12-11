import streamlit as st
import os, sys, time, json, requests, multiprocessing
import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import geopandas as gpd
import urllib3

# Disable warnings from urllib3
urllib3.disable_warnings()

def download_function(collection):
    request, filepath = collection
    response = requests.get(url=request, verify=False, timeout=30.00).json()
    with open(filepath, 'w') as file_object:
        json.dump(response, file_object)

class Process():
    def __init__(self, lat_range, lon_range, start_date, end_date, parameter):
        self.processes = 5  # Max concurrent requests
        self.request_template = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parameter}&community=RE&longitude={{longitude}}&latitude={{latitude}}&start={start_date}&end={end_date}&format=JSON"
        self.filename_template = "File_Lat_{latitude}_Lon_{longitude}.csv"
        self.lat_range = lat_range
        self.lon_range = lon_range

    def execute(self):
        Start_Time = time.time()
        latitudes = np.arange(self.lat_range[0], self.lat_range[1], 0.5)
        longitudes = np.arange(self.lon_range[0], self.lon_range[1], 0.5)

        requests = []
        for longitude in longitudes:
            for latitude in latitudes:
                request = self.request_template.format(latitude=latitude, longitude=longitude)
                filename = self.filename_template.format(latitude=latitude, longitude=longitude)
                requests.append((request, filename))

        requests_total = len(requests)
        pool = multiprocessing.Pool(self.processes)
        pool.imap_unordered(download_function, requests)

        print("Total Script Time:", round((time.time() - Start_Time), 2))

# Streamlit user interface
st.title("NASA POWER Data Download")

# User input
lat_min = st.slider("Minimum Latitude", -90.0, 90.0, 29.0)
lat_max = st.slider("Maximum Latitude", -90.0, 90.0, 32.0)
lon_min = st.slider("Minimum Longitude", -180.0, 180.0, -99.0)
lon_max = st.slider("Maximum Longitude", -180.0, 180.0, -96.0)
start_date = st.text_input("Start Date (YYYYMMDD)", "20150101")
end_date = st.text_input("End Date (YYYYMMDD)", "20151231")
parameter = st.text_input("NASA POWER Parameter", "ALLSKY_SFC_SW_DWN")

if st.button("Download Data"):
    process = Process((lat_min, lat_max), (lon_min, lon_max), start_date, end_date, parameter)
    process.execute()
    st.success("Download Complete!")

# Further code for visualization
# ...

# Note: You need to modify the visualization part to read the downloaded data and display it.

import glob
import pandas as pd

# Function to load and process data
def load_and_process_data(file_pattern):
    files = glob.glob(file_pattern)
    all_data = []

    for file in files:
        with open(file, 'r') as f:
            data = json.load(f)
            # Extracting data - modify this part according to the structure of your JSON
            for entry in data['features']:
                properties = entry['properties']
                properties['latitude'] = entry['geometry']['coordinates'][1]
                properties['longitude'] = entry['geometry']['coordinates'][0]
                all_data.append(properties)

    df = pd.DataFrame(all_data)
    return df

# Visualization Code in Streamlit
if st.button("Visualize Data"):
    file_pattern = "File_Lat_*.csv"  # Modify this pattern to match your downloaded files
    df = load_and_process_data(file_pattern)

    # Check if the DataFrame is not empty
    if not df.empty:
        # Convert DataFrame to xarray DataArray or Dataset
        # This depends on how your data is structured. Here's a simple example:
        da = xr.DataArray(df['parameter_of_interest'], coords=[df['latitude'], df['longitude']], dims=['latitude', 'longitude'])

        # Create a plot with a geographic projection
        plt.figure(figsize=(10, 6))
        ax = plt.axes(projection=ccrs.PlateCarree())

        # Plot the data
        da.plot(ax=ax, transform=ccrs.PlateCarree())

        # Set the extent to your area of interest
        ax.set_extent([lon_min, lon_max, lat_min, lat_max])  # Adjust as needed

        # Add gridlines, coastlines or other features
        ax.gridlines(draw_labels=True)
        ax.coastlines()

        # Display the plot in Streamlit
        st.pyplot(plt)
    else:
        st.error("No data available for visualization.")

