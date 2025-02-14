import time
import tkinter as tk
from datetime import datetime
import threading
import requests
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim, OpenCage

# Set up geolocators
geolocator_nominatim = Nominatim(user_agent="precise_location_tracker")
geolocator_opencage = OpenCage(api_key="eb13a9e2395949e49298a3827edaca83")  # Your OpenCage API key


# Function to get location from IP using multiple APIs
def get_location():
    try:
        # Fetch data from ipinfo.io
        response_ipinfo = requests.get("https://ipinfo.io/json")
        data_ipinfo = response_ipinfo.json()
        lat_ipinfo, lon_ipinfo = map(float, data_ipinfo["loc"].split(","))
        city_ipinfo = data_ipinfo.get("city", "Unknown")
        country_ipinfo = data_ipinfo.get("country", "Unknown")

        # Fetch data from ip-api.com
        response_ipapi = requests.get("http://ip-api.com/json/")
        data_ipapi = response_ipapi.json()
        lat_ipapi, lon_ipapi = data_ipapi.get("lat", 0), data_ipapi.get("lon", 0)
        city_ipapi = data_ipapi.get("city", "Unknown")
        country_ipapi = data_ipapi.get("country", "Unknown")

        # Fetch data from OpenCage Geocoding API
        response_opencage = requests.get(
            f"https://api.opencagedata.com/geocode/v1/json?q={lat_ipinfo}+{lon_ipinfo}&key=eb13a9e2395949e49298a3827edaca83"
        )
        data_opencage = response_opencage.json()
        if data_opencage.get("results"):
            lat_opencage = data_opencage["results"][0]["geometry"]["lat"]
            lon_opencage = data_opencage["results"][0]["geometry"]["lng"]
            city_opencage = data_opencage["results"][0]["components"].get("city", "Unknown")
            country_opencage = data_opencage["results"][0]["components"].get("country", "Unknown")
        else:
            lat_opencage, lon_opencage, city_opencage, country_opencage = lat_ipinfo, lon_ipinfo, city_ipinfo, country_ipinfo

        # Average the coordinates from all APIs for better accuracy
        lat = (lat_ipinfo + lat_ipapi + lat_opencage) / 3
        lon = (lon_ipinfo + lon_ipapi + lon_opencage) / 3
        city = city_ipinfo if city_ipinfo != "Unknown" else (city_ipapi if city_ipapi != "Unknown" else city_opencage)
        country = country_ipinfo if country_ipinfo != "Unknown" else (
            country_ipapi if country_ipapi != "Unknown" else country_opencage)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return lat, lon, city, country, timestamp
    except Exception as e:
        return None, None, "Error", "Fetching", str(e)


# Function for forward geocoding
def forward_geocode(address):
    try:
        location = geolocator_opencage.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return None, None
    except Exception as e:
        return None, None


class LocationTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Precise Location Tracker")
        self.root.geometry("500x350")

        self.label = tk.Label(root, text="Press Start to Track Location", font=("Arial", 12))
        self.label.pack(pady=20)

        self.start_button = tk.Button(root, text="Start", command=self.start_tracking, bg="green", fg="white",
                                      font=("Arial", 12))
        self.start_button.pack(pady=10)

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_tracking, bg="red", fg="white",
                                     font=("Arial", 12))
        self.stop_button.pack(pady=10)
        self.stop_button.config(state=tk.DISABLED)

        self.tracking = False
        self.tracking_thread = None

    def track_location(self):
        while self.tracking:
            lat, lon, city, country, timestamp = get_location()
            if lat and lon:
                try:
                    location = geolocator_opencage.reverse((lat, lon), exactly_one=True, language="en")
                    address = location.address if location else "Address not found"
                except GeocoderTimedOut:
                    try:
                        location = geolocator_nominatim.reverse((lat, lon), exactly_one=True, language="en")
                        address = location.address if location else "Address not found"
                    except Exception as e:
                        address = f"Error fetching address: {e}"
                except Exception as e:
                    address = f"Error fetching address: {e}"

                self.label.config(text=f"📍 {city}, {country}\n🌍 {lat:.6f}, {lon:.6f}\n🕒 {timestamp}\n🏡 {address}")
            else:
                self.label.config(text="⚠ Unable to fetch location")

            time.sleep(10)  # Increased delay to avoid rate limits

    def start_tracking(self):
        self.tracking = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.tracking_thread = threading.Thread(target=self.track_location)
        self.tracking_thread.start()

    def stop_tracking(self):
        self.tracking = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        if self.tracking_thread:
            self.tracking_thread.join()  # Wait for the thread to finish


if __name__ == "__main__":
    root = tk.Tk()
    app = LocationTracker(root)
    root.mainloop()
