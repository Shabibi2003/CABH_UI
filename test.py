import streamlit as st
import pandas as pd
import mysql.connector
from datetime import datetime
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import calendar
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.backends.backend_pdf import PdfPages
import io
from io import BytesIO
from PIL import Image

st.set_page_config(
    page_title="Indoor Air Quality Dashboard",
    page_icon="🌫️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def create_pdf_from_figs(fig_dict):
    pdf_buffer = BytesIO()
    with PdfPages(pdf_buffer) as pdf:
        for fig in fig_dict.values():
            pdf.savefig(fig, bbox_inches='tight')
    pdf_buffer.seek(0)
    return pdf_buffer


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

residential_ids = [
    "1203240075", "1201240077", "1201240072", "1203240079", "1201240079",
    "1201240085", "1203240083", "1203240073", "1203240074", "1201240076",
    "1212230160", "1201240073", "1203240080", "1201240074","1202240011",
    "1202240027", "1203240076", "1203240078", "1203240075", "1203240079",
]

# Mapping of indoor device IDs to outdoor device IDs
indoor_to_outdoor_mapping = {
    "1202240026": "THIRD_DPCC_SCR_RKPURAM",
    "1202240025": "THIRD_DPCC_SCR_RKPURAM",
    "1203240081": "THIRD_DPCC_SCR_RKPURAM",
    "1201240075": "CPCB1703205345",
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
    "1202240012": "DELDPCC016"
    
}

pollutant_display_names = {
    'aqi': 'AQI',
    'pm25': 'PM 2.5',
    'pm10': 'PM 10',
    'co2': 'CO₂',
    'voc': 'VOC',
    'temp': 'Temp.',
    'humidity': 'Humidity',
    'heat_index': 'Heat Index'
}

# Function to plot and display line charts for pollutants
def plot_and_display_line_charts(indoor_df, outdoor_df, pollutant_display_names, all_figs):
    thresholds = {
        'aqi': 300,
        'pm25': 250,
        'pm10': 350,
        'co2': 900,
        'voc': 500,
        'temp': 28,
        'humidity': 70,
        'heat_index': 41
    }

    combined_df = pd.concat(
        [indoor_df.add_suffix('_indoor'), outdoor_df.add_suffix('_outdoor')],
        axis=1
    )

    for pollutant in pollutant_display_names.keys():
        indoor_col = f"{pollutant}_indoor"
        outdoor_col = f"{pollutant}_outdoor"

        # Skip plotting if indoor data doesn't exist
        if indoor_col not in combined_df.columns:
            continue

        fig, ax = plt.subplots(figsize=(10, 6))

        # Plot indoor data
        combined_df[indoor_col].plot(ax=ax, label=f"{pollutant_display_names[pollutant]} (Indoor)", color='blue')

        # Plot outdoor data only if:
        # - the pollutant is NOT CO2 or VOC
        # - the column exists
        if pollutant.lower() not in ['co2', 'voc'] and outdoor_col in combined_df.columns:
            combined_df[outdoor_col].plot(ax=ax, label=f"{pollutant_display_names[pollutant]} (Outdoor)", color='orange')

        # Add a horizontal red line for the threshold if it exists
        if pollutant in thresholds:
            ax.axhline(y=thresholds[pollutant], color='red', linestyle='--', linewidth=1.5, label=f"Threshold ({thresholds[pollutant]})")

        ax.set_title(f"{pollutant_display_names[pollutant]} - Indoor vs Outdoor", fontsize=14)
        ax.set_xlabel("Date", fontsize=12)
        ax.set_ylabel(pollutant_display_names[pollutant], fontsize=12)
        ax.legend()
        ax.grid(True)

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        img = img.resize((int(img.width * 0.7), int(img.height * 0.7)))


        st.image(img)
        all_figs[f"{pollutant}_line_chart"] = fig

# Function to plot and display heatmaps for each feature (pollutant)
def plot_and_display_feature_heatmaps(indoor_df, features, year, month, all_figs):
    feature_boundaries = {
        'aqi': [0, 50, 100, 150, 200, 300, 500],
        'pm25': [0, 12, 35, 55, 150, 250, 500],
        'pm10': [0, 20, 50, 100, 250, 350, 500],
        'co2': [0, 900, 10000],
        'voc': [0, 500, 1000],
        'temp': [0, 18, 28, 50],
        'humidity': [0, 50, 70, 100],
        'heat_index': [0, 27, 32, 41, 54]
    }

    feature_labels = {
        'aqi': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'pm25': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'pm10': ['Good', 'Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe'],
        'co2': ['Good', 'Poor'],
        'voc': ['Good', 'Poor'],
        'temp': ['Low', 'Normal', 'High'],
        'humidity': ['Low', 'Normal', 'High'],
        'heat_index': ['Comfortable', 'Caution', 'Extreme Caution', 'Danger']
    }

    num_days = calendar.monthrange(year, month)[1]
    first_day_of_month = calendar.monthrange(year, month)[0]
    calendar_data = np.full((5, 7), np.nan)
    daily_averages = indoor_df.resample('D').mean()

    # Add heat index calculation
    # if 'temp' in indoor_df.columns and 'humidity' in indoor_df.columns:
    #     indoor_df['heat_index'] = calculate_heat_index(indoor_df['temp'], indoor_df['humidity'])
    #     features.append('heat_index')  # Add heat index to the list of features

    for feature in features:
        if feature not in daily_averages.columns:
            continue
        calendar_data.fill(np.nan)
        for day in range(1, num_days + 1):
            if day in daily_averages.index.day:
                daily_avg = daily_averages.loc[daily_averages.index.day == day, feature].mean()
                week_row = (day + first_day_of_month - 1) // 7
                week_col = (day + first_day_of_month - 1) % 7
                if week_row < 5:
                    calendar_data[week_row, week_col] = daily_avg

        fig, ax = plt.subplots(figsize=(10, 6))
        boundaries = feature_boundaries[feature]
        labels = feature_labels[feature]

        # Dynamically adjust the colormap to match the number of bins
        n_bins = len(boundaries) - 1
        color_list = ['#006400', '#228B22', '#FFFF00', '#FF7F00', '#FF0000', '#8B0000']
        cmap = ListedColormap(color_list)
        norm = BoundaryNorm(boundaries, cmap.N)

        sns.heatmap(calendar_data, annot=True, fmt=".0f", cmap=cmap, norm=norm,
                    cbar=False, xticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    yticklabels=False, ax=ax, linewidths=1, linecolor='black', annot_kws={"size": 14})
        ax.xaxis.tick_top()
        ax.set_title(f"Daily Average - {pollutant_display_names.get(feature, feature)}", fontsize=14, pad=35)
        ax.set_xlabel(f"{calendar.month_name[month]} {year}", fontsize=12)
        ax.set_ylabel("Week", fontsize=12)
        ax.set_yticks([])

        fig.subplots_adjust(right=0.85)
        cbar_ax = fig.add_axes([0.87, 0.1, 0.03, 0.8])
        cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cbar_ax, orientation='vertical')
        cbar.set_ticks([(b + b_next) / 2 for b, b_next in zip(boundaries[:-1], boundaries[1:])])
        cbar.set_ticklabels(labels)
        cbar.ax.tick_params(labelsize=12)

        buf = BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        img = img.resize((int(img.width * 0.7), int(img.height * 0.7)))


        st.image(img)
        all_figs[f"{feature}_heatmap"] = fig

