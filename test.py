import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import calendar
from matplotlib.colors import ListedColormap, BoundaryNorm

st.set_page_config(
    page_title="Indoor Air Quality Dashboard",  # Title on browser tab
    page_icon="🌫️",                            # Emoji or image
    layout="wide",                              # 'centered' or 'wide'
    initial_sidebar_state="expanded"            # Or 'collapsed'
)


# Database connection details
host = "139.59.34.149"
user = "neemdb"
password = "(#&pxJ&p7JvhA7<B"
database = "cabh_iaq_db"

# Device Data Dictionary (deviceID, address, typology)
device_data = {
    "1201240075": ("Hines Office, 12th Floor, One Horizon Centre, Sec-43, Gurugram", "Office"),
    "1201240078": ("Hines Office, 12th Floor, One Horizon Centre, Sec-43, Gurugram", "Office"),
    "1202240026": ("D-1/25 Vasant Vihar, New Delhi-110057(EDS Delhi)", "Office"),
    "1202240025": ("D-1/25 Vasant Vihar, New Delhi-110057(EDS Delhi)", "Office"),
    "1203240081": ("26A Poorvi Marg, Vasant Vihar, New Delhi-110057 (EDS, E-Block, Delhi)", "Office"),
    "1202240011": ("D-188, Abul Fazal Enclave-I, Jamia Nagar, New Delhi-110025", "Apartment"),
    "1202240027": ("D-188, Abul Fazal Enclave-I, Jamia Nagar, New Delhi-110025", "Apartment"),
    "1203240076": ("D 184 ABUL FAZAL ENCLAVE, JAMIA NAGAR, OKHLA, NEW DELHI 25", "Midrise Apartment (G+5)"),
    "1203240078": ("D 184 ABUL FAZAL ENCLAVE, JAMIA NAGAR, OKHLA, NEW DELHI 25", "Midrise Apartment (G+5)"),
    "1203240075": ("A 48/B, Third Floor, Abul Fazal Enclave Part II, New Delhi", "Residential"),
    "1201240077": ("448, Sector-9, Pocket-1 DDA Flats Dwarka, New Delhi-110075", "Residential"),
    "1201240072": ("448, Sector-9, Pocket-1 DDA Flats Dwarka, New Delhi-110075", "Residential"),
    "1203240079": ("C-403, Prince Apartments, Plot 54, I.P. Extension, Patparganj, Delhi - 110092", "Residential, Multi-family"),
    "1201240079": ("B-3/527, Ekta Gardens Apts, Patparganj, Delhi - 110092", "Residential"),
    "1201240085": ("B-3/527, Ekta Gardens Apts, Patparganj, Delhi - 110092", "Residential"),
    "1203240083": ("Flat No. 25, Tower E2, Sector E1, Vasant Kunj, New Delhi", "Residential"),
    "1203240073": ("Flat no. 495, Block 14, Kaveri Apartments, D6, Vasant Kunj, Delhi - 110070", "Residential"),
    "1203240074": ("569 sector A pocket C Vasant Kunj, Delhi - 110070", "Residential"),
    "1201240076": ("H No.-296 Near Durga Ashram, Chhatarpur, Delhi-110074", "Residential"),
    "1212230160": ("H No.-296 Near Durga Ashram, Chhatarpur, Delhi-110074", "Residential"),
    "1202240009": ("D-13A 2nd Floor Left side, Paryavaran Complex, Delhi 1100030", "Office"),
    "1202240008": ("D-13A 2nd Floor Left side, Paryavaran Complex, Delhi 1100030", "Office"),
    "1201240073": ("569 sector A pocket C Vasant Kunj, Delhi - 110070", "Residential"),
    "1203240080": ("F-5, 318-N, Chirag Delhi, Delhi-110017", "Residential"),
    "1201240074": ("F-5, 318-N, Chirag Delhi, Delhi-110017", "Residential"),
    "1203240077": ("B-2/51-A, Keshav Puram", "Apartment"),
    "1203240082": ("B-2/51-A, Keshav Puram", "Apartment"),
    "1202240029": ("St. Mary's School, Dwarka Sec-19", "Office"),
    "1202240028": ("St. Mary's School, Dwarka Sec-19", "Office"),
    "1202240010": ("St. Mary's School, Dwarka Sec-19", "Office"),
    "1202240012": ("St. Mary's School, Dwarka Sec-19", "School"),
}

