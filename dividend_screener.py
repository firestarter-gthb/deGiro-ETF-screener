import pandas as pd
import yfinance as yf
from datetime import datetime, timedelta
import numpy as np
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.getLogger('yfinance').setLevel(logging.CRITICAL)

def run_dividend_screener():
    print("1. DEGIRO ETF's inlezen...")
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

    if 'yf_ticker' not in unique_etfs.columns:
        exchange_suffix_map = {
            '194': '.DE', '196': '.DE', '200': '.L', '570': '.AS', 
            '608': '.SW', '710': '.PA', '947': '.MI'
        }
        def get_yf_ticker(row):
            if str(row.get('isin')).strip() == 'DE000A0Q4R85':
                return '4BRZ.DE'
            exch = str(row['exchangeId'])
            return str(row['symbol']).strip() + exchange_suffix_map.get(exch, '') if exch in exchange_suffix_map else None
        unique_etfs['yf_ticker'] = unique_etfs.apply(get_yf_ticker, axis=1)

    unique_etfs = unique_etfs.dropna(subset=['yf_ticker']).copy()
    unique_etfs = unique_etfs.drop_duplicates(subset=['yf_ticker'])
    
    tickers = unique_etfs['yf_ticker'].tolist()
    etf_dict = unique_etfs.set_index('yf_ticker').to_dict('index')

    print(f"-> {len(tickers)} unieke tickers klaar voor verwerking.")
    print("\n2. Data en dividenden ophalen...")
    
    results = []
    succes_count = 0
    fail_count = 0
    
    # Voor debugging / speedup kunnen we limiten, maar in de repo doen we alle tickers.
    # tickers = tickers[:20]

    for t in tickers:
        try:
            ticker_obj = yf.Ticker(t)
            hist = ticker_obj.history(period="3y")
            
            if hist.empty:
                fail_count += 1
                continue
                
            current_price = hist['Close'].iloc[-1]
            if pd.isna(current_price) or current_price == 0:
                fail_count += 1
                continue
                
            if 'Dividends' not in hist.columns:
                fail_count += 1
                continue
                
            divs = hist['Dividends']
            divs = divs[divs > 0]
            
            if divs.empty:
                continue
                
            one_year_ago = hist.index[-1] - pd.DateOffset(years=1)
            ttm_divs = divs[divs.index >= one_year_ago]
            ttm_div_sum = ttm_divs.sum()
            
            ttm_yield = (ttm_div_sum / current_price) * 100
            
            if ttm_yield == 0:
                continue
                
            two_years_ago = hist.index[-1] - pd.DateOffset(years=2)
            three_years_ago = hist.index[-1] - pd.DateOffset(years=3)
            
            div_year1_sum = ttm_div_sum
            div_year2_sum = divs[(divs.index >= two_years_ago) & (divs.index < one_year_ago)].sum()
            div_year3_sum = divs[(divs.index >= three_years_ago) & (divs.index < two_years_ago)].sum()
            
            growth_3y = np.nan
            if div_year3_sum > 0:
                # Jaarlijkse groei schatting over 3 jaar (CAGR-achtig of simpele %)
                growth_3y = ((div_year1_sum / div_year3_sum) ** (1/2) - 1) * 100
                
            g_score = growth_3y if not np.isnan(growth_3y) else 0
            score = ttm_yield + max(min(g_score, 5), -5) # Cap growth invloed
            
            row_data = etf_dict[t]
            
            results.append({
                'yf_ticker': t,
                'name': row_data.get('name', ''),
                'price': round(current_price, 2),
                'Yield (%)': round(ttm_yield, 2),
                'Growth 3y (%)': round(growth_3y, 2) if not np.isnan(growth_3y) else np.nan,
                'Score': round(score, 2),
                'Divs TTM': len(ttm_divs),
                'Currency': row_data.get('currency', '')
            })
            succes_count += 1
            
            if succes_count % 10 == 0:
                print(f"[{succes_count}] Verwerkt... (Laatste: {t}, Yield: {ttm_yield:.2f}%)")

        except Exception as e:
            fail_count += 1
            pass
            
    print(f"\n3. Resultaten verwerken... ({succes_count} succes, {fail_count} gefaald/geen dividend)")
    
    if not results:
        print("Geen dividend ETF's gevonden.")
        return
        
    df_res = pd.DataFrame(results)
    df_res = df_res.sort_values(by='Score', ascending=False)
    
    # Filter onzin yields (>20%) eruit
    df_res = df_res[df_res['Yield (%)'] < 20.0]
    
    df_res.to_csv('dividend_screener_result_final.csv', index=False, sep='|')
    print(f"Opgeslagen als 'dividend_screener_result_final.csv'")

if __name__ == "__main__":
    run_dividend_screener()
