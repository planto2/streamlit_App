import streamlit as st
import requests
import pandas as pd
import random
import folium

from streamlit_folium import st_folium


# ==============================
# 설정
# ==============================

st.set_page_config(
    page_title="대한민국 축제 탐험가",
    page_icon="🎉",
    layout="wide"
)


st.title("🎉 대한민국 축제 탐험가")
st.caption(
    "한국관광공사 TourAPI 기반 전국 축제 검색 서비스"
)


# ==============================
# API 설정
# ==============================

try:
    API_KEY = st.secrets["TOUR_API_KEY"]

except:

    st.error(
        """
        API 키가 없습니다.

        Streamlit Cloud → Settings → Secrets 에 아래 추가:

        TOUR_API_KEY="발급받은키"
        """
    )

    st.stop()



BASE_URL = (
    "https://apis.data.go.kr/B551011/KorService1/"
    "searchFestival2"
)



# ==============================
# 데이터 요청
# ==============================


@st.cache_data(ttl=3600)
def get_festivals():


    params = {

        "serviceKey": API_KEY,

        "MobileOS": "ETC",

        "MobileApp": "FestivalExplorer",

        "_type": "json",

        "numOfRows": 500,

        "pageNo": 1

    }


    try:

        response = requests.get(
            BASE_URL,
            params=params,
            timeout=10
        )


        if response.status_code != 200:

            st.error(
                f"HTTP 오류 : {response.status_code}"
            )

            return []


        data = response.json()


        body = (
            data
            .get("response", {})
            .get("body", {})
        )


        items = body.get(
            "items",
            {}
        )


        if items == "":

            return []


        result = items.get(
            "item",
            []
        )


        if isinstance(result, dict):

            result = [result]


        return result



    except Exception as e:


        st.error(
            f"API 오류 발생 : {e}"
        )

        return []




festivals = get_festivals()



# ==============================
# 데이터 확인
# ==============================


if not festivals:


    st.warning(
        """
        축제 정보를 가져오지 못했습니다.

        확인할 것:

        1. API 인증키 확인
        2. 공공데이터포털 활용신청 승인 여부
        3. Streamlit Secrets 설정 확인
        """
    )


    st.stop()



df = pd.DataFrame(
    festivals
)



# ==============================
# 세션
# ==============================


if "favorites" not in st.session_state:

    st.session_state.favorites = []



# ==============================
# 필터
# ==============================


col1,col2 = st.columns(2)



with col1:

    keyword = st.text_input(
        "🔎 축제 검색",
        ""
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
            "📍 지역",
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
    f"🎪 축제 {len(df)}개 발견"
)



# ==============================
# 랜덤 추천
# ==============================


if st.button(
    "🎲 랜덤 축제 추천"
):


    festival = random.choice(
        df.to_dict("records")
    )


    st.success(
        f"""
        🌟 오늘의 추천

        🎪 {festival.get('title')}

        📍 {festival.get('addr1','')}

        📅
        {festival.get('eventstartdate','')}
        -
        {festival.get('eventenddate','')}
        """
    )



# ==============================
# 카드 출력
# ==============================


for f in df.to_dict("records"):


    with st.container():


        st.divider()


        c1,c2 = st.columns(
            [1,3]
        )


        with c1:


            img = f.get(
                "firstimage"
            )


            if img:

                st.image(
                    img,
                    width=180
                )



        with c2:


            st.header(
                f.get(
                    "title",
                    "이름 없음"
                )
            )


            st.write(
                "📍",
                f.get(
                    "addr1",
                    ""
                )
            )


            st.write(
                "📅",
                f.get(
                    "eventstartdate",
                    ""
                ),
                "~",
                f.get(
                    "eventenddate",
                    ""
                )
            )


            if st.button(
                "⭐ 저장",
                key=f.get(
                    "contentid"
                )
            ):

                st.session_state.favorites.append(
                    f
                )

                st.toast(
                    "저장했습니다!"
                )



# ==============================
# 지도
# ==============================


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



count = 0



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


        count += 1


    except:

        pass



if count:


    st_folium(
        map_obj,
        width=900,
        height=500
    )


else:


    st.info(
        "지도 좌표 데이터가 없습니다."
    )



# ==============================
# 즐겨찾기
# ==============================


st.sidebar.title(
    "⭐ 저장한 축제"
)



if st.session_state.favorites:


    for f in st.session_state.favorites:

        st.sidebar.write(
            "🎉",
            f["title"]
        )

else:

    st.sidebar.write(
        "아직 저장한 축제가 없습니다."
    )
