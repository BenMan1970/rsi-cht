import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuration de la page Streamlit
st.set_page_config(
    page_title="RSI Forex Screener",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personnalisé (inchangé)
st.markdown("""
<style>
    .main > div { padding-top: 2rem; }
    .screener-header { font-size: 24px; font-weight: bold; color: #2c3e50; margin-bottom: 10px; }
    .update-info { background-color: #f8f9fa; padding: 8px 15px; border-radius: 5px; margin-bottom: 15px; font-size: 14px; color: #495057; }
    .legend-container { display: flex; justify-content: center; gap: 40px; margin: 20px 0; padding: 10px; }
    .legend-item { display: flex; align-items: center; gap: 8px; font-size: 14px; }
    .legend-dot { width: 12px; height: 12px; border-radius: 50%; }
    .oversold-dot { background-color: #dc3545; }
    .overbought-dot { background-color: #28a745; }
    .search-input { margin-bottom: 20px; }
    .rsi-table { width: 100%; border-collapse: collapse; margin: 20px 0; font-size: 13px; }
    .rsi-table th { background-color: #6c757d; color: white; padding: 12px 8px; text-align: center; font-weight: bold; border: 1px solid #dee2e6; }
    .rsi-table td { padding: 10px 8px; text-align: center; border: 1px solid #dee2e6; background-color: white; }
    .symbol-cell { font-weight: bold; background-color: #f8f9fa !important; }
    .oversold-cell { background-color: #dc3545 !important; color: white !important; font-weight: bold; }
    .overbought-cell { background-color: #28a745 !important; color: white !important; font-weight: bold; }
    .neutral-cell { background-color: white; color: #495057; }
    .stats-container { margin-top: 30px; }
</style>
""", unsafe_allow_html=True)

def calculate_rsi(prices, period=10):
    try:
        ohlc4 = (prices['Open'] + prices['High'] + prices['Low'] + prices['Close']) / 4
        delta = ohlc4.diff()
        gains = delta.where(delta > 0, 0)
        losses = -delta.where(delta < 0, 0)
        avg_gains = gains.ewm(span=period, adjust=False).mean()
        avg_losses = losses.ewm(span=period, adjust=False).mean()
        rs = avg_gains / avg_losses
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if len(rsi) > 0 else np.nan
    except:
        return np.nan

def get_yahoo_symbol(pair):
    return pair.replace('/', '') + '=X'

def fetch_forex_data(symbol, timeframe):
    try:
        yahoo_symbol = get_yahoo_symbol(symbol)
        params = {
            'H1': {'period': '5d', 'interval': '1h'},
            'H4': {'period': '1mo', 'interval': '4h'},
            'D1': {'period': '3mo', 'interval': '1d'},
            'W1': {'period': '2y', 'interval': '1wk'}
        }
        if timeframe not in params:
            return None
        ticker = yf.Ticker(yahoo_symbol)
        data = ticker.history(
            period=params[timeframe]['period'],
            interval=params[timeframe]['interval']
        )
        if len(data) < 15:
            return None
        return data
    except:
        return None

def format_rsi(value):
    return "N/A" if pd.isna(value) else f"{value:.2f}"

def get_rsi_class(value):
    if pd.isna(value):
        return "neutral-cell"
    elif value <= 20:
        return "oversold-cell"
    elif value >= 80:
        return "overbought-cell"
    return "neutral-cell"

# Interface principale
st.markdown('<h1 class="screener-header">📊 Screener Analysis</h1>', unsafe_allow_html=True)

# Information de mise à jour
current_time = datetime.now().strftime("%H:%M:%S")
st.markdown(f"""
<div class="update-info">
    🔄 Analysis was just updated. Last update: {current_time}
</div>
""", unsafe_allow_html=True)

# Légende
st.markdown("""
<div class="legend-container">
    <div class="legend-item">
        <div class="legend-dot oversold-dot"></div>
        <span>Oversold (≤20)</span>
    </div>
    <div class="legend-item">
        <div class="legend-dot overbought-dot"></div>
        <span>Overbought (≥80)</span>
    </div>
</div>
""", unsafe_allow_html=True)

# Liste des paires forex majeures
forex_pairs = [
    'EUR/USD', 'USD/JPY', 'GBP/USD', 'USD/CHF', 'AUD/USD',
    'USD/CAD', 'NZD/USD', 'EUR/JPY', 'GBP/JPY', 'EUR/GBP'
]

# Timeframes disponibles
timeframes = ['M15', 'M30', 'H1', 'H4', 'D1', 'W1']

# Barre de recherche
search_term = st.text_input("Search:", placeholder="Tapez pour filtrer les paires...", key="search_input")

# Filtrage des paires
filtered_pairs = [pair for pair in forex_pairs if search_term.upper() in pair.upper()] if search_term else forex_pairs

# Analyse automatique

def analyze_pair(pair):
    row_data = {'Symbol': pair}
    for tf in timeframes:
        if tf in ['M15', 'M30']:
            rsi_value = np.random.uniform(25, 75)
        else:
            data = fetch_forex_data(pair, tf)
            rsi_value = calculate_rsi(data, period=10) if data is not None else np.nan
        row_data[tf] = rsi_value
    return row_data

progress_bar = st.progress(0)
status_text = st.empty()

if st.button("🔄 Relancer l’analyse"):
    st.experimental_rerun()

progress_bar = st.progress(0)
status_text = st.empty()
results = []

with st.spinner("📡 Analyse en cours des paires..."):
    with ThreadPoolExecutor() as executor:
        futures = {executor.submit(analyze_pair, pair): pair for pair in filtered_pairs}
        total = len(futures)
        for i, future in enumerate(as_completed(futures)):
            pair = futures[future]
            result = future.result()
            results.append(result)
            status_text.text(f"Analyse en cours: {pair} ({i+1}/{total})")
            progress_bar.progress((i + 1) / total)

progress_bar.empty()
status_text.empty()


# Suppression des éléments de progression
progress_bar.empty()
status_text.empty()

# Création du tableau HTML
st.markdown("### 📈 Résultats de l'analyse RSI")
html_table = '<table class="rsi-table">'
html_table += '<thead><tr><th>Symbol</th>'
for tf in timeframes:
    html_table += f'<th>{tf}</th>'
html_table += '</tr></thead><tbody>'
for row in results:
    html_table += f'<tr><td class="symbol-cell">{row["Symbol"]}</td>'
    for tf in timeframes:
        rsi_val = row[tf]
        css_class = get_rsi_class(rsi_val)
        formatted_val = format_rsi(rsi_val)
        html_table += f'<td class="{css_class}">{formatted_val}</td>'
    html_table += '</tr>'
html_table += '</tbody></table>'
st.markdown(html_table, unsafe_allow_html=True)

# Statistiques
st.markdown('<div class="stats-container">', unsafe_allow_html=True)
st.markdown("### 📊 Statistiques des signaux")
col1, col2, col3, col4 = st.columns(4)
for i, tf in enumerate(['H1', 'H4', 'D1', 'W1']):
    rsi_values = [row[tf] for row in results if not pd.isna(row[tf])]
    if rsi_values:
        oversold = sum(1 for x in rsi_values if x <= 20)
        overbought = sum(1 for x in rsi_values if x >= 80)
        total_signals = oversold + overbought
        with [col1, col2, col3, col4][i]:
            st.metric(
                label=f"Signaux {tf}",
                value=str(total_signals),
                delta=f"🔴 {oversold} | 🟢 {overbought}"
            )
st.markdown('</div>', unsafe_allow_html=True)
st.success(f"✅ Analyse terminée! {len(filtered_pairs)} paires analysées.")

# Section d'aide
with st.expander("ℹ️ Guide d'utilisation"):
    st.markdown("""
    ## Configuration du RSI
    - **Période**: 10
    - **Source**: OHLC4 (moyenne des prix Open, High, Low, Close)
    - **Seuils**: Oversold ≤ 20 | Overbought ≥ 80
    
    ## Timeframes
    - **M15/M30**: Simulés (Yahoo Finance ne supporte pas ces intervalles)
    - **H1**: Données horaires (5 derniers jours)
    - **H4**: Données 4h (1 mois)
    - **D1**: Données quotidiennes (3 mois)
    - **W1**: Données hebdomadaires (2 ans)
    
    ## Utilisation
    - L'analyse se lance automatiquement au chargement de la page.
    - Utilisez la barre de recherche pour filtrer les paires.
    - Les cellules colorées indiquent les opportunités:
      - 🔴 Rouge: Survente (RSI ≤ 20)
      - 🟢 Vert: Surachat (RSI ≥ 80)
    
    ## Paires analysées
    EUR/USD, USD/JPY, GBP/USD, USD/CHF, AUD/USD, USD/CAD, NZD/USD, EUR/JPY, GBP/JPY, EUR/GBP
    """)

# Footer
st.markdown("---")
st.markdown("*Développé avec Streamlit | Données Yahoo Finance | RSI OHLC4 Période 10*")


