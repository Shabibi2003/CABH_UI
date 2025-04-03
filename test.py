import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import calendar
from matplotlib.colors import ListedColormap, BoundaryNorm

# Database connection details
host = "139.59.34.149"
user = "neemdb"
password = "(#&pxJ&p7JvhA7<B"
database = "cabh_iaq_db"

# Function to plot and display heatmaps in Streamlit
def plot_and_display_feature_heatmaps(df, features, year, month):
    feature_boundaries = {
        'aqi': [0, 50, 100, 150, 200, 300, 500],
        'pm25': [0, 12, 35, 55, 150, 250, 500],
        'pm10': [0, 20, 50, 100, 250, 350, 500],
        'co2': [0, 900, 10000],
        'voc': [0, 500, 1000]
    }

    feature_labels = {
        'aqi': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'pm25': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'pm10': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'co2': ['Good', 'Poor'],
        'voc': ['Good', 'Poor']
    }

    # Filter data for the selected month
    for feature in features:
        indoor_feature = feature

        # Filter data for the current feature and year
        feature_data = df[(df.index.year == year) & (df.index.month == month)][feature]

        if feature_data.empty:
            st.warning(f"No data available for {feature} in {calendar.month_name[month]} {year}.")
            continue

        # Initialize the figure for a single subplot (for a single month)
        fig, ax = plt.subplots(figsize=(10, 6))

        # Define custom color map
        color_list = ['#006400', '#228B22', '#FFFF00', '#FF7F00', '#FF0000', '#8B0000']
        cmap = ListedColormap(color_list)

        # Get boundaries and labels for the feature
        boundaries = feature_boundaries[feature]
        labels = feature_labels[feature]

        # Adjust boundaries to avoid extra tick issue
        if len(boundaries) - 1 != len(labels):
            labels = labels[:-1]  # Adjust if boundaries and labels lengths don't match

        # Prepare the calendar data (up to 5 weeks in a month)
        num_days = calendar.monthrange(year, month)[1]
        calendar_data = np.full((5, 7), np.nan)  # 5 rows to accommodate up to 5 weeks

        for day in range(1, num_days + 1):
            day_values = feature_data[feature_data.index.day == day]
            if not day_values.empty:
                daily_avg = day_values.mean()

                # Calculate position in the calendar grid
                first_day_of_month = calendar.monthrange(year, month)[0]  # First weekday of the month
                week_row = (day + first_day_of_month - 1) // 7
                week_col = (day + first_day_of_month - 1) % 7

                # Ensure the week_row is within bounds (maximum of 5 rows)
                if week_row < 5:
                    calendar_data[week_row, week_col] = daily_avg

        # Plot the heatmap for the selected feature
        norm = BoundaryNorm(boundaries, cmap.N)
        sns.heatmap(calendar_data, annot=True, fmt=".0f", cmap=cmap, norm=norm,
                    cbar=False, xticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], 
                    yticklabels=[1, 2, 3, 4, 5], ax=ax, linewidths=1, linecolor='black')

        ax.set_title(f"{calendar.month_name[month]} {year} - {indoor_feature}", fontsize=14)
        ax.set_xlabel("Day of the Week", fontsize=12)
        ax.set_ylabel("Week", fontsize=12)

        # Create extra space for the color bar and adjust layout
        fig.subplots_adjust(right=0.85)  # Add more space to the right of the subplots

        # Create the color bar in the extra space to the right
        cbar_ax = fig.add_axes([0.87, 0.1, 0.03, 0.8])  # Position for the color bar
        cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, orientation='vertical')

        # Set color bar ticks and labels
        cbar.set_ticks([(b + b_next) / 2 for b, b_next in zip(boundaries[:-1], boundaries[1:])])
        cbar.set_ticklabels(labels)
        cbar.ax.tick_params(labelsize=12)  # Adjust font size of color bar ticks
        cbar.ax.set_ylabel(f"{feature} Levels", fontsize=14)  # Label for the color bar

        # Display the heatmap in Streamlit
        st.pyplot(fig)
        plt.close()

# Streamlit app
st.title("CABH Indoor Air Quality Monitoring")

# User inputs
device_id = st.text_input("Enter Device ID:", value="1202240012")
year = st.number_input("Select Year:", min_value=2024, max_value=2025, value=2024)
month = st.selectbox("Select Month:", list(range(1, 13)))

# Button to generate heatmaps
if st.button("Generate Heatmaps"):
    if not device_id.strip():
        st.error("Device ID cannot be empty.")
        st.stop()
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()

        # Query to fetch data
        query = """
        SELECT id, deviceID, datetime, pm25, pm10, aqi, co2, voc, temp, humidity, battery, viral_index
        FROM reading_db
        WHERE deviceID = %s AND YEAR(datetime) = %s AND MONTH(datetime) = %s;
        """
        cursor.execute(query, (device_id, year, month))
        rows = cursor.fetchall()
        st.success("Data fetched successfully.")
        if rows:
            # Process data
            df = pd.DataFrame(rows, columns=["id", "deviceID", "datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity", "battery", "viral_index"])
            df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            df.set_index('datetime', inplace=True)

            # Generate heatmaps and statistics
            pollutants = ['aqi', 'pm25', 'pm10', 'co2', 'voc']
            plot_and_display_feature_heatmaps(df, pollutants, year, month)

        else:
            st.warning("No data found for the given Device ID and selected month.")

    except mysql.connector.Error as e:
        st.error(f"Database error: {e}")
    except Exception as e:
        st.error(f"An unexpected error occurred: {e}")  # Handle unexpected errors
    finally:
        # Ensure the database connection is closed
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()
            st.info("Database connection closed.")
