from ds_layout import apply_theme
import pandas as pd
from datetime import datetime
import os

def genereer_fundamentals_html(csv_pad='fundamentals_screener_result_final.csv', output_html='fundamentals_screener_dashboard.html'):
    if not os.path.exists(csv_pad):
        print(f"Fout: Kan {csv_pad} niet vinden.")
        return

    df = pd.read_csv(csv_pad, sep='|')
    current_time = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    
    # HTML opbouwen
    html = f"""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <title>Fundamentals & Risico Dashboard</title>
    <style>
        body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 40px; background: #f4f6f9; color: #333; }}
        h1 {{ color: #2c3e50; }}
        .header-info {{ margin-bottom: 20px; color: #7f8c8d; }}
        table {{ border-collapse: collapse; width: 100%; background: #fff; box-shadow: 0 4px 6px rgba(0,0,0,0.1); font-size: 14px; }}
        th, td {{ padding: 12px 15px; text-align: left; border-bottom: 1px solid #eee; }}
        th {{ background: #34495e; color: white; cursor: pointer; }}
        th:hover {{ background: #2c3e50; }}
        tr:hover {{ background: #f1f1f1; }}
        .volatility-high {{ color: #e74c3c; font-weight: bold; }}
        .volatility-low {{ color: #27ae60; font-weight: bold; }}
        .drawdown-deep {{ color: #c0392b; }}
        .drawdown-safe {{ color: #2980b9; }}
        .sharpe-good {{ color: #27ae60; font-weight: bold; }}
        .value-good {{ color: #8e44ad; font-weight: bold; }}
    </style>
</head>
<body>
    <h1>📊 ETF Fundamentals & Risico Dashboard</h1>
    <div class="header-info">
        <p>Gefilterd op onderliggende waarde en wiskundig risico (1 jaar historie).</p>
        <p><em>Laatste update: {current_time}</em> | <em>Aantal ETF's: {len(df)}</em></p>
    </div>
    
    <table id="fundamentalsTable">
        <thead>
            <tr>
                <th>Rank</th>
                <th>Ticker</th>
                <th>Naam ETF</th>
                <th>Prijs</th>
                <th>GICS Sector L1</th>
                <th>GICS Sector L2</th>
                <th>Volatiliteit (%)</th>
                <th>Max Drawdown (%)</th>
                <th>Sharpe Ratio</th>
                <th>Rendement 1J (%)</th>
                <th>P/E Ratio</th>
                <th>Assets (Mln)</th>
            </tr>
        </thead>
        <tbody>
"""

    for idx, row in df.iterrows():
        vol = row['Volatiliteit (%)']
        dd = row['Max Drawdown (%)']
        sharpe = row['Sharpe Ratio']
        pe = row['P/E Ratio']
        
        vol_class = "volatility-low" if vol < 15 else ("volatility-high" if vol > 25 else "")
        dd_class = "drawdown-safe" if dd > -10 else ("drawdown-deep" if dd < -25 else "")
        sharpe_class = "sharpe-good" if sharpe > 1.5 else ""
        pe_class = "value-good" if not pd.isna(pe) and pe < 15 else ""

        html += f"""            <tr>
                <td>#{row['Rank']}</td>
                <td><strong>{row['yf_ticker']}</strong></td>
                <td>{row['name']}</td>
                <td>€{row['Price']:.2f}</td>
                <td>{row.get('GICS Sector L1', '-')}</td>
                <td>{row.get('GICS Sector L2', '-')}</td>
                <td class="{vol_class}">{vol:.2f}%</td>
                <td class="{dd_class}">{dd:.2f}%</td>
                <td class="{sharpe_class}">{sharpe:.2f}</td>
                <td>{row['Rendement 1J (%)']:.2f}%</td>
                <td class="{pe_class}">{pe if not pd.isna(pe) else '-'}</td>
                <td>{row['Assets (Mln)'] if not pd.isna(row['Assets (Mln)']) else '-'}</td>
            </tr>
"""

    html += f"""        </tbody>
    </table>
    <script>
        // Eenvoudige sorteer logica
        const getCellValue = (tr, idx) => tr.children[idx].innerText || tr.children[idx].textContent;
        const comparer = (idx, asc) => (a, b) => ((v1, v2) => 
            v1 !== '' && v2 !== '' && !isNaN(v1.replace(/[^0-9.-]+/g,"")) && !isNaN(v2.replace(/[^0-9.-]+/g,"")) ? 
            v1.replace(/[^0-9.-]+/g,"") - v2.replace(/[^0-9.-]+/g,"") : v1.toString().localeCompare(v2)
            )(getCellValue(asc ? a : b, idx), getCellValue(asc ? b : a, idx));

        document.querySelectorAll('th').forEach(th => th.addEventListener('click', (() => {{
            const table = th.closest('table');
            const tbody = table.querySelector('tbody');
            Array.from(tbody.querySelectorAll('tr'))
                .sort(comparer(Array.from(th.parentNode.children).indexOf(th), this.asc = !this.asc))
                .forEach(tr => tbody.appendChild(tr) );
        }})));
    </script>
</body>
</html>"""

    with open(output_html, 'w', encoding='utf-8') as f:
        f.write(apply_theme(html, 'fundamentals'))
    print(f"HTML rapport gegenereerd: {output_html}")

if __name__ == "__main__":
    genereer_fundamentals_html()
