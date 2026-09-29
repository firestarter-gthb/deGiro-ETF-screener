import pandas as pd
import os

# Dezelfde exchange suffix map als in momentum_screener.py
EXCHANGE_SUFFIX_MAP = {
    '194': '.DE', '196': '.DE', '200': '.L', '570': '.AS',
    '608': '.SW', '710': '.PA', '947': '.MI'
}

def get_yf_ticker(row):
    exch = str(row['exchangeId'])
    if exch in EXCHANGE_SUFFIX_MAP:
        return str(row['symbol']).strip() + EXCHANGE_SUFFIX_MAP[exch]
    return None

def main():
    print("Inlezen van degiro_etfs.csv...")
    try:
        df = pd.read_csv('degiro_etfs.csv')
    except FileNotFoundError:
        print("Fout: degiro_etfs.csv niet gevonden.")
        return

    # Genereer yf_ticker voor elke rij (zelfde logica als momentum_screener.py)
    df['yf_ticker'] = df.apply(get_yf_ticker, axis=1)

    if os.path.exists('momentum_screener_result_final.csv'):
        print("Vergelijken met momentum_screener_result_final.csv op yf_ticker...")
        final_df = pd.read_csv('momentum_screener_result_final.csv', sep='|')
        
        # Match op exacte yf_ticker — dit zijn bewezen werkende tickers
        known_good_tickers = set(final_df['yf_ticker'].dropna().tolist())
        
        df['download'] = df['yf_ticker'].apply(lambda t: 1 if t in known_good_tickers else 0)
        
        count_1 = (df['download'] == 1).sum()
        count_0 = (df['download'] == 0).sum()
        print(f"Bewezen werkende tickers: {count_1} om te downloaden, {count_0} overgeslagen.")
    else:
        print("Geen momentum_screener_result_final.csv gevonden, alles wordt op 1 gezet.")
        df['download'] = 1

    df.to_csv('degiro_etfs_download_list.csv', index=False)
    print("Opgeslagen als degiro_etfs_download_list.csv!")

if __name__ == "__main__":
    main()
