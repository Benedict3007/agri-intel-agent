import requests
import pandas as pd
import matplotlib.pyplot as plt
import os
import io
from datetime import datetime
from langchain.tools import tool

# --- Define a browser-like header ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://agridata.ec.europa.eu/extensions/DataPortal/home.html" 
}
# Output dir for charts
CHARTS_DIR = os.path.join("..", "..", "data", "charts")
os.makedirs(CHARTS_DIR, exist_ok=True)

@tool
def get_crop_price_data(crop_name: str) -> str:
    """
    Fetches historical price data for a given crop from the EU Agri-food Data Portal
    and returns it as a string-formatted DataFrame.
    
    Args: 
        crop_name (str): The name of the crop to fetch data for
    """
    print(f"Fetching price data for {crop_name}...")
    today_date = datetime.now().strftime('%Y-%m-%d')
    base_url = f"https://www.ec.europa.eu/agrifood/api/cereal/prices?&begin_date=2020-01-01&end_date={today_date}"
    
    try:
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text), engine='python', on_bad_lines='skip')

        # --- Data Cleaning ---
        df = df[['Year', 'Week', 'PriceEUR']]
        df.rename(columns={'PriceEUR': 'Price (EUR/tonne)'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Year'].astype(str) + df['Week'].astype(str) + '0', format='%Y%W%w')
        df = df.sort_values(by='Date').set_index('Date')

        print(f"Successfully fetched {len(df)} data points,")
        return df.tail().to_string()

    except requests.exceptions.RequestException as e:
        return f"Error fetching data from the API: {e}"
    except Exception as e:
        return f"An error occurred while processing the data: {e}"

@tool
def plot_crop_price_chart(crop_name: str) -> str:
    """
    Fetches crop price data and generates a plot, saving it to a file.

    Args:
        crop_name (str): The name of the crop to plot.
    
    Returns:
        str: A confirmation message with the path to the saved chart.
    """
    print(f"Plotting price chart for {crop_name}")

    today_date = datetime.now().strftime('%Y-%m-%d')
    base_url = f"https://www.ec.europa.eu/agrifood/api/cereal/prices?&begin_date=2020-01-01&end_date={today_date}"

    try:
        response = requests.get(base_url, headers=HEADERS)
        response.raise_for_status()

        df = pd.read_csv(io.StringIO(response.text), engine='python', on_bad_lines='skip')

        # --- Data Cleaning ---
        df = df[['Year', 'Week', 'PriceEUR']]
        df.rename(columns={'PriceEUR': 'Price (EUR/tonne)'}, inplace=True)
        df['Date'] = pd.to_datetime(df['Year'].astype(str) + df['Week'].astype(str) + '0', format='%Y%W%w')
        df = df.sort_values(by='Date').set_index('Date')

        # --- Plotting Logic ---
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12,7))
        ax.plot(df.index, df['Price (EUR/tonne)'], marker='.', linestyle='-', markersize=4)
        ax.set_title(f'EU Soft Wheat Prices (2020-Present)', fontsize=16)
        ax.set_ylabel('Price (EUR / tonne)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)
        plt.tight_layout()

        # Save the plot to the charts dir
        chart_path = os.path.join(CHARTS_DIR, "soft_wheat_price_chart.png")
        plt.savefig(chart_path)
        plt.close(fig)

        print(f"Chart saved to {chart_path}")
        return f"Successfully generated and saved the price chart to '{chart_path}"

    except Exception as e:
        return f"An error occured while generating the chart: {e}"