# Remaining code with corrected indentation...
def plot_indoor_vs_outdoor_scatter(indoor_df, outdoor_df, pollutants, all_figs):
        # Resample to hourly averages
        indoor_df_hourly = indoor_df.resample('H').mean()
        outdoor_df_hourly = outdoor_df.resample('H').mean()

        for pollutant in pollutants:
            if pollutant in indoor_df_hourly.columns and pollutant in outdoor_df_hourly.columns:
                data = pd.merge(indoor_df_hourly[[pollutant]], outdoor_df_hourly[[pollutant]], left_index=True, right_index=True, how='inner')
                if data.empty:
                    continue

                fig, ax = plt.subplots(figsize=(10, 6))
                ax.scatter(data[pollutant + '_x'], data[pollutant + '_y'], color='purple', alpha=0.7)
                ax.set_title(f"Hourly Avg: Indoor vs Outdoor - {pollutant.upper()}", fontsize=14)
                ax.set_xlabel(f"{pollutant.upper()} (Indoor)", fontsize=12)
                ax.set_ylabel(f"{pollutant.upper()} (Outdoor)", fontsize=12)
                ax.grid(True)
                buf = io.BytesIO()
                fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
                buf.seek(0)
                img = Image.open(buf)
                img = img.resize((int(img.width * 0.7), int(img.height * 0.7)))  # Scale to 70%
                
                st.image(img)
                all_figs[f"{pollutant}_scatter"] = fig

