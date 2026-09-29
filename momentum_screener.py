import pandas as pd
import yfinance as yf
from datetime import datetime
import numpy as np
import time
import re
import requests
import logging
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Onderdruk rommelige yfinance waarschuwingen over mogelijk gedenoteerde tickers
logging.getLogger('yfinance').setLevel(logging.CRITICAL)
logging.getLogger('urllib3').setLevel(logging.CRITICAL)

def run_momentum_screener():
    # 1. Rate-limit bestendige sessie opzetten
    session = requests.Session()
    retry = Retry(
        total=5, 
        backoff_factor=1, 
        status_forcelist=[ 429, 500, 502, 503, 504 ]
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    print("1. DEGIRO ETF's inlezen en ontdubbelen...")
    
    import os
    if os.path.exists('degiro_etfs_download_list.csv'):
        df = pd.read_csv('degiro_etfs_download_list.csv')
        if 'download' in df.columns:
            df = df[df['download'] == 1]
    else:
        df = pd.read_csv('degiro_etfs.csv')
        
    df['is_eur'] = df['currency'] == 'EUR'
    df = df.sort_values(by=['is_eur', 'exchangeId'], ascending=[False, True])
    unique_etfs = df.drop_duplicates(subset=['isin']).copy()

    # Gebruik de yf_ticker kolom als die al in het bestand zit (bewezen werkende tickers),
    # anders opnieuw berekenen vanuit exchange suffix
    if 'yf_ticker' not in unique_etfs.columns:
        exchange_suffix_map = {
            '194': '.DE', '196': '.DE', '200': '.L', '570': '.AS', 
            '608': '.SW', '710': '.PA', '947': '.MI'
        }
        def get_yf_ticker(row):
            exch = str(row['exchangeId'])
            return str(row['symbol']).strip() + exchange_suffix_map.get(exch, '') if exch in exchange_suffix_map else None
        unique_etfs['yf_ticker'] = unique_etfs.apply(get_yf_ticker, axis=1)

    unique_etfs = unique_etfs.dropna(subset=['yf_ticker']).copy()

    tickers = unique_etfs['yf_ticker'].tolist()
    print(f"-> {len(tickers)} unieke tickers klaar voor verwerking.")

    print("\n2. Data ophalen (in chunks van 8 om rate limits te spreiden en het te versnellen)...")
    results = []
    current_year = str(datetime.now().year)
    succes_count = 0
    fail_count = 0

    chunk_size = 8
    
    # Maak een dictionary aan van de tickers naar hun row-data, zodat we ze makkelijk kunnen opzoeken
    unique_etfs = unique_etfs.drop_duplicates(subset=['yf_ticker'])
    etf_dict = unique_etfs.set_index('yf_ticker').to_dict('index')

    for i in range(0, len(tickers), chunk_size):
        chunk = tickers[i:i+chunk_size]
        
        try:
            # We sturen 4 requests tegelijk (threads=True) via de veilige session
            hist = yf.download(chunk, period='1y', threads=True, session=session, progress=False)
            
            for t in chunk:
                if isinstance(hist.columns, pd.MultiIndex):
                    if t not in hist['Close'].columns:
                        fail_count += 1
                        continue
                    df_t = hist.xs(t, level=1, axis=1).dropna()
                else:
                    if chunk[0] != t or hist.empty:
                        fail_count += 1
                        continue
                    df_t = hist.dropna()
                    
                closes = df_t['Close']
                
                if len(closes) < 200:
                    fail_count += 1
                    continue
                    
                current_price = closes.iloc[-1].item() if hasattr(closes.iloc[-1], 'item') else closes.iloc[-1]
                last_day = closes.iloc[-2].item() if hasattr(closes.iloc[-2], 'item') else closes.iloc[-2]
                
                ret_1m = (current_price / closes.iloc[-22].item()) - 1
                ret_3m = (current_price / closes.iloc[-64].item()) - 1
                ret_1y = (current_price / closes.iloc[0].item()) - 1
                
                ytd_prices = closes[current_year:]
                ret_ytd = (current_price / ytd_prices.iloc[0].item()) - 1 if not ytd_prices.empty else np.nan
                
                avg_200 = closes.tail(200).mean().item()
                dist_200 = (current_price / avg_200) - 1
                
                # Z-score berekening: afstand van 20MA in standaarddeviaties
                closes_20 = closes.tail(20)
                avg_20 = closes_20.mean().item()
                std_20 = closes_20.std().item()
                
                dist_20 = (current_price - avg_20) / std_20 if std_20 else np.nan
                
                # Filter extreme bugs vanuit Yahoo
                if ret_1m > 5.0 or ret_1y > 5.0 or ret_ytd > 5.0:
                    fail_count += 1
                    continue
                    
                # Filter "spook-data" (illiquide ETFs of kapotte Yahoo feeds met flatline koersen)
                if closes.iloc[-22].item() == closes.iloc[-64].item() == closes.iloc[0].item():
                    fail_count += 1
                    continue
                    
                row_data = etf_dict[t]
                results.append({
                    'name': row_data['name'],
                    'isin': row_data['isin'],
                    'yf_ticker': t,
                    'currency': row_data['currency'],
                    'totalExpenseRatio': row_data['totalExpenseRatio'],
                    'Current price': current_price,
                    'Last day': last_day,
                    'Last month': ret_1m,
                    'Last 3 months': ret_3m,
                    'Last year': ret_1y,
                    'YTD Performance': ret_ytd,
                    '200 avg': dist_200,
                    'Z-score 20MA': dist_20
                })
                succes_count += 1
                
        except Exception as e:
            fail_count += len(chunk)
            
        # Voortgang printen en een tiny sleep na elke chunk van 4 (ongeveer 2 requests per seconde)
        if (i + chunk_size) % 100 == 0 or (i + chunk_size) >= len(tickers):
            print(f"  ... {min(i + chunk_size, len(tickers))} van de {len(tickers)} ETF's verwerkt ...")
            
        time.sleep(1.0) # 1s rust na elke 8 downloads (gefilterde lijst = minder rate-limit risico)

    print(f"\nKlaar! {succes_count} gelukt, {fail_count} overgeslagen (onvoldoende data/fout bij Yahoo).")

    print("\n3. Ranks berekenen en exporteren...")
    final_df = pd.DataFrame(results)
    if len(final_df) > 0:
        final_df['Rank 1M'] = final_df['Last month'].rank(ascending=False, method='min')
        final_df['Rank 3M'] = final_df['Last 3 months'].rank(ascending=False, method='min')
        final_df['Rank 1 Jaar'] = final_df['Last year'].rank(ascending=False, method='min')
        final_df['Rank 200 M'] = final_df['200 avg'].rank(ascending=False, method='min')
        
        # Sub-scores berekenen
        score_shortterm = (final_df['Rank 1M'] * 0.15) + (final_df['Rank 3M'] * 0.40)
        score_longterm = (final_df['Rank 1 Jaar'] * 0.25) + (final_df['Rank 200 M'] * 0.20)
        
        # Sub-scores ranken (laagste score krijgt rank 1)
        final_df['Rank shortterm'] = score_shortterm.rank(ascending=True, method='min').astype(int)
        final_df['Rank longterm'] = score_longterm.rank(ascending=True, method='min').astype(int)

        # Gewogen Total score berekend
        final_df['Total score'] = score_shortterm + score_longterm
        
        final_df = final_df.sort_values(by='Total score', ascending=True).reset_index(drop=True)
        final_df['Rank all'] = range(1, len(final_df) + 1)
        
        def get_category(name):
            n = str(name).lower()
            if re.search(r'\b(tech|artificial intelligence|ai|cyber|digital|cloud|nasdaq|metaverse|semiconductor|memory chips|software|robotics)\b', n): return 'Technology'
            if re.search(r'\b(bio|genomics|health|healthcare|medical|pharma)\b', n): return 'Healthcare / Biotech'
            if re.search(r'\b(commodity|commodities|energy|oil|gold|metal|metals|mining|agriculture|water|clean energy|bioenergy|resources)\b', n): return 'Commodity / Energy'
            if re.search(r'\b(bank|banks|financial|financials|insurance)\b', n): return 'Financials'
            if re.search(r'\b(real estate|property|reit|reits)\b', n): return 'Real Estate'
            if re.search(r'\b(esg|sri|climate|socially responsible|clean|green|transition)\b', n): return 'ESG / Sustainable'
            if re.search(r'\b(bond|bonds|treasury|corporate|high yield|fixed income|gilt|sovereign)\b', n): return 'Bonds / Fixed Income'
            if re.search(r'\b(value|growth|momentum|quality|dividend|cash cow|low volatility|yield|factor)\b', n): return 'Factor / Smart Beta'
            if re.search(r'\b(japan|jpy)\b', n): return 'Region: Japan'
            if re.search(r'\b(emerging|em|india|china|taiwan|asia|brazil|korea)\b', n): return 'Region: Emerging Markets / Asia'
            if re.search(r'\b(europe|euro|uk|germany|france|stoxx|dax|ftse 100)\b', n): return 'Region: Europe'
            if re.search(r'\b(usa|us|s&p 500|dow jones|russell)\b', n): return 'Region: US'
            if re.search(r'\b(world|global|all country|acwi)\b', n): return 'Global / Broad'
            return 'Other'
            
        final_df['Category'] = final_df['name'].apply(get_category)
        
        def get_reinvest(name):
            n = str(name).lower()
            if re.search(r'(?<![a-z])(acc|accumulating|accum|accu|1c|2c|3c|4c)(?![a-z])', n): return 'Acc'
            if re.search(r'(usdacc|euracc|hgdacc|gbpacc|chfacc)', n): return 'Acc'
            if re.search(r'\b(c)\b$', n): return 'Acc'
            if re.search(r'\b(a)\b$', n): return 'Acc'
            if re.search(r'\(\s*acc\s*\)', n): return 'Acc'
            if re.search(r'\(\s*a\s*\)', n): return 'Acc'
            if re.search(r'\(\s*c\s*\)', n): return 'Acc'

            if re.search(r'(?<![a-z])(dist|distr|distributing|distribution|inc|income|dis|1d|2d|3d|4d)(?![a-z])', n): return 'Distr'
            if re.search(r'(usddist|eurdist|hgddist|gbpdist|chfdist)', n): return 'Distr'
            if re.search(r'\b(d)\b$', n): return 'Distr'
            if re.search(r'\(\s*dist\s*\)', n): return 'Distr'
            if re.search(r'\(\s*d\s*\)', n): return 'Distr'
            if re.search(r'\(\s*inc\s*\)', n): return 'Distr'

            return 'Unknown'
            
        final_df['reinvest'] = final_df['name'].apply(get_reinvest)
        
        output_cols = ['Rank all', 'Rank shortterm', 'Rank longterm', 'name', 'Category', 'reinvest', 'isin', 'yf_ticker', 'currency', 'totalExpenseRatio', 
                       'Current price', 'Last day', 'Last month', 'Last 3 months', 'Last year', 
                       'YTD Performance', '200 avg', 'Z-score 20MA', 'Rank 1M', 'Rank 3M', 'Rank 1 Jaar', 'Rank 200 M', 'Total score']
        final_df = final_df[[c for c in output_cols if c in final_df.columns]]
        
        num_cols = ['totalExpenseRatio', 'Current price', 'Last day', 'Last month', 'Last 3 months', 'Last year', 'YTD Performance', '200 avg', 'Z-score 20MA', 'Rank 1M', 'Rank 3M', 'Rank 1 Jaar', 'Rank 200 M', 'Total score']
        for c in num_cols:
            if c in final_df.columns:
                final_df[c] = final_df[c].apply(lambda x: str(x).replace('.', ',') if pd.notnull(x) else '')
                
        final_df.to_csv('momentum_screener_result_final.csv', index=False, sep='|')
        print('✅ Bestand succesvol opgeslagen als momentum_screener_result_final.csv!')

if __name__ == "__main__":
    run_momentum_screener()
