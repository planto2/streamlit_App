import streamlit as st
import requests
import pandas as pd
import random
import folium

from datetime import datetime
from streamlit_folium import st_folium


# ======================================
# 기본 설정
# ======================================

st.set_page_config(
    page_title="대한민국 축제 탐험가",
    page_icon="🎉",
    layout="wide"
)


st.title("🎉 대한민국 축제 탐험가")
st.write(
    "한국관광공사 국문 관광정보 서비스 기반 축제 검색"
)


# ======================================
# API KEY
# ======================================

try:

    API_KEY = st.secrets["TOUR_API_KEY"]

except:

    st.error(
        """
        Streamlit Secrets에 API 키를 등록해주세요.

        예:

        TOUR_API_KEY="발급받은_인증키"
        """
    )

    st.stop()



# ======================================
# TourAPI 주소
# ======================================

BASE_URL = (
    "https://apis.data.go.kr/B551011/KorService1/"
    "searchFestival2"
)



# ======================================
# 축제 데이터 가져오기
# ======================================

@st.cache_data(ttl=3600)
def load_festivals():


    today = datetime.now()

    start_date = (
        f"{today.year}"
        f"{today.month:02d}"
        f"{today.day:02d}"
    )


    params = {

        "serviceKey": API_KEY,

        "MobileOS": "ETC",

        "MobileApp": "FestivalExplorer",

        "_type": "json",

        "numOfRows": 500,

        "pageNo": 1,

        "eventStartDate": start_date

    }


    try:


        response = requests.get(
            BASE_URL,
            params=params,
            timeout=15
        )


        if response.status_code != 200:

            st.error(
                f"HTTP 오류 : {response.status_code}"
            )

            st.code(
                response.text[:1000]
            )

            return []



        data = response.json()



        header = (
            data
            .get("response", {})
            .get("header", {})
        )


        code = header.get(
            "resultCode"
        )


        if code != "0000":

            st.error(
                f"""
                API 오류

                코드 : {code}

                메시지 :
                {header.get('resultMsg')}
                """
            )

            return []



        body = (
            data
            ["response"]
            ["body"]
        )


        items = body.get(
            "items"
        )


        if not items:

            return []



        result = items.get(
            "item",
            []
        )


        if isinstance(
            result,
            dict
        ):

            result = [result]



        return result



    except Exception as e:


        st.error(
            f"API 처리 오류 : {e}"
        )


        return []



# ======================================
# 데이터 로드
# ======================================


festivals = load_festivals()



if not festivals:


    st.warning(
        """
        축제 정보를 가져오지 못했습니다.

        확인:
        - 공공데이터포털 활용신청 승인 여부
        - Encoding 인증키 사용 여부
        - Secrets 설정 확인
        """
    )


    st.stop()



df = pd.DataFrame(
    festivals
)



# ======================================
# 즐겨찾기
# ======================================

if "favorites" not in st.session_state:

    st.session_state.favorites = []



# ======================================
# 검색
# ======================================


col1, col2 = st.columns(2)


with col1:

    keyword = st.text_input(
        "🔎 축제 검색"
    )



with col2:


    if "addr1" in df.columns:

        regions = [
            "전체"
        ] + sorted(
            df["addr1"]
            .dropna()
            .unique()
            .tolist()
        )


        region = st.selectbox(
            "📍 지역 선택",
            regions
        )

    else:

        region = "전체"



if keyword:

    df = df[
        df["title"]
        .str.contains(
            keyword,
            case=False,
            na=False
        )
    ]



if region != "전체":

    df = df[
        df["addr1"] == region
    ]



st.subheader(
    f"🎪 검색된 축제 : {len(df)}개"
)



# ======================================
# 랜덤 추천
# ======================================

if st.button(
    "🎲 오늘의 축제 추천"
):

    choice = random.choice(
        df.to_dict("records")
    )


    st.success(
        f"""
        🎉 추천 축제

        {choice.get('title')}

        📍
        {choice.get('addr1','')}

        📅
        {choice.get('eventstartdate')}
        ~
        {choice.get('eventenddate')}
        """
    )



# ======================================
# 축제 카드
# ======================================


for festival in df.to_dict(
    "records"
):


    st.divider()


    c1,c2 = st.columns(
        [1,3]
    )


    with c1:


        image = festival.get(
            "firstimage"
        )


        if image:

            st.image(
                image,
                width=180
            )



    with c2:


        st.subheader(
            festival.get(
                "title",
                "이름 없음"
            )
        )


        st.write(
            "📍",
            festival.get(
                "addr1",
                ""
            )
        )


        st.write(
            "📅",
            festival.get(
                "eventstartdate",
                ""
            ),
            "~",
            festival.get(
                "eventenddate",
                ""
            )
        )



        if st.button(
            "⭐ 관심 축제",
            key=festival.get(
                "contentid"
            )
        ):

            st.session_state.favorites.append(
                festival
            )

            st.toast(
                "저장 완료!"
            )



# ======================================
# 지도
# ======================================

st.subheader(
    "🗺️ 축제 지도"
)


map_obj = folium.Map(
    location=[
        36.5,
        127.8
    ],
    zoom_start=7
)


marker_count = 0


for f in df.to_dict("records"):


    try:


        lat = float(
            f["mapy"]
        )

        lon = float(
            f["mapx"]
        )


        folium.Marker(
            [
                lat,
                lon
            ],
            popup=f["title"]
        ).add_to(
            map_obj
        )


        marker_count += 1


    except:

        pass



if marker_count:


    st_folium(
        map_obj,
        width=900,
        height=500
    )


else:

    st.info(
        "좌표 정보가 없습니다."
    )



# ======================================
# 사이드바
# ======================================


st.sidebar.title(
    "⭐ 저장한 축제"
)



if st.session_state.favorites:


    for f in st.session_state.favorites:

        st.sidebar.write(
            f"🎉 {f['title']}"
        )


else:

    st.sidebar.write(
        "저장한 축제가 없습니다."
    )
