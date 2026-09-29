import pandas as pd
import os

def main():
    print("Inlezen van degiro_etfs.csv...")
    try:
        df = pd.read_csv('degiro_etfs.csv')
    except FileNotFoundError:
        print("Fout: degiro_etfs.csv niet gevonden.")
        return

    if os.path.exists('momentum_screener_result_final.csv'):
        print("Vergelijken met momentum_screener_result_final.csv...")
        final_df = pd.read_csv('momentum_screener_result_final.csv', sep='|')
        final_isins = set(final_df['isin'].dropna().tolist())
        df['download'] = df['isin'].apply(lambda x: 1 if x in final_isins else 0)
        
        count_1 = (df['download'] == 1).sum()
        count_0 = (df['download'] == 0).sum()
        print(f"Gevonden: {count_1} ETFs om te downloaden, {count_0} overgeslagen.")
    else:
        print("Geen momentum_screener_result_final.csv gevonden, alles wordt op 1 gezet.")
        df['download'] = 1

    df.to_csv('degiro_etfs_download_list.csv', index=False)
    print("Opgeslagen als degiro_etfs_download_list.csv!")

if __name__ == "__main__":
    main()