# Streamlit app
# st.title("CABH Indoor Air Quality Monitoring")

pollutant_display_names = {
    'aqi': 'AQI',
    'pm25': 'PM 2.5',
    'pm10': 'PM 10',
    'co2': 'CO₂',
    'voc': 'VOC'
}
# Function to plot and display heatmaps for each feature (pollutant)
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
            st.warning(f"No data available for {pollutant_display_names.get(feature, feature)} in {calendar.month_name[month]} {year}.")
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
                    cbar=False, xticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], yticklabels=False,
                    ax=ax, linewidths=1, linecolor='black',
                    annot_kws={"size": 14})  # Increase font size for annotations
        ax.xaxis.tick_top()
        ax.set_title(f"Daily Average - {pollutant_display_names.get(feature, feature)}", fontsize=14, pad=35)
        ax.set_xlabel(f"{month_name} {year}", fontsize=12)
        ax.set_ylabel("Week", fontsize=12)

        ax.set_yticks([])

        # Create extra space for the color bar and adjust layout
        fig.subplots_adjust(right=0.85)  # Add more space to the right of the subplots

        # Create the color bar in the extra space to the right
        cbar_ax = fig.add_axes([0.87, 0.1, 0.03, 0.8])  # Position for the color bar
        cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, orientation='vertical')

        # Set color bar ticks and labels
        cbar.set_ticks([(b + b_next) / 2 for b, b_next in zip(boundaries[:-1], boundaries[1:])])
        cbar.set_ticklabels(labels)
        cbar.ax.tick_params(labelsize=12)  # Adjust font size of color bar ticks
        # cbar.ax.set_ylabel(f"{feature} Levels", fontsize=14)  # Label for the color bar

        # Display the heatmap in Streamlit
        st.pyplot(fig)
        plt.close()

# Streamlit app UI
st.title("Indoor Air Quality Trends")

# Create columns for user inputs (deviceID, year, month)
col1, col2, col3 = st.columns(3)

with col1:
    device_id_list = [
        "1201240075", "1203240078", "1201240078", "1202240026", "1202240025", "1203240081", "1202240011",
        "1202240027", "1203240076", "1203240078", "1203240075", "1201240077", "1201240072", "1203240079",
        "1201240079", "1201240085", "1203240083", "1203240073", "1203240074", "1201240076", "1212230160",
        "1202240009", "1202240008", "1201240073", "1203240080", "1201240074", "1203240077", "1203240082",
        "1202240029", "1202240028", "1202240010", "1202240012"
    ]
    device_id = st.selectbox("Select Device ID:", options=sorted(device_id_list), index=device_id_list.index("1202240012"))


with col2:
    year = st.number_input("Select Year:", min_value=2024, max_value=2025, value=2024)


with col3:
    month = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    month_name = st.selectbox("Select Month:", list(month.keys()), index=0)
    selected_month = month[month_name]  # You can use this as the number later


# Get the address and typology for the entered device ID
device_info = device_data.get(device_id, ("Not Available", "Not Available"))

# Display address and typology
st.write(f"Address: {device_info[0]}")
st.write(f"Typology: {device_info[1]}")

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
        cursor.execute(query, (device_id, year, selected_month))

        rows = cursor.fetchall()
        #st.success("Data fetched successfully.")
        if rows:
            # Process data
            df = pd.DataFrame(rows, columns=["id", "deviceID", "datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity", "battery", "viral_index"])
            df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
            df.set_index('datetime', inplace=True)

            st.success("Data fetched successfully.")
            
            plot_and_display_feature_heatmaps(df, pollutant_display_names.keys(), year, selected_month)

            # Generate heatmaps and statistics
            # pollutants = ['aqi', 'pm25', 'pm10', 'co2', 'voc']
            # plot_and_display_feature_heatmaps(df, pollutants, year, month)

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