def plot_residential_seasonal_line_chart(indoor_df, pollutants, year, all_figs):
        seasons = {
            "Spring": [2, 3, 4],
            "Summer": [5, 6, 7],
            "Autumn": [8, 9, 10],
            "Winter": [11, 12, 1]
        }
    
        yearly_df = indoor_df[(indoor_df.index.year == year) | ((indoor_df.index.year == year - 1) & (indoor_df.index.month == 12))]
        
        for pollutant in pollutants:
            fig, ax = plt.subplots(figsize=(10, 6))
            for season, months in seasons.items():
                seasonal_data = indoor_df[indoor_df.index.month.isin(months)]
                if not seasonal_data.empty:
                    seasonal_data = seasonal_data.resample('D').mean()
                    ax.plot(seasonal_data.index, seasonal_data[pollutant], label=season)
                else:
                    ax.plot([], [], label=f"{season} (No Data)")
    
            ax.set_title(f"Yearly {pollutant.upper()} Trends for Residential Buildings ({year})", fontsize=14)
            ax.set_xlabel("Date", fontsize=12)
            ax.set_ylabel(f"{pollutant.upper()}", fontsize=12)
            ax.legend(title="Season")
            ax.grid(True)
            ax.set_xlim(indoor_df.index.min(), indoor_df.index.max())
            buf = io.BytesIO()
            fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
            buf.seek(0)
            img = Image.open(buf)
            img = img.resize((int(img.width * 0.7), int(img.height * 0.7)))  # Scale to 70%
                
            st.image(img)
            all_figs[f"{pollutant}_seasonal_line_chart"] = fig


st.markdown("""
        <style>
            .title {
                font-size: 18px;
                text-align: center;
                padding: 20px;
            }
            .black-line {
                border-top: 3px solid black;
                margin-top: 30px;
                margin-bottom: 30px;
            }
        </style>
    """, unsafe_allow_html=True)

