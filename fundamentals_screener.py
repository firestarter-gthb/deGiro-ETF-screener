import pandas as pd
import yfinance as yf
import numpy as np
import time
from datetime import datetime
import os

def get_max_drawdown(prices):
    roll_max = prices.cummax()
    drawdown = prices / roll_max - 1.0
    return drawdown.min()

def main():
    print("===================================================")
    print("DEGIRO ETF Fundamentals & Risk Screener Starten...")
    print("===================================================\n")
    
    print("1. DEGIRO ETF's inlezen...")
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
    print("\n2. Fundamentals en Risico data ophalen (1 jaar historie)...")
    
    results = []
    succes_count = 0
    fail_count = 0
    risk_free_rate = 0.02 # Aanname 2% risicovrije rente voor Sharpe
    
    for i, t in enumerate(tickers):
        try:
            row_data = etf_dict[t]
            ticker_obj = yf.Ticker(t)
            
            # Haal 1 jaar geschiedenis op voor risk metrics
            hist = ticker_obj.history(period='1y')
            if len(hist) < 200:
                fail_count += 1
                continue
                
            prices = hist['Close']
            current_price = prices.iloc[-1]
            
            # Risk Metrics
            daily_returns = prices.pct_change().dropna()
            volatility = daily_returns.std() * np.sqrt(252) # Geannualiseerd
            annual_return = (prices.iloc[-1] / prices.iloc[0]) - 1.0
            
            sharpe_ratio = (annual_return - risk_free_rate) / volatility if volatility > 0 else 0
            max_dd = get_max_drawdown(prices)
            
            # Fundamentals Metrics (kunnen leeg zijn)
            info = ticker_obj.info
            aum = info.get('totalAssets', np.nan)
            pe = info.get('trailingPE', np.nan)
            if pe is None: pe = np.nan
            
            results.append({
                'isin': row_data['isin'],
                'yf_ticker': t,
                'name': row_data['name'],
                'currency': row_data['currency'],
                'Price': round(current_price, 2),
                'Volatiliteit (%)': round(volatility * 100, 2),
                'Max Drawdown (%)': round(max_dd * 100, 2),
                'Sharpe Ratio': round(sharpe_ratio, 2),
                'Rendement 1J (%)': round(annual_return * 100, 2),
                'P/E Ratio': round(pe, 2) if not pd.isna(pe) else np.nan,
                'Assets (Mln)': round(aum / 1000000, 1) if not pd.isna(aum) else np.nan
            })
            succes_count += 1
            
        except Exception as e:
            fail_count += 1
            
        if (i+1) % 10 == 0:
            print(f"[{i+1}] Verwerkt... (Laatste: {t}, Sharpe: {sharpe_ratio if 'sharpe_ratio' in locals() else 'N/A'})")
            
        if (i+1) % 50 == 0 and len(results) > 0:
            # Tussentijds opslaan
            pd.DataFrame(results).to_csv('fundamentals_screener_progress.csv', index=False, sep='|')
            
        time.sleep(0.1) # Zeer lichte sleep

    print(f"\n3. Resultaten verwerken... ({succes_count} succes, {fail_count} gefaald/te weinig data)")
    
    if len(results) > 0:
        df_res = pd.DataFrame(results)
        
        # We maken een simpele score: Hoge Sharpe is goed, Diepe drawdown is slecht
        # Score = Sharpe - (Max DD * 2). (Aangezien max DD negatief is, wordt dit +)
        df_res['Score'] = df_res['Sharpe Ratio'] + (df_res['Max Drawdown (%)'] / 100 * 2)
        
        # Rank op beste score
        df_res['Rank'] = df_res['Score'].rank(ascending=False, method='min').astype(int)
        
        df_res = df_res.sort_values('Rank')
        df_res.to_csv('fundamentals_screener_result_final.csv', index=False, sep='|')
        print("Opgeslagen als 'fundamentals_screener_result_final.csv'")
    else:
        print("Geen data om op te slaan.")

if __name__ == "__main__":
    main()
