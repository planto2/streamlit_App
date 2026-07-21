import streamlit as st
import requests
import pandas as pd
import random
import folium

from datetime import datetime
from urllib.parse import unquote
from streamlit_folium import st_folium


# ==================================
# Streamlit 설정
# ==================================

st.set_page_config(
    page_title="대한민국 축제 탐험가",
    page_icon="🎉",
    layout="wide"
)


st.title("🎉 대한민국 축제 탐험가")
st.caption(
    "한국관광공사 국문 관광정보 서비스_GW 기반"
)


# ==================================
# API KEY
# ==================================

try:

    API_KEY = st.secrets["TOUR_API_KEY"]

    # 인코딩/디코딩 혼동 대응
    API_KEY = unquote(API_KEY)


except Exception:


    st.error(
        """
        Streamlit Secrets 설정 필요

        예:

        TOUR_API_KEY="일반 인증키(Encoding)"
        """
    )

    st.stop()



# ==================================
# Tour API
# ==================================

BASE_URL = (
    "https://apis.data.go.kr/B551011/KorService1/"
    "searchFestival2"
)



# ==================================
# API 호출
# ==================================

@st.cache_data(ttl=3600)
def get_festivals():


    today = datetime.now()


    params = {


        "serviceKey": API_KEY,


        "MobileOS": "ETC",


        "MobileApp": "FestivalExplorer",


        "_type": "json",


        "pageNo": 1,


        "numOfRows": 100,


        "eventStartDate":
            f"{today.year}0101",


        "eventEndDate":
            f"{today.year}1231"

    }



    try:


        response = requests.get(
            BASE_URL,
            params=params,
            timeout=20
        )


        # 디버깅 표시

        with st.expander(
            "🔧 API 디버그 정보"
        ):

            st.write(
                "HTTP 상태:",
                response.status_code
            )


            st.write(
                "요청 URL"
            )


            st.code(
                response.url
            )


            st.write(
                "응답 일부"
            )


            st.code(
                response.text[:2000]
            )



        if response.status_code != 200:

            return []



        # JSON 변환

        try:

            data = response.json()


        except:


            st.error(
                "JSON 변환 실패"
            )

            return []



        header = (
            data
            .get("response", {})
            .get("header", {})
        )



        result_code = header.get(
            "resultCode"
        )


        if result_code != "0000":


            st.error(
                f"""
                API 오류

                코드:
                {result_code}

                메시지:
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
            f"연결 오류 : {e}"
        )


        return []



# ==================================
# 데이터 가져오기
# ==================================

festivals = get_festivals()



if not festivals:


    st.warning(
        """
        축제 데이터를 가져오지 못했습니다.

        위의 API 디버그 정보를 확인하세요.
        """
    )

    st.stop()



df = pd.DataFrame(
    festivals
)



# ==================================
# 즐겨찾기
# ==================================

if "favorites" not in st.session_state:

    st.session_state.favorites = []



# ==================================
# 검색
# ==================================

st.subheader(
    "🔎 축제 검색"
)


col1,col2 = st.columns(2)



with col1:

    keyword = st.text_input(
        "축제명 검색"
    )



with col2:


    if "addr1" in df.columns:


        region_list = [
            "전체"
        ] + sorted(
            df["addr1"]
            .dropna()
            .unique()
            .tolist()
        )


        region = st.selectbox(
            "지역",
            region_list
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



st.success(
    f"총 {len(df)}개 축제"
)



# ==================================
# 랜덤 추천
# ==================================

if st.button(
    "🎲 랜덤 축제 추천"
):


    pick = random.choice(
        df.to_dict("records")
    )


    st.info(
        f"""
        🎉 {pick['title']}

        📍 {pick.get('addr1','')}

        📅
        {pick.get('eventstartdate','')}
        -
        {pick.get('eventenddate','')}
        """
    )



# ==================================
# 카드
# ==================================

for festival in df.to_dict(
    "records"
):


    st.divider()


    c1,c2 = st.columns(
        [1,3]
    )



    with c1:


        img = festival.get(
            "firstimage"
        )


        if img:

            st.image(
                img,
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
            "⭐ 저장",
            key=str(
                festival.get(
                    "contentid"
                )
            )
        ):

            st.session_state.favorites.append(
                festival
            )

            st.toast(
                "저장 완료"
            )



# ==================================
# 지도
# ==================================

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



for festival in df.to_dict(
    "records"
):


    try:


        folium.Marker(

            [
                float(
                    festival["mapy"]
                ),

                float(
                    festival["mapx"]
                )

            ],

            popup=
            festival["title"]

        ).add_to(
            map_obj
        )


    except:

        pass



st_folium(
    map_obj,
    width=900,
    height=500
)



# ==================================
# 사이드바
# ==================================

st.sidebar.title(
    "⭐ 저장한 축제"
)


for f in st.session_state.favorites:

    st.sidebar.write(
        f"🎉 {f['title']}"
    )