st.markdown('<h2 class="title">Indoor & Outdoor Air Quality Trends</h2>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# 1. Heat Index calculation function (reuse your validated logic)
def calculate_heat_index(T, R):
    T_f = T * 9 / 5 + 32
    if T_f < 80:
        HI_f = 0.5 * (T_f + 61.0 + ((T_f - 68.0) * 1.2) + (R * 0.094))
    else:
        HI_f = (-42.379 + 2.04901523 * T_f + 10.14333127 * R
                - 0.22475541 * T_f * R - 0.00683783 * T_f ** 2
                - 0.05481717 * R ** 2 + 0.00122874 * T_f ** 2 * R
                + 0.00085282 * T_f * R ** 2 - 0.00000199 * T_f ** 2 * R ** 2)
        if R < 13 and 80 <= T_f <= 112:
            adjustment = ((13 - R) / 4) * ((17 - abs(T_f - 95)) / 17) ** 0.5
            HI_f -= adjustment
        elif R > 85 and 80 <= T_f <= 87:
            adjustment = ((R - 85) / 10) * ((87 - T_f) / 5)
            HI_f += adjustment
    return (HI_f - 32) * 5 / 9  # Return in Celsius
#-------------------------------------------------------------------------------
# 2. Function to calculate and display the hourly heat index chart
def plot_hourly_heat_index_chart(indoor_df_hourly, outdoor_df_hourly, all_figs):

    # Ensure temp and humidity exist for both indoor and outdoor data
    if 'temp' not in indoor_df_hourly.columns or 'humidity' not in indoor_df_hourly.columns:
        st.warning("Indoor Temperature and Humidity data are required to calculate Heat Index.")
        return
    if 'temp' not in outdoor_df_hourly.columns or 'humidity' not in outdoor_df_hourly.columns:
        st.warning("Outdoor Temperature and Humidity data are required to calculate Heat Index.")
        return

    # Calculate Heat Index column for indoor data
    indoor_df_hourly['heat_index'] = indoor_df_hourly.apply(
        lambda row: calculate_heat_index(row['temp'], row['humidity'])
        if not np.isnan(row['temp']) and not np.isnan(row['humidity']) else np.nan,
        axis=1
    )

    # Calculate Heat Index column for outdoor data
    outdoor_df_hourly['heat_index'] = outdoor_df_hourly.apply(
        lambda row: calculate_heat_index(row['temp'], row['humidity'])
        if not np.isnan(row['temp']) and not np.isnan(row['humidity']) else np.nan,
        axis=1
    )

    # Plot the hourly heat index line chart
    fig, ax = plt.subplots(figsize=(10, 6))
    indoor_df_hourly['heat_index'].plot(ax=ax, color='blue', linewidth=2, label="Indoor Heat Index")
    outdoor_df_hourly['heat_index'].plot(ax=ax, color='orange', linewidth=2, label="Outdoor Heat Index")

    # Add threshold lines with labels
    ax.axhline(y=27, color='brown', linestyle='--', linewidth=1.5, label="Caution (27°C)")
    ax.axhline(y=40, color='red', linestyle='--', linewidth=1.5, label="Danger (40°C)")

    ax.set_title("Hourly Average Heat Index (°C)", fontsize=16)
    ax.set_xlabel("Time", fontsize=12)
    ax.set_ylabel("Heat Index (°C)", fontsize=12)
    ax.legend()
    ax.grid(True)

    # Display in Streamlit
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf)
    img = img.resize((int(img.width * 0.7), int(img.height * 0.7)))
    st.image(img)

    all_figs["hourly_heat_index"] = fig
