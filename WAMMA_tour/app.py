import streamlit as st
import requests
import pandas as pd
import random
from datetime import datetime
from dateutil import parser

import folium
from streamlit_folium import st_folium


# -----------------------
# 기본 설정
# -----------------------

st.set_page_config(
    page_title="대한민국 축제 탐험가",
    page_icon="🎉",
    layout="wide"
)


API_KEY = st.secrets["TOUR_API_KEY"]


BASE_URL = (
    "https://apis.data.go.kr/B551011/KorService1/"
    "searchFestival1"
)


# -----------------------
# 데이터 가져오기
# -----------------------

@st.cache_data(ttl=3600)
def get_festivals(year, month):

    params = {
        "serviceKey": API_KEY,
        "MobileOS": "ETC",
        "MobileApp": "FestivalExplorer",
        "_type": "json",
        "numOfRows": 200,
        "eventStartDate": f"{year}{month:02d}01"
    }


    try:

        res = requests.get(
            BASE_URL,
            params=params
        )

        data = res.json()

        items = (
            data["response"]
            ["body"]
            ["items"]
            ["item"]
        )

        return items

    except Exception:

        return []



# -----------------------
# 세션 저장
# -----------------------

if "favorites" not in st.session_state:
    st.session_state.favorites = []



# -----------------------
# UI
# -----------------------

st.title("🎉 대한민국 축제 탐험가")

st.write(
    "한국관광공사 데이터를 활용한 전국 축제 검색 서비스"
)



col1, col2 = st.columns(2)


with col1:

    today = datetime.now()

    year = st.selectbox(
        "연도",
        [2025,2026],
        index=1
    )


with col2:

    month = st.slider(
        "월",
        1,
        12,
        today.month
    )



festivals = get_festivals(
    year,
    month
)



if not festivals:

    st.warning(
        "축제 정보를 찾지 못했습니다."
    )

    st.stop()



df = pd.DataFrame(festivals)



# -----------------------
# 검색
# -----------------------

keyword = st.text_input(
    "🔎 축제 검색",
    ""
)


if keyword:

    df = df[
        df["title"]
        .str.contains(
            keyword,
            case=False,
            na=False
        )
    ]



regions = [
    "전체"
] + sorted(
    df["addr1"]
    .dropna()
    .unique()
    .tolist()
)


region = st.selectbox(
    "📍 지역",
    regions
)



if region != "전체":

    df = df[
        df.addr1 == region
    ]



st.subheader(
    f"🎪 발견한 축제 {len(df)}개"
)



# -----------------------
# 랜덤 추천
# -----------------------

if st.button(
    "🎲 오늘의 축제 추천!"
):

    pick = random.choice(
        df.to_dict("records")
    )

    st.success(
        f"""
        🎉 추천 축제

        {pick['title']}

        📍 {pick.get('addr1','')}

        📅 {pick.get('eventstartdate','')}
        ~
        {pick.get('eventenddate','')}
        """
    )



# -----------------------
# 카드 출력
# -----------------------


for festival in df.to_dict("records"):


    with st.container():

        st.markdown(
            "---"
        )


        col1,col2 = st.columns(
            [1,3]
        )


        with col1:

            if festival.get(
                "firstimage"
            ):

                st.image(
                    festival["firstimage"]
                )


        with col2:


            st.subheader(
                festival["title"]
            )


            st.write(
                "📍 "
                +
                festival.get(
                    "addr1",
                    ""
                )
            )


            st.write(
                "📅 "
                +
                festival.get(
                    "eventstartdate",
                    ""
                )
                +
                " ~ "
                +
                festival.get(
                    "eventenddate",
                    ""
                )
            )


            if st.button(
                "⭐ 관심 축제 저장",
                key=festival["contentid"]
            ):

                if festival not in st.session_state.favorites:

                    st.session_state.favorites.append(
                        festival
                    )

                    st.toast(
                        "저장 완료!"
                    )



# -----------------------
# 지도
# -----------------------

st.subheader(
    "🗺️ 축제 지도"
)


map_data = []


for f in df.to_dict("records"):

    if (
        f.get("mapy")
        and
        f.get("mapx")
    ):

        map_data.append(
            [
                float(f["mapy"]),
                float(f["mapx"]),
                f["title"]
            ]
        )



if map_data:

    m = folium.Map(
        location=[
            36.5,
            127.8
        ],
        zoom_start=7
    )


    for lat,lon,name in map_data:

        folium.Marker(
            [
                lat,
                lon
            ],
            popup=name
        ).add_to(m)


    st_folium(
        m,
        width=900,
        height=500
    )



# -----------------------
# 즐겨찾기
# -----------------------

st.sidebar.title(
    "⭐ 저장한 축제"
)


for f in st.session_state.favorites:

    st.sidebar.write(
        f["title"]
    )
