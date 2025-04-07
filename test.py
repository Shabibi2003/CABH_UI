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
    page_title="Indoor Air Quality Dashboard",
    page_icon="🌫️",
    layout="centered",
    initial_sidebar_state="expanded"
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

# Mapping of indoor device IDs to outdoor device IDs
indoor_to_outdoor_mapping = {
    "1202240026": "THIRD_DPCC_SCR_RKPURAM",
    "1202240025": "THIRD_DPCC_SCR_RKPURAM",
    "1203240081": "THIRD_DPCC_SCR_RKPURAM",
    "1202240011": "DELCPCB010",
    "1202240027": "DELCPCB010",
    "1203240076": "DELCPCB010",
    "1203240078": "DELCPCB010",
    "1203240075": "DELCPCB010",
    "1201240077": "DELDPCC016",
    "1201240072": "DELDPCC016",
    "1203240079": "DELDPCC006",
    "1201240079": "DELDPCC006",
    "1201240085": "DELDPCC006",
    "1203240083": "THIRD_DPCC_SCR_RKPURAM",
    "1203240073": "DELDPCC018",
    "1203240074": "DELDPCC011",
    "1201240076": "DELDPCC018",
    "1212230160": "DELDPCC018",
    "1202240009": "DELDPCC018",
    "1202240008": "DELDPCC018",
    "1201240073": "DELDPCC018",
    "1203240080": "DELCPCB005",
    "1201240074": "DELCPCB005",
    "1203240077": "DELDPCC014",
    "1203240082": "DELDPCC014",
    "1202240029": "DELDPCC016",
    "1202240028": "DELDPCC016",
    "1202240010": "DELDPCC016",
    "1202240012": "DELDPCC016",
}

pollutant_display_names = {
    'aqi': 'AQI',
    'pm25': 'PM 2.5',
    'pm10': 'PM 10',
    'co2': 'CO₂',
    'voc': 'VOC',
    'temp': 'Temp.',
    'humidity': 'Humidity'
}

# Function to plot and display line charts for pollutants
def plot_and_display_line_charts(indoor_df, outdoor_df, pollutant_display_names):
    combined_df = pd.concat(
        [indoor_df.add_suffix('_indoor'), outdoor_df.add_suffix('_outdoor')],
        axis=1
    )

    for pollutant in pollutant_display_names.keys():
        if f"{pollutant}_indoor" in combined_df.columns and f"{pollutant}_outdoor" in combined_df.columns:
            fig, ax = plt.subplots(figsize=(10, 6))
            combined_df[f"{pollutant}_indoor"].plot(ax=ax, label=f"{pollutant_display_names[pollutant]} (Indoor)", color='blue')
            combined_df[f"{pollutant}_outdoor"].plot(ax=ax, label=f"{pollutant_display_names[pollutant]} (Outdoor)", color='orange')
            ax.set_title(f"{pollutant_display_names[pollutant]} - Indoor vs Outdoor", fontsize=14)
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel(pollutant_display_names[pollutant], fontsize=12)
            ax.legend()
            ax.grid(True)
            st.pyplot(fig)
            plt.close()

# Function to plot and display heatmaps for each feature (pollutant)
def plot_and_display_feature_heatmaps(df, features, year, month):
    feature_boundaries = {
        'aqi': [0, 50, 100, 150, 200, 300, 500],
        'pm25': [0, 12, 35, 55, 150, 250, 500],
        'pm10': [0, 20, 50, 100, 250, 350, 500],
        'co2': [0, 900, 10000],
        'voc': [0, 500, 1000],
        'temp': [0, 18, 28, 50],
        'humidity': [0, 50, 70, 100]
    }

    feature_labels = {
        'aqi': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'pm25': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'pm10': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'co2': ['Good', 'Poor'],
        'voc': ['Good', 'Poor'],
        'temp': ['Low', 'Normal', 'High'],
        'humidity': ['Low', 'Normal', 'High']
    }

    # Precompute the calendar grid for the selected month
    num_days = calendar.monthrange(year, month)[1]
    first_day_of_month = calendar.monthrange(year, month)[0]
    calendar_data = np.full((5, 7), np.nan) 

    # Compute daily averages for all features at once
    daily_averages = df.resample('D').mean()

    for feature in features:
        if feature not in daily_averages.columns:
            st.warning(f"No data available for {pollutant_display_names.get(feature, feature)} in {calendar.month_name[month]} {year}.")
            continue

        # Fill the calendar grid with daily averages
        calendar_data.fill(np.nan)  # Reset the grid
        for day in range(1, num_days + 1):
            if day in daily_averages.index.day:
                daily_avg = daily_averages.loc[daily_averages.index.day == day, feature].mean()
                week_row = (day + first_day_of_month - 1) // 7
                week_col = (day + first_day_of_month - 1) % 7
                if week_row < 5:
                    calendar_data[week_row, week_col] = daily_avg

        # Plot the heatmap
        fig, ax = plt.subplots(figsize=(10, 6))
        color_list = ['#006400', '#228B22', '#FFFF00', '#FF7F00', '#FF0000', '#8B0000']
        cmap = ListedColormap(color_list)
        boundaries = feature_boundaries[feature]
        labels = feature_labels[feature]
        norm = BoundaryNorm(boundaries, cmap.N)

        sns.heatmap(calendar_data, annot=True, fmt=".0f", cmap=cmap, norm=norm,
                    cbar=False, xticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], yticklabels=False,
                    ax=ax, linewidths=1, linecolor='black', annot_kws={"size": 14})
        ax.xaxis.tick_top()
        ax.set_title(f"Daily Average - {pollutant_display_names.get(feature, feature)}", fontsize=14, pad=35)
        ax.set_xlabel(f"{calendar.month_name[month]} {year}", fontsize=12)
        ax.set_ylabel("Week", fontsize=12)
        ax.set_yticks([])

        # Add color bar
        fig.subplots_adjust(right=0.85)
        cbar_ax = fig.add_axes([0.87, 0.1, 0.03, 0.8])
        cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, orientation='vertical')
        cbar.set_ticks([(b + b_next) / 2 for b, b_next in zip(boundaries[:-1], boundaries[1:])])
        cbar.set_ticklabels(labels)
        cbar.ax.tick_params(labelsize=12)

        st.pyplot(fig)
        plt.close()
# Streamlit UI
st.markdown('<h1 class="title">Indoor Air Quality Trends</h1>', unsafe_allow_html=True)

# Create columns for user inputs (deviceID, year, month)
col1, col2, col3 = st.columns(3)

with col1:
    device_id_list = list(device_data.keys())
    device_id = st.selectbox("Select Device ID:", options=sorted(device_id_list), index=0)

with col2:
    year = st.number_input("Select Year:", min_value=2024, max_value=2025, value=2024)

with col3:
    month = {
        "January": 1, "February": 2, "March": 3, "April": 4,
        "May": 5, "June": 6, "July": 7, "August": 8,
        "September": 9, "October": 10, "November": 11, "December": 12
    }
    month_name = st.selectbox("Select Month:", list(month.keys()), index=0)
    selected_month = month[month_name]

st.markdown('<div class="red-line"></div>', unsafe_allow_html=True)

# Get the address and typology for the entered device ID
device_info = device_data.get(device_id, ("Not Available", "Not Available"))

# Display address and typology
st.write(f"Address: {device_info[0]}")
st.write(f"Typology: {device_info[1]}")

st.markdown('<div class="red-line"></div>', unsafe_allow_html=True)

# Button to generate line charts
if st.button("Generate Line Charts"):
    with st.spinner("Generating Line Charts...please wait"):
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

            # Get the corresponding outdoor device ID
            outdoor_device_id = indoor_to_outdoor_mapping.get(device_id)
            if not outdoor_device_id:
                st.error(f"No outdoor device mapping found for indoor device ID {device_id}.")
                st.stop()

            # Query to fetch indoor data
            indoor_query = """
            SELECT datetime, pm25, pm10, aqi, co2, voc, temp, humidity
            FROM reading_db
            WHERE deviceID = %s AND YEAR(datetime) = %s AND MONTH(datetime) = %s AND DateTime >= '2024-01-01';
            """
            cursor.execute(indoor_query, (device_id, year, selected_month))
            indoor_rows = cursor.fetchall()

            # Query to fetch outdoor data
            outdoor_query = """
            SELECT datetime, pm25, pm10, aqi, co2, voc, temp, humidity
            FROM cpcb_data
            WHERE deviceID = %s AND YEAR(datetime) = %s AND MONTH(datetime) = %s AND DateTime >= '2024-01-01';
            """
            cursor.execute(outdoor_query, (outdoor_device_id, year, selected_month))
            outdoor_rows = cursor.fetchall()

            query = """
            SELECT datetime, pm25, pm10, aqi, co2, voc, temp, humidity
            FROM reading_db
            WHERE deviceID = %s AND YEAR(datetime) = %s AND MONTH(datetime) = %s AND DateTime >= '2024-01-01';
            """
            cursor.execute(query, (device_id, year, selected_month))
            rows = cursor.fetchall()

            if indoor_rows and outdoor_rows:
                # Process indoor data
                indoor_df = pd.DataFrame(indoor_rows, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                indoor_df['datetime'] = pd.to_datetime(indoor_df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                indoor_df.set_index('datetime', inplace=True)
                indoor_df = indoor_df.resample('D').mean()  # Resample to daily averages

                # Process outdoor data
                outdoor_df = pd.DataFrame(outdoor_rows, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                outdoor_df['datetime'] = pd.to_datetime(outdoor_df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                outdoor_df.set_index('datetime', inplace=True)
                outdoor_df = outdoor_df.resample('D').mean()  # Resample to daily averages

            else:
                st.warning("No data found for the given Device IDs and selected month.")
                
            if rows:
                # Process data
                df = pd.DataFrame(rows, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                df['datetime'] = pd.to_datetime(df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                df.set_index('datetime', inplace=True)
    
                st.success("Data fetched successfully.")

                # Generate heatmaps sequentially
                for feature in pollutant_display_names.keys():
                    plot_and_display_feature_heatmaps(df, [feature], year, selected_month)
    
            else:
                st.warning("No data found for the given Device ID and selected month.")
                # Plot line charts
                plot_and_display_line_charts(indoor_df, outdoor_df, pollutant_display_names)
                
            

        except mysql.connector.Error as e:
            st.error(f"Database error: {e}")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
        finally:
            st.markdown('<div class="red-line"></div>', unsafe_allow_html=True)

            # Ensure the database connection is closed
            if 'conn' in locals() and conn.is_connected():
                cursor.close()
                conn.close()
