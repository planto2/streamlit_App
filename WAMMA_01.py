import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go


# ==============================
# Page Config
# ==============================

st.set_page_config(
    page_title="Global Market Cap Top10 Dashboard",
    page_icon="🌍",
    layout="wide"
)


# ==============================
# Title
# ==============================

st.title("🌍 Global Market Cap Top 10 Stock Dashboard")

st.markdown(
    """
    글로벌 시가총액 Top 10 기업의 주가 성과를 비교하는 대시보드입니다.  
    기준값을 100으로 정규화하여 상대적인 성과를 비교합니다.
    """
)


# ==============================
# Stock Universe
# ==============================

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


# ==============================
# Sidebar
# ==============================

st.sidebar.header("⚙️ Dashboard Settings")


period = st.sidebar.selectbox(
    "조회 기간",
    [
        "1mo",
        "3mo",
        "6mo",
        "1y",
        "2y",
        "5y"
    ],
    index=3
)


selected = st.sidebar.multiselect(
    "기업 선택",
    list(stocks.keys()),
    default=list(stocks.keys())
)


if len(selected) == 0:
    st.warning("하나 이상의 기업을 선택하세요.")
    st.stop()



# ==============================
# Data Loading
# ==============================

@st.cache_data(ttl=3600)
def load_data(selected_companies, period):

    result = pd.DataFrame()


    for company in selected_companies:

        ticker = stocks[company]


        try:

            data = yf.download(
                ticker,
                period=period,
                auto_adjust=True,
                progress=False
            )


            if data.empty:
                continue


            close = data["Close"]


            # yfinance 최신 버전 대응
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]


            close.name = company


            result = pd.concat(
                [
                    result,
                    close
                ],
                axis=1
            )


        except Exception:
            continue



    result = result.sort_index()

    # 거래일 차이 보정
    result = result.ffill()


    return result



# ==============================
# Loading
# ==============================

with st.spinner(
    "📡 주가 데이터를 불러오는 중입니다..."
):

    df = load_data(
        selected,
        period
    )


if df.empty:

    st.error(
        "데이터를 가져오지 못했습니다."
    )

    st.stop()



# ==============================
# Normalize
# ==============================

normalized = pd.DataFrame(
    index=df.index
)


returns = {}


latest_prices = {}


for company in df.columns:


    series = df[company].dropna()


    if len(series) < 2:
        continue


    normalized[company] = (
        df[company]
        /
        series.iloc[0]
        *
        100
    )


    returns[company] = (
        series.iloc[-1]
        /
        series.iloc[0]
        -
        1
    ) * 100


    latest_prices[company] = series.iloc[-1]
    # ==============================
# KPI Dashboard
# ==============================

best_company = max(
    returns,
    key=returns.get
)


average_return = sum(
    returns.values()
) / len(returns)



kpi1, kpi2, kpi3 = st.columns(3)


kpi1.metric(
    "🏆 최고 수익률",
    best_company,
    f"{returns[best_company]:.2f}%"
)


kpi2.metric(
    "📊 평균 수익률",
    f"{average_return:.2f}%"
)


kpi3.metric(
    "🏢 선택 기업 수",
    f"{len(normalized.columns)}개"
)



st.divider()



# ==============================
# Plotly Chart
# ==============================

st.subheader(
    "📈 주가 성과 비교"
)


fig = go.Figure()



for company in normalized.columns:

    fig.add_trace(
        go.Scatter(
            x=normalized.index,
            y=normalized[company],
            mode="lines",
            name=company,
            line=dict(
                width=3
            )
        )
    )



fig.update_layout(
    height=650,

    template="plotly_white",

    hovermode="x unified",

    xaxis_title="Date",

    yaxis_title="Performance (Base=100)",

    legend=dict(
        orientation="h",
        y=1.08
    )
)



fig.update_xaxes(

    rangeslider_visible=True,

    rangeselector=dict(

        buttons=[

            dict(
                count=1,
                label="1M",
                step="month",
                stepmode="backward"
            ),

            dict(
                count=6,
                label="6M",
                step="month",
                stepmode="backward"
            ),

            dict(
                count=1,
                label="YTD",
                step="year",
                stepmode="todate"
            ),

            dict(
                count=1,
                label="1Y",
                step="year",
                stepmode="backward"
            ),

            dict(
                step="all",
                label="ALL"
            )
        ]
    )
)



st.plotly_chart(
    fig,
    use_container_width=True
)



# ==============================
# Return Ranking
# ==============================


st.divider()


st.subheader(
    "🏆 기간별 수익률 순위"
)



ranking = pd.DataFrame(

    {
        "Company": returns.keys(),

        "Return (%)": returns.values()

    }

)


ranking = ranking.sort_values(

    "Return (%)",

    ascending=False

)



st.dataframe(

    ranking.style.format(
        {
            "Return (%)": "{:.2f}%"
        }
    ),

    use_container_width=True,

    hide_index=True

)



# ==============================
# Latest Price
# ==============================


st.divider()


st.subheader(
    "💵 현재 가격"
)



price_table = pd.DataFrame(

    {
        "Company": latest_prices.keys(),

        "Price": latest_prices.values()

    }

)



st.dataframe(

    price_table.style.format(

        {
            "Price": "${:.2f}"

        }

    ),

    use_container_width=True,

    hide_index=True

)




# ==============================
# Raw Data
# ==============================


st.divider()


with st.expander(
    "📋 최근 주가 데이터 보기"
):

    st.dataframe(

        df.tail()
        .style
        .format("{:.2f}"),

        use_container_width=True

    )



# ==============================
# Footer
# ==============================


st.divider()


st.caption(
    """
    Data source: Yahoo Finance (via yfinance)  
    ⚠️ This dashboard is for educational purposes only and is not investment advice.
    """
)
