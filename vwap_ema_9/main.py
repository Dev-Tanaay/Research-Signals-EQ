import pandas as pd 

def signal_generation():
    daily_eod_data_df = pd.read_csv("fno_eod_data.csv") 
    daily_eod_data_df = daily_eod_data_df.sort_values(["symbol", "date"])
    daily_eod_data_df["prev_close"] = daily_eod_data_df.groupby("symbol")["close"].shift(1)
    daily_eod_data_df["tr"] = pd.concat([
        daily_eod_data_df["high"] - daily_eod_data_df["low"],
        (daily_eod_data_df["high"] - daily_eod_data_df["prev_close"]).abs(),
        (daily_eod_data_df["low"] - daily_eod_data_df["prev_close"]).abs()
    ], axis=1).max(axis=1)

    daily_eod_data_df["atr14"] = (
        daily_eod_data_df.groupby("symbol")["tr"]
        .transform(lambda x: x.ewm(
            alpha=1/14,
            adjust=False
        ).mean())
    )

    daily_eod_data_df["norm_move"] = (daily_eod_data_df["open"] - daily_eod_data_df["prev_close"]) / daily_eod_data_df["atr14"]
    daily_eod_data_df["rank_desc"] = daily_eod_data_df.groupby("date")["norm_move"].rank(ascending=False, method="first")
    daily_eod_data_df["rank_asc"]  = daily_eod_data_df.groupby("date")["norm_move"].rank(ascending=True,  method="first")
    daily_eod_data_df["side"] = 0
    daily_eod_data_df.loc[daily_eod_data_df["rank_desc"] <= 5, "side"] = 1
    daily_eod_data_df.loc[daily_eod_data_df["rank_asc"]  <= 5, "side"] = -1
    daily_eod_data_df = daily_eod_data_df[daily_eod_data_df["side"]!=0]
    daily_eod_data_df = daily_eod_data_df.sort_values(["date"])
    daily_eod_data_df = daily_eod_data_df[daily_eod_data_df["date"]>="2024-01-01"]
    daily_eod_data_df.to_csv("entry_signals.csv",index=False)

if __name__ == "__main__":
    # signal_generation()
    df = pd.read_csv("daily_fno_stocks.csv")
    df = df[["symbol","instrument_token"]].drop_duplicates()
    df.to_csv("symbols_list.csv",index=False)
