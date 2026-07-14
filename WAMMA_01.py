import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Global Market Cap Top10 Dashboard",
    layout="wide"
)

st.title("🌍 Global Market Cap Top 10 Stock Dashboard")
st.markdown("최근 1년 주가 성과 비교")

# 시가총액 Top10 (2025 기준)
stocks = {
    "Apple": "AAPL",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Amazon": "AMZN",
    "Alphabet": "GOOGL",
    "Meta": "META",
    "Saudi Aramco": "2222.SR",
    "Broadcom": "AVGO",
    "Tesla": "TSLA",
    "Berkshire Hathaway": "BRK-B"
}

selected = st.multiselect(
    "기업 선택",
    list(stocks.keys()),
    default=list(stocks.keys())
)

if len(selected) == 0:
    st.warning("최소 하나 이상의 기업을 선택하세요.")
    st.stop()

@st.cache_data
def load_data():

    tickers = [stocks[s] for s in selected]

    data = yf.download(
        tickers,
        period="1y",
        auto_adjust=True,
        progress=False
    )["Close"]

    return data

df = load_data()

# 정규화
normalized = df / df.iloc[0] * 100

fig = go.Figure()

for company in selected:

    ticker = stocks[company]

    if len(selected) == 1:
        y = normalized
    else:
        y = normalized[ticker]

    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=y,
            mode="lines",
            name=company,
            line=dict(width=3)
        )
    )

fig.update_layout(
    height=700,
    title="Normalized Stock Performance (Base = 100)",
    xaxis_title="Date",
    yaxis_title="Performance",
    hovermode="x unified",
    template="plotly_white",
    legend=dict(
        orientation="h",
        y=1.05
    )
)

st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("📈 1년 수익률")

cols = st.columns(len(selected))

for col, company in zip(cols, selected):

    ticker = stocks[company]

    if len(selected) == 1:
        perf = (df.iloc[-1] / df.iloc[0] - 1) * 100
    else:
        perf = (df[ticker].iloc[-1] / df[ticker].iloc[0] - 1) * 100

    col.metric(
        company,
        f"{perf:.2f}%"
    )

st.divider()

st.dataframe(df.tail())
