import tushare as ts
import pandas as pd
import os

TOEKN_PATH = os.path.expanduser("~/.tushare.token")

with open(TOEKN_PATH, "r") as f:
    token = f.read().strip()
    ts.set_token(token=token)
    pro = ts.pro_api(token=token)

code = "601398.SH"
df: pd.DataFrame = ts.pro_bar(ts_code=code, adj='qfq', start_date='20220101', end_date='20240308')
df.to_csv("data.csv")