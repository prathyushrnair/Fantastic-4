import time
import geocoder
from geopy.distance import geodesic
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.button import MDRaisedButton
import mysql.connector
from mysql.connector import Error

KV = """
ScreenManager:
    LoginScreen:
    ActivityScreen:
    TrackingScreen:

<LoginScreen>:
    name: "login"
    MDLabel:
        text: "Eco-Commute Tracker"
        halign: "center"
        pos_hint: {"center_y": 0.8}
        font_style: "H4"

    MDTextField:
        id: username
        hint_text: "Enter Username"
        pos_hint: {"center_x": 0.5, "center_y": 0.6}
        size_hint_x: 0.8

    MDRaisedButton:
        text: "Login"
        pos_hint: {"center_x": 0.5, "center_y": 0.4}
        on_press:
            app.root.current = "activity"

<ActivityScreen>:
    name: "activity"
    MDLabel:
        text: "Select Activity"
        halign: "center"
        pos_hint: {"center_y": 0.8}
        font_style: "H4"

    MDRaisedButton:
        text: "Walking"
        pos_hint: {"center_x": 0.5, "center_y": 0.6}
        on_press: 
            app.activity = "Walking"
            app.root.current = "tracking"

    MDRaisedButton:
        text: "Cycling"
        pos_hint: {"center_x": 0.5, "center_y": 0.5}
        on_press: 
            app.activity = "Cycling"
            app.root.current = "tracking"

    MDRaisedButton:
        text: "Public Transport"
        pos_hint: {"center_x": 0.5, "center_y": 0.4}
        on_press: 
            app.activity = "Public Transport"
            app.root.current = "tracking"

<TrackingScreen>:
    name: "tracking"
    MDLabel:
        id: activity_label
        text: "Tracking Activity..."
        halign: "center"
        pos_hint: {"center_y": 0.85}
        font_style: "H5"

    MDLabel:
        id: location_label
        text: "Fetching location..."
        halign: "center"
        pos_hint: {"center_y": 0.6}
        font_style: "H6"

    MDLabel:
        id: distance_label
        text: "Distance: 0 km"
        halign: "center"
        pos_hint: {"center_y": 0.5}
        font_style: "H6"

    MDRaisedButton:
        text: "Stop Tracking"
        pos_hint: {"center_x": 0.5, "center_y": 0.3}
        on_press: 
            app.stop_tracking()
            app.root.current = "activity"
"""

class LoginScreen(Screen):
    pass

class ActivityScreen(Screen):
    pass

class TrackingScreen(Screen):
    pass

class EcoCommuteApp(MDApp):
    def build(self):
        self.activity = None  # To store selected activity
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name="login"))
        self.sm.add_widget(ActivityScreen(name="activity"))
        self.sm.add_widget(TrackingScreen(name="tracking"))
        return Builder.load_string(KV)

    def on_start(self):
        """Initialize tracking when the user enters the tracking screen."""
        self.initial_point = None
        self.running = False

    def start_tracking(self):
        """Start location tracking."""
        self.running = True
        self.initial_point = self.get_location()
        if self.initial_point:
            self.update_ui()
            Clock.schedule_interval(self.track_location, 5)  # Runs every 5 seconds

    def stop_tracking(self):
        """Stop location tracking."""
        self.running = False
        Clock.unschedule(self.track_location)

    def get_location(self):
        """Fetch current location (latitude, longitude)."""
        location = geocoder.ip("me")
        return tuple(location.latlng) if location.latlng else None

    def track_location(self, dt):
        """Fetch new location, calculate distance, update UI, and store in database."""
        if not self.running:
            return

        new_point = self.get_location()
        if new_point:
            distance = (
                geodesic(self.initial_point, new_point).kilometers
                if self.initial_point else 0
            )

            # Store distance in database
            self.save_trip(self.initial_point, new_point, distance)

            self.initial_point = new_point
            self.update_ui(new_point, distance)

    def update_ui(self, location=None, distance=0):
        """Update UI elements with new location and distance."""
        screen = self.sm.get_screen("tracking")
        screen.ids.activity_label.text = f"Tracking {self.activity}..."
        screen.ids.location_label.text = f"Location: {location}" if location else "Fetching location..."
        screen.ids.distance_label.text = f"Distance: {distance:.2f} km"

    def save_trip(self, initial_location, final_location, distance):
        """Save trip details to MySQL database."""
        connection = create_connection()
        if not connection:
            return

        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO WalkingRunningTrips (user_id, initial_distance, final_distance, trip_time, initial_location, final_location, trip_date)
            VALUES (%s, %s, %s, NOW(), %s, %s, CURDATE())
        """, (1, 0, distance, str(initial_location), str(final_location)))  # Replace 1 with user_id if needed

        # Update total distance in Users table
        cursor.execute("""
            UPDATE Users SET total_distance = total_distance + %s WHERE user_id = %s
        """, (distance, 1))  # Replace 1 with user_id

        connection.commit()
        connection.close()
        print(f"Trip saved: {initial_location} -> {final_location}, Distance: {distance} km")

def create_connection():
    """Connect to MySQL database."""
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='npol',
            database='combined_db'
        )
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

if __name__ == "_main_":
    EcoCommuteApp().run()