# --------------------------------------------------------------------------
def plot_and_display_heat_index_heatmap(indoor_df, year, month, all_figs):
        num_days = calendar.monthrange(year, month)[1]
        first_day_of_month = calendar.monthrange(year, month)[0]
        calendar_data = np.full((5, 7), np.nan)
        daily_averages = indoor_df.resample('D').mean()

        def calculate_heat_index(T, R):
            # Convert Celsius to Fahrenheit
            T_f = T * 9 / 5 + 32
        
            if T_f < 80:
                # Simplified Steadman approximation for mild conditions
                HI_f = 0.5 * (T_f + 61.0 + ((T_f - 68.0) * 1.2) + (R * 0.094))
            else:
                # Rothfusz full formula
                HI_f = (-42.379 + 2.04901523 * T_f + 10.14333127 * R
                        - 0.22475541 * T_f * R - 0.00683783 * T_f ** 2
                        - 0.05481717 * R ** 2 + 0.00122874 * T_f ** 2 * R
                        + 0.00085282 * T_f * R ** 2 - 0.00000199 * T_f ** 2 * R ** 2)
        
                # Low humidity adjustment
                if R < 13 and 80 <= T_f <= 112:
                    adjustment = ((13 - R) / 4) * ((17 - abs(T_f - 95)) / 17) ** 0.5
                    HI_f -= adjustment
        
                # High humidity adjustment
                elif R > 85 and 80 <= T_f <= 87:
                    adjustment = ((R - 85) / 10) * ((87 - T_f) / 5)
                    HI_f += adjustment
        
            # Return Heat Index in Celsius
            return (HI_f - 32) * 5 / 9


    
        # Heat Index boundaries and labels
        boundaries = [0,27, 32, 41, 54, 100]
        labels = ['Satisfactory', 'Moderate', 'Poor', 'Very Poor', 'Severe']
        color_list = ['#006400', '#228B22', '#FFFF00', '#FF7F00', '#FF0000']
        cmap = ListedColormap(color_list)
        norm = BoundaryNorm(boundaries, cmap.N)
    
        # Calculate daily Heat Index
        for day in range(1, num_days + 1):
            if day in daily_averages.index.day:
                temp = daily_averages.loc[daily_averages.index.day == day, 'temp'].mean()
                humidity = daily_averages.loc[daily_averages.index.day == day, 'humidity'].mean()
                if not np.isnan(temp) and not np.isnan(humidity):
                    heat_index = calculate_heat_index(temp, humidity)
                    week_row = (day + first_day_of_month - 1) // 7
                    week_col = (day + first_day_of_month - 1) % 7
                    if week_row < 5:
                        calendar_data[week_row, week_col] = heat_index
    
        # Plot Heat Index heatmap
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.heatmap(calendar_data, annot=True, fmt=".1f", cmap=cmap, norm=norm,
                    cbar=False, xticklabels=['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
                    yticklabels=False, ax=ax, linewidths=1, linecolor='black', annot_kws={"size": 14})
        ax.xaxis.tick_top()
        ax.set_title(f"Daily Average Heat Index (°C) - {calendar.month_name[month]} {year}", fontsize=14, pad=35)
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
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=100, bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        img = img.resize((int(img.width * 0.7), int(img.height * 0.7)))  # Scale to 70%
    
        st.image(img)
        all_figs[f"Heat_Index"] = fig


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

st.markdown('<div class="black-line"></div>', unsafe_allow_html=True)

    # Get the address and typology for the entered device ID
device_info = device_data.get(device_id, ("Not Available", "Not Available"))

    # Display address and typology
st.write(f"Address: {device_info[0]}")
st.write(f"Typology: {device_info[1]}")

st.markdown('<div class="black-line"></div>', unsafe_allow_html=True)

    # Button to generate line charts
if st.button("Generate Charts"):
        all_figs = {}
        with st.spinner("Generating Charts...please wait"):
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

                # Query to fetch indoor data for selected month
                indoor_query_month = """
                SELECT datetime, pm25, pm10, aqi, co2, voc, temp, humidity
                FROM reading_db
                WHERE deviceID = %s AND YEAR(datetime) = %s AND MONTH(datetime) = %s;
                """
                cursor.execute(indoor_query_month, (device_id, year, selected_month))
                indoor_rows = cursor.fetchall()

                # Query to fetch all indoor data for the year (for seasonal trends)
                indoor_query_year = """
                SELECT datetime, pm25, pm10, aqi, co2, voc, temp, humidity
                FROM reading_db
                WHERE deviceID = %s AND YEAR(datetime) = %s;
                """
                cursor.execute(indoor_query_year, (device_id, year))
                indoor_rows_year = cursor.fetchall()

                # Query to fetch outdoor data for selected month
                outdoor_query = """
                SELECT datetime, pm25, pm10, aqi, co2, voc, temp, humidity
                FROM cpcb_data
                WHERE deviceID = %s AND YEAR(datetime) = %s AND MONTH(datetime) = %s;
                """
                cursor.execute(outdoor_query, (outdoor_device_id, year, selected_month))
                outdoor_rows = cursor.fetchall()

                if indoor_rows and outdoor_rows:
                # Process indoor data for the selected month
                    indoor_df = pd.DataFrame(indoor_rows, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                    indoor_df['datetime'] = pd.to_datetime(indoor_df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    indoor_df.set_index('datetime', inplace=True)

                    # Filter indoor data: Remove rows with zero in specific columns before resampling
                    columns_to_check_indoor = ['pm25', 'pm10', 'aqi', 'temp']  # Modify as needed
                    indoor_df = indoor_df[(indoor_df[columns_to_check_indoor] != 0).all(axis=1)]

                    # Resample to daily averages after filtering out zero values
                    indoor_df = indoor_df.resample('D').mean()

                    indoor_df_hourly = pd.DataFrame(indoor_rows, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                    indoor_df_hourly['datetime'] = pd.to_datetime(indoor_df_hourly['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    indoor_df_hourly.set_index('datetime', inplace=True)

                    columns_to_check_indoor = ['pm25', 'pm10', 'aqi', 'temp']  # Modify as needed
                    indoor_df_hourly = indoor_df_hourly[(indoor_df_hourly[columns_to_check_indoor] != 0).all(axis=1)]

                    indoor_df_hourly = indoor_df_hourly.resample('H').mean()
                    
                    # Process outdoor data
                    outdoor_df = pd.DataFrame(outdoor_rows, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                    outdoor_df['datetime'] = pd.to_datetime(outdoor_df['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    outdoor_df.set_index('datetime', inplace=True)

                    # Filter outdoor data: Remove rows with zero in specific columns before resampling
                    columns_to_check_outdoor = ['pm25', 'pm10', 'aqi']  # Modify as needed
                    outdoor_df = outdoor_df[(outdoor_df[columns_to_check_outdoor] != 0).all(axis=1)]

                    # Resample to daily averages after filtering out zero values
                    outdoor_df = outdoor_df.resample('D').mean()

                    outdoor_df_hourly = pd.DataFrame(outdoor_rows, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                    outdoor_df_hourly['datetime'] = pd.to_datetime(outdoor_df_hourly['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    outdoor_df_hourly.set_index('datetime', inplace=True)

                    # Filter outdoor data: Remove rows with zero in specific columns before resampling
                    columns_to_check_outdoor = ['pm25', 'pm10', 'aqi']  
                    outdoor_df_hourly = outdoor_df_hourly[(outdoor_df_hourly[columns_to_check_outdoor] != 0).all(axis=1)]

                    # Resample to hourly averages after filtering out zero values
                    outdoor_df_hourly = outdoor_df_hourly.resample('H').mean()

                    # Generate heatmaps and other plots using one-month data
                    features = ['pm25', 'pm10', 'aqi', 'co2', 'voc', 'temp', 'humidity']
                    plot_and_display_feature_heatmaps(indoor_df, features, year, selected_month, all_figs)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<h3 style='font-size:30px; text-align:left; font-weight:bold;'>Heat Index (°C)</h3>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    plot_and_display_heat_index_heatmap(indoor_df, year, selected_month, all_figs)


                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<h3 style='font-size:30px; text-align:left; font-weight:bold;'>Line Charts of Indoor & Outdoor</h3>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)

                    plot_and_display_line_charts(indoor_df, outdoor_df, pollutant_display_names, all_figs)


                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<h3 style='font-size:30px; text-align:left; font-weight:bold;'>Indoor vs Outdoor Scatter Plots</h3>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    plot_indoor_vs_outdoor_scatter(indoor_df_hourly, outdoor_df_hourly, ['aqi', 'pm10', 'pm25'], all_figs)

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.markdown("<h3 style='font-size:30px; text-align:left; font-weight:bold;'>Hourly Average Heat Index</h3>", unsafe_allow_html=True)
                    st.markdown("<br>", unsafe_allow_html=True)
                    plot_hourly_heat_index_chart(indoor_df_hourly, outdoor_df_hourly, all_figs)

                else:
                    st.warning("No data found for the given Device ID and selected month.")

                # Generate seasonal line chart using all-year data
                if indoor_rows_year:
                    indoor_df_year = pd.DataFrame(indoor_rows_year, columns=["datetime", "pm25", "pm10", "aqi", "co2", "voc", "temp", "humidity"])
                    indoor_df_year['datetime'] = pd.to_datetime(indoor_df_year['datetime'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
                    indoor_df_year.set_index('datetime', inplace=True)

                    # Check if the device ID belongs to residential buildings
                    if device_id in residential_ids:
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("<h3 style='font-size:30px; text-align:left; font-weight:bold;'>Seasonal Line Chart for Residential Buildings</h3>", unsafe_allow_html=True)
                        st.markdown("<br>", unsafe_allow_html=True)
                        plot_residential_seasonal_line_chart(indoor_df_year, ['aqi', 'pm10', 'pm25'], year, all_figs)
                    else:
                        st.info("Seasonal line charts are only available for residential buildings.")
                else:
                    st.warning("No yearly data found for the selected Device ID.")
                
                if all_figs:
                    pdf_data = create_pdf_from_figs(all_figs)
                    st.download_button(
                        label="📄 Download All Charts as PDF",
                        data=pdf_data,
                        file_name="AirQualityCharts.pdf",
                        mime="application/pdf"
                    )


            except mysql.connector.Error as e:
                st.error(f"Database error: {e}")
            except Exception as e:
                st.error(f"An unexpected error occurred: {e}")
            finally:
                # Ensure the database connection is closed
                if 'conn' in locals() and conn.is_connected():
                    cursor.close()
                    conn.close()