import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="Global Market Cap Top10 Dashboard",
    layout="wide"
)

st.title("🌍 Global Market Cap Top 10 Stock Dashboard")
st.markdown("최근 1년 주가 성과 비교 (기준값 = 100)")

# 글로벌 시가총액 Top10
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

if not selected:
    st.warning("최소 하나 이상의 기업을 선택하세요.")
    st.stop()


# ----------------------------
# 데이터 다운로드
# ----------------------------
@st.cache_data
def load_data(selected):

    data = pd.DataFrame()

    for company in selected:

        ticker = stocks[company]

        try:
            df = yf.download(
                ticker,
                period="1y",
                auto_adjust=True,
                progress=False
            )

            if df.empty:
                continue

            close = df["Close"]
            close.name = company

            data = pd.concat([data, close], axis=1)

        except Exception:
            pass

    # 거래일이 달라 생기는 NaN 보완
    data = data.sort_index()
    data = data.ffill()

    return data


df = load_data(selected)

if df.empty:
    st.error("주가 데이터를 불러오지 못했습니다.")
    st.stop()

# ----------------------------
# 정규화
# ----------------------------
normalized = pd.DataFrame(index=df.index)

for company in df.columns:

    series = df[company].dropna()

    if len(series) == 0:
        continue

    normalized[company] = df[company] / series.iloc[0] * 100


# ----------------------------
# Plotly
# ----------------------------
fig = go.Figure()

for company in normalized.columns:

    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized[company],
            mode="lines",
            name=company,
            line=dict(width=3)
        )
    )

fig.update_layout(
    title="Normalized Stock Performance (Base = 100)",
    height=700,
    template="plotly_white",
    hovermode="x unified",
    xaxis_title="Date",
    yaxis_title="Normalized Price",
    legend=dict(
        orientation="h",
        y=1.05
    )
)

st.plotly_chart(fig, use_container_width=True)

# ----------------------------
# 수익률
# ----------------------------
st.divider()

st.subheader("📈 최근 1년 수익률")

cols = st.columns(len(df.columns))

for col, company in zip(cols, df.columns):

    series = df[company].dropna()

    if len(series) < 2:
        perf = 0
    else:
        perf = (series.iloc[-1] / series.iloc[0] - 1) * 100

    col.metric(
        company,
        f"{perf:.2f}%"
    )

# ----------------------------
# 최근 데이터
# ----------------------------
st.divider()

st.subheader("최근 주가 데이터")

st.dataframe(df.tail())
