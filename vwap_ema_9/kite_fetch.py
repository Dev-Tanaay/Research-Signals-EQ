import pandas as pd
import requests

def get_historical_data_kite(auth_token,instr_token,sec,from_date,to_date,interval):
    print(f"Fetching historical data for {sec} from {from_date} to {to_date}")
    url = (
        f"https://api.kite.trade/instruments/historical/"
        f"{instr_token}/{interval}?from={from_date}&to={to_date}"
    )
    headers = {
        "X-Kite-Version": "3",
        "Authorization": auth_token
    }
    for attempt in range(2):
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                res_json = response.json()
                res_status = res_json["status"]
                if res_status == "success":
                    res_data = res_json["data"]["candles"]

                    df = pd.DataFrame(res_data,columns=["Datetime","Open","High","Low","Close","Volume"])

                    df["Datetime"] = pd.to_datetime(df["Datetime"])
                    df = df.drop_duplicates(subset=["Datetime"],keep="first")

                    df["Date"] = df["Datetime"].dt.strftime("%Y-%m-%d")
                    df["symbol"] = sec
                    df = df.rename(columns={
                        "Datetime":"datetime",
                        "Open":"open",
                        "High":"high",
                        "Low":"low",
                        "Close":"close",
                        "Volume": "volume",
                        "Date":"date"
                    })
                    return df

                error = f"Request Failed: {res_status}"

            else:
                error = f"Request Failed: HTTP {response.status_code}"

        except Exception as e:
            error = f"An error occurred: {e}"

        if attempt <= 1:
            print(f"{sec}: {error}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
        else:
            print(f"{sec}: {error}")
            print(f"{sec}: Retry failed. Returning None.")

    return None

if __name__ == "__main__":
    stocks_df = pd.read_csv("daily_fno_stocks.csv")
    stocks_df = stocks_df[["symbol", "instrument_token"]].drop_duplicates()
    stocks = dict(zip(stocks_df["symbol"], stocks_df["instrument_token"]))
    auth_token = 'token gzr8ntx4qcftjxm7:MaCU9m3aUp9CgEdjEVAbZ33aerNPEQur'
    output = []
    for symb,instr_token in stocks.items():
        data_final = get_historical_data_kite(auth_token,instr_token,symb,"2023-10-01","2024-12-31","day")
        output.append(data_final)
    df = pd.concat(output,ignore_index = True)
    df.to_csv("fno_eod_data.csv",index=False)
