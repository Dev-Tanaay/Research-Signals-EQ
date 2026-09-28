import pandas as pd
import requests
import zipfile
import io

from concurrent.futures import ThreadPoolExecutor, as_completed

def download_fno_reports(date_str: str):
    formatted_date = pd.to_datetime(date_str).strftime("%d-%b-%Y").upper()
    file_date = pd.to_datetime(date_str).strftime("%d%m%Y")

    url = (
        "https://www.nseindia.com/api/reports?"
        "archives=%5B%7B%22name%22%3A%22F%26O%20-%20Market%20Activity%20Report%22%2C"
        "%22type%22%3A%22archives%22%2C%22category%22%3A%22derivatives%22%2C"
        "%22section%22%3A%22equity%22%7D%5D&"
        f"date={formatted_date}&type=equity&mode=single"
    )

    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
    }

    try:
        session.get("https://www.nseindia.com", headers=headers, timeout=10)
        response = session.get(url, headers=headers, timeout=20)

        if response.status_code != 200:
            print(f"[{date_str}] HTTP Error: {response.status_code}")
            return None, None

        if "zip" not in response.headers.get("Content-Type", ""):
            print(f"[{date_str}] Expected ZIP but received different content.")
            return None, None

        with zipfile.ZipFile(io.BytesIO(response.content)) as z:
            csv_filename = next(
                (f for f in z.namelist() if f == f"futstk{file_date}.csv"), None
            )

            if not csv_filename:
                print(f"[{date_str}] No CSV file found inside ZIP.")
                return None, None

            with z.open(csv_filename) as f:
                raw_df = pd.read_csv(
                    f, header=None, names=range(30), engine="python"
                )

        return raw_df, formatted_date

    except Exception as e:
        print(f"[{date_str}] Download Error: {e}")
        return None, None

output = []
trading_days = pd.read_csv("trading_days.csv")
symbol_change = pd.read_csv("symbol_change.csv")
symbol_change["date"] = pd.to_datetime(symbol_change["date"]).dt.strftime("%Y-%m-%d")
symbol_change = symbol_change[(symbol_change["date"] >= "2024-01-01") & (symbol_change["date"] <= "2024-12-31")]
symbol_change = symbol_change[["prev_symbol", "new_symbol"]]
symbol_change = dict(zip(symbol_change["prev_symbol"],symbol_change["new_symbol"]))
failed_dates = []

with ThreadPoolExecutor(max_workers=3) as executor:
    future_to_date = {
        executor.submit(download_fno_reports, date_str): date_str
        for date_str in trading_days["date"].tolist()
    }

    for future in as_completed(future_to_date):
        date_str = future_to_date[future]
        try:
            raw_df, date = future.result()
            if raw_df is None:
                print(f"FAILED: {date_str}")
                continue
            raw_df = raw_df.iloc[2:, :4].copy()
            raw_df.columns = ["S No","Symbol","Traded Value","No of Contracts"]
            for col in ["Symbol", "S No", "Traded Value", "No of Contracts"]:
                raw_df[col] = raw_df[col].str.strip()
            raw_df["Date"] = pd.to_datetime(date)
            raw_df["Symbol"] = raw_df["Symbol"].replace(symbol_change)
            output.append(raw_df)
        except Exception as e:
            print(f"FAILED: {date_str} -> {e}")
            failed_dates.append(date_str)

if output:
    result = pd.concat(output, ignore_index=True)
    result = result.sort_values(["Date", "Symbol"])
    result.to_csv("daily_stocks.csv", index=False)

pd.DataFrame({"Date": failed_dates}).to_csv("failed_dates.csv",index=False)