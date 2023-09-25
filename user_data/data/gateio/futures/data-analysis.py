import pandas as pd

df_gateio = pd.read_feather("BTC_USDT_USDT-1m-futures.feather")

print(df_gateio.columns)
print(df_gateio.head())