import pandas as pd

df = pd.read_csv('degiro_etfs.csv')
print(f'Totaal rijen: {len(df)}')
print(f"Unieke ISINs: {df['isin'].nunique()}")
print(f"Unieke Symbolen (Tickers): {df['symbol'].nunique()}")
print(f"Aantal in EUR: {len(df[df['currency']=='EUR'])}")
