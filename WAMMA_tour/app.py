import streamlit as st
import requests
import pandas as pd
import random
import folium

from datetime import datetime
from urllib.parse import unquote
from streamlit_folium import st_folium


# =====================================
# 기본 설정
# =====================================

st.set_page_config(
    page_title="대한민국 축제 탐험가",
    page_icon="🎉",
    layout="wide"
)


st.title("🎉 대한민국 축제 탐험가")
st.caption(
    "한국관광공사 국문 관광정보 서비스 기반"
)



# =====================================
# API KEY
# =====================================

try:

    API_KEY = st.secrets["TOUR_API_KEY"]

    API_KEY = unquote(API_KEY)


except:

    st.error(
        """
        Streamlit Secrets 설정 필요

        TOUR_API_KEY="Encoding 인증키"
        """
    )

    st.stop()



# =====================================
# API 주소
# =====================================

BASE_URL = (
    "https://apis.data.go.kr/B551011/"
    "KorService2/searchFestival2"
)



# =====================================
# 데이터 로딩
# =====================================

@st.cache_data(ttl=3600)
def load_festivals():


    today = datetime.now()


    params = {

        "serviceKey": API_KEY,

        "MobileOS": "ETC",

        "MobileApp": "FestivalExplorer",

        "_type": "json",

        "pageNo": 1,

        "numOfRows": 500,

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


        if response.status_code != 200:

            st.error(
                f"API 오류 : {response.status_code}"
            )

            return []



        data = response.json()


        header = (
            data
            .get("response", {})
            .get("header", {})
        )


        if header.get(
            "resultCode"
        ) != "0000":

            st.error(
                header.get(
                    "resultMsg"
                )
            )

            return []



        items = (
            data
            ["response"]
            ["body"]
            ["items"]
            ["item"]
        )


        if isinstance(
            items,
            dict
        ):

            items = [items]


        return items



    except Exception as e:


        st.error(
            f"API 연결 오류 : {e}"
        )


        return []



# =====================================
# 세션 상태
# =====================================

if "favorites" not in st.session_state:

    st.session_state.favorites = []


if "random_festival" not in st.session_state:

    st.session_state.random_festival = None


if "mbti_result" not in st.session_state:

    st.session_state.mbti_result = None



# =====================================
# 데이터 준비
# =====================================

festivals = load_festivals()


if not festivals:

    st.warning(
        "축제 정보를 가져오지 못했습니다."
    )

    st.stop()



df = pd.DataFrame(
    festivals
)



# =====================================
# 검색 기능
# =====================================

st.subheader(
    "🔎 축제 검색"
)


c1,c2 = st.columns(2)


with c1:

    keyword = st.text_input(
        "축제명 검색"
    )


with c2:


    regions = [
        "전체"
    ]


    if "addr1" in df:

        regions += sorted(
            df["addr1"]
            .dropna()
            .unique()
            .tolist()
        )


    region = st.selectbox(
        "지역",
        regions
    )



filtered_df = df.copy()



if keyword:


    filtered_df = filtered_df[
        filtered_df["title"]
        .str.contains(
            keyword,
            case=False,
            na=False
        )
    ]



if region != "전체":

    filtered_df = filtered_df[
        filtered_df["addr1"]
        ==
        region
    ]



st.success(
    f"현재 {len(filtered_df)}개 축제"
)



# =====================================
# 랜덤 추천
# =====================================

st.divider()

st.subheader(
    "🎲 오늘의 랜덤 축제"
)



if st.button(
    "랜덤 축제 뽑기"
):

    st.session_state.random_festival = random.choice(
        df.to_dict("records")
    )



if st.session_state.random_festival:


    f = st.session_state.random_festival


    st.success(
        f"""
🎉 {f.get('title')}

📍 {f.get('addr1','')}

📅
{f.get('eventstartdate','')}
~
{f.get('eventenddate','')}
"""
    )



# =====================================
# MBTI 추천
# =====================================

st.divider()

st.subheader(
    "🧭 나의 축제 여행 MBTI"
)


a,b = st.columns(2)


with a:


    q1 = st.radio(
        "여행 분위기",
        [
            "사람 많은 축제",
            "조용한 축제"
        ]
    )


    q2 = st.radio(
        "즐기는 방식",
        [
            "먹거리 중심",
            "체험 중심"
        ]
    )



with b:


    q3 = st.radio(
        "느낌",
        [
            "전통/역사",
            "감성/사진"
        ]
    )


    q4 = st.radio(
        "계획 스타일",
        [
            "계획형",
            "즉흥형"
        ]
    )



if st.button(
    "✨ 내 축제 MBTI 확인"
):


    result = ""

    result += (
        "E"
        if q1=="사람 많은 축제"
        else "I"
    )


    result += (
        "S"
        if q2=="먹거리 중심"
        else "N"
    )


    result += (
        "T"
        if q3=="전통/역사"
        else "F"
    )


    result += (
        "J"
        if q4=="계획형"
        else "P"
    )


    st.session_state.mbti_result = result



if st.session_state.mbti_result:


    mbti = st.session_state.mbti_result


    st.success(
        f"🎉 당신의 축제 유형 : {mbti}"
    )


    keyword_map = {


        "E":
        [
            "축제",
            "행사",
            "공연"
        ],


        "I":
        [
            "문화",
            "전통",
            "꽃"
        ],


        "S":
        [
            "먹거리",
            "음식",
            "시장"
        ],


        "N":
        [
            "체험",
            "문화",
            "공연"
        ],


        "T":
        [
            "전통",
            "역사"
        ],


        "F":
        [
            "꽃",
            "사진",
            "힐링"
        ]

    }


    keywords = []

    for char in mbti:

        keywords += keyword_map.get(
            char,
            []
        )


    mbti_df = df[
        df["title"]
        .str.contains(
            "|".join(keywords),
            case=False,
            na=False
        )
    ]



    if len(mbti_df):


        pick = random.choice(
            mbti_df.to_dict("records")
        )


    else:


        pick = random.choice(
            df.to_dict("records")
        )



    st.info(
        f"""
추천 축제 🎪

{pick['title']}

📍 {pick.get('addr1','')}
"""
    )



# =====================================
# 축제 카드
# =====================================

st.divider()

st.subheader(
    "🎪 축제 목록"
)


for festival in filtered_df.to_dict(
    "records"
):


    left,right = st.columns(
        [1,3]
    )


    with left:


        if festival.get(
            "firstimage"
        ):

            st.image(
                festival["firstimage"],
                width=160
            )


    with right:


        st.subheader(
            festival["title"]
        )


        st.write(
            festival.get(
                "addr1",
                ""
            )
        )


        if st.button(
            "⭐ 저장",
            key=str(
                festival["contentid"]
            )
        ):

            st.session_state.favorites.append(
                festival
            )

            st.toast(
                "저장 완료"
            )


    st.divider()



# =====================================
# 지도
# =====================================

st.subheader(
    "🗺️ 축제 지도"
)


m = folium.Map(
    location=[
        36.5,
        127.8
    ],
    zoom_start=7
)


for f in filtered_df.to_dict(
    "records"
):

    try:

        folium.Marker(
            [
                float(f["mapy"]),
                float(f["mapx"])
            ],
            popup=f["title"]
        ).add_to(m)

    except:

        pass



st_folium(
    m,
    width=900,
    height=500
)



# =====================================
# 사이드바
# =====================================

st.sidebar.title(
    "⭐ 저장한 축제"
)


for f in st.session_state.favorites:

    st.sidebar.write(
        f"🎉 {f['title']}"
    )
