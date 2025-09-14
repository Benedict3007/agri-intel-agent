import matplotlib
matplotlib.use('Agg')
import requests
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import os
from datetime import datetime
from langchain.tools import tool
from pathlib import Path

# --- Define a browser-like header ---
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
}

# Output dir for charts
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CHARTS_DIR = PROJECT_ROOT / "data" / "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)

def _fetch_and_process_data(product_name: str, member_state_code: str=None) -> pd.DataFrame:
    """Helper function to fetch, clean, and filter data from the API."""
    today_date = datetime.now().strftime('%Y-%m-%d')
    base_url = f"https://www.ec.europa.eu/agrifood/api/cereal/prices?&begin_date=2020-01-01&end_date={today_date}"

    # Optinal URL Parameters
    if product_name:
        # API expects product names with spaces encoded as %20
        formatted_product = product_name.replace(" ", "%20")
        base_url += f"&productNames={formatted_product}"
    if member_state_code:
        base_url += f"&memberStateCodes={member_state_code}"

    response = requests.get(base_url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()

    if not data:
        return pd.DataFrame()

    df = pd.DataFrame(data)

    # Convert price string to a number (removes '€' and converts to float)
    df['price'] = df['price'].replace({r'[€,]': ''}, regex=True).astype(float)
    # Convert data string to datetime objects for plotting
    df['endDate'] = pd.to_datetime(df['endDate'], format='%d/%m/%Y')

    # Group by date and calculate the average price for that week
    df_agg = df.groupby('endDate')['price'].mean().reset_index()
    df_agg = df_agg.sort_values(by='endDate')

    return df_agg

@tool
def get_crop_price_data(product_name: str, member_state_code: str=None) -> str:
    """
    Fetches historical price data for a specific crop, optionaly filtered by country code
    Use this to get the latest price figures.
    Args:
        product_name (str): The name of the crop (e.g., 'Feed Wheat')
        member_state_code (str, optional): The 2-letter country code (e.g., 'DE')
    """
    print(f"Fetching data for {product_name} in {member_state_code or 'all of EU'}")
    try:
        df = _fetch_and_process_data(product_name=product_name, member_state_code=member_state_code)
        if df.empty:
            return f"No data found for {product_name} in {member_state_code or 'the specified region'}."

        # Return the last 5 weeks of average prices
        return df.tail().to_string()
    except Exception as e:
        return f"An error occured: {e}"

@tool
def plot_crop_price_chart(product_name: str, member_state_code: str=None) -> str:
    """
    Generates a plot of historical prices for a specific crop, optionally filtered by country.
    Use this when a user asks for a 'chart', 'plot', or 'graph'.
    Args:
        product_name (str): The name of the crop (e.g., 'Feed Wheat')
        member_state_code (str, optional): The 2-letter country code (e.g., 'DE')
    """
    print(f"Plotting chart for {product_name} in {member_state_code or 'all of EU'}")
    try:
        df = _fetch_and_process_data(product_name=product_name, member_state_code=member_state_code)
        if df.empty:
            return f"No data found for {product_name} in {member_state_code or 'the specified region'}."
        
        plt.style.use('seaborn-v0_8-whitegrid')
        fig, ax = plt.subplots(figsize=(12,7))
        ax.plot(df['endDate'], df['price'], marker='.', linestyle='-', markersize=4)

        country = f" ({member_state_code})" if member_state_code else " (EU Average)"
        ax.set_title(f'{product_name.title()} Prices{country}', fontsize=16)
        ax.set_ylabel('Price (EUR / tonne)', fontsize=12)
        ax.set_xlabel('Date', fontsize=12)

        # Format the x-axis to show dates clearly
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate()

        plt.tight_layout()

        chart_filename = f"{product_name.replace(' ', '_')}_{member_state_code or 'EU'}_chart.png"
        chart_path = CHARTS_DIR / chart_filename
        plt.savefig(chart_path)
        plt.close(fig)

        print(f"Chart saved to {chart_path}")

        return f"Chart generated. You can view it at /charts/{chart_filename}"

    except Exception as e:
        return f"An error occurred: {e}"