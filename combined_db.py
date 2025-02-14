"""
Combined database for managing walking/running and carpooling activities.
"""

import mysql.connector
from mysql.connector import Error

# Database connection
def create_connection(db_name):
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='npol',
            database=db_name
        )
        print(f"Connection to MySQL DB '{db_name}' successful")
    except Error as e:
        print(f"The error '{e}' occurred")
    return connection

# Create tables
def create_tables(connection):
    cursor = connection.cursor()
    try:
        # Users table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Users (
            user_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            total_distance FLOAT DEFAULT 0
        )
        """)

        # Friends table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Friends (
            user_id INT,
            friend_id INT,
            PRIMARY KEY (user_id, friend_id),
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (friend_id) REFERENCES Users(user_id)
        )
        """)

        # CarpoolTrips table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS CarpoolTrips (
            trip_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            friend_id INT,
            distance FLOAT NOT NULL,
            trip_date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id),
            FOREIGN KEY (friend_id) REFERENCES Users(user_id)
        )
        """)

        # WalkingRunningTrips table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS WalkingRunningTrips (
            trip_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            initial_distance FLOAT NOT NULL,
            final_distance FLOAT NOT NULL,
            trip_time TIME NOT NULL,
            initial_location VARCHAR(100) NOT NULL,
            final_location VARCHAR(100) NOT NULL,
            trip_date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        """)

        # Rewards table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS Rewards (
            reward_id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            reward_points INT NOT NULL,
            reward_date DATE NOT NULL,
            FOREIGN KEY (user_id) REFERENCES Users(user_id)
        )
        """)

        connection.commit()
        print("Tables created successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Add a new user
def add_user(connection, name, email):
    cursor = connection.cursor()
    try:
        cursor.execute("""
        INSERT INTO Users (name, email) VALUES (%s, %s)
        """, (name, email))
        connection.commit()
        print("User added successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Add a friend relationship
def add_friend(connection, user_id, friend_id):
    cursor = connection.cursor()
    try:
        cursor.execute("""
        INSERT INTO Friends (user_id, friend_id) VALUES (%s, %s)
        """, (user_id, friend_id))
        connection.commit()
        print("Friend added successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Record a carpool trip
def record_carpool_trip(connection, user_id, friend_id, distance, trip_date):
    cursor = connection.cursor()
    try:
        cursor.execute("""
        INSERT INTO CarpoolTrips (user_id, friend_id, distance, trip_date) VALUES (%s, %s, %s, %s)
        """, (user_id, friend_id, distance, trip_date))

        # Update total distance for both users
        cursor.execute("""
        UPDATE Users SET total_distance = total_distance + %s WHERE user_id = %s
        """, (distance, user_id))

        cursor.execute("""
        UPDATE Users SET total_distance = total_distance + %s WHERE user_id = %s
        """, (distance, friend_id))

        connection.commit()
        print("Carpool trip recorded successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Record a walking/running trip
def record_walking_running_trip(connection, user_id, initial_distance, final_distance, trip_time, initial_location, final_location, trip_date):
    cursor = connection.cursor()
    try:
        distance = final_distance - initial_distance
        cursor.execute("""
        INSERT INTO WalkingRunningTrips (user_id, initial_distance, final_distance, trip_time, initial_location, final_location, trip_date)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (user_id, initial_distance, final_distance, trip_time, initial_location, final_location, trip_date))

        # Update total distance for the user
        cursor.execute("""
        UPDATE Users SET total_distance = total_distance + %s WHERE user_id = %s
        """, (distance, user_id))

        connection.commit()
        print("Walking/Running trip recorded successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Issue rewards based on distance
def issue_rewards(connection):
    cursor = connection.cursor()
    try:
        # Calculate rewards based on total distance
        cursor.execute("""
        SELECT user_id, total_distance FROM Users
        """)
        users = cursor.fetchall()

        for user in users:
            user_id, total_distance = user
            reward_points = int(total_distance // 10)  # 1 point per 10 km

            if reward_points > 0:
                cursor.execute("""
                INSERT INTO Rewards (user_id, reward_points, reward_date) VALUES (%s, %s, CURDATE())
                """, (user_id, reward_points))

        connection.commit()
        print("Rewards issued successfully")
    except Error as e:
        print(f"The error '{e}' occurred")

# Main function
def main():
    db_name = 'combined_db'
    connection = create_connection(db_name)
    if connection:
        create_tables(connection)

        # Example usage
        add_user(connection, "John Doe", "john@example.com")
        add_user(connection, "Jane Doe", "jane@example.com")
        add_friend(connection, 1, 2)
        record_carpool_trip(connection, 1, 2, 50.5, '2023-10-01')
        record_walking_running_trip(connection, 1, 0, 5.0, '01:30:00', 'Home', 'Park', '2023-10-02')
        issue_rewards(connection)

        connection.close()

if __name__ == "__main__":
    main()