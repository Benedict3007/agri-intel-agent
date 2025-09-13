import requests
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://agridata.ec.europa.eu/extensions/DataPortal/home.html"
}

today_date = datetime.now().strftime('%Y-%m-%d')
base_url = f"https://www.ec.europa.eu/agrifood/api/cereal/prices?&begin_date=2020-01-01&end_date={today_date}"

print(f"Requesting data from: {base_url}")

try:
    response = requests.get(url=base_url, headers=HEADERS)
    response.raise_for_status()

    output_file = "api_output.csv"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(response.text)

    print(f"\n Success! Raw data saved to '{output_file}'")
except requests.exceptions.RequestException as e:
    print(f"\n Error: Failed to fetch data. {e}")