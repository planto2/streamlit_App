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
    page_title="대한민국 축제 여행 플래너",
    page_icon="🎉",
    layout="wide"
)


st.title(
    "🎉 대한민국 축제 여행 플래너"
)

st.caption(
    "한국관광공사 관광정보 API 기반"
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

FESTIVAL_URL = (
    "https://apis.data.go.kr/B551011/"
    "KorService2/searchFestival2"
)


KEYWORD_URL = (
    "https://apis.data.go.kr/B551011/"
    "KorService2/searchKeyword2"
)


LOCATION_URL = (
    "https://apis.data.go.kr/B551011/"
    "KorService2/locationBasedList2"
)



# =====================================
# 세션 상태
# =====================================

if "favorites" not in st.session_state:

    st.session_state.favorites = []


if "random_festival" not in st.session_state:

    st.session_state.random_festival = None


if "mbti" not in st.session_state:

    st.session_state.mbti = None


if "selected_festival" not in st.session_state:

    st.session_state.selected_festival = None



# =====================================
# 공통 API 요청 함수
# =====================================

def api_request(url, params):


    params.update({

        "serviceKey": API_KEY,

        "MobileOS": "ETC",

        "MobileApp": "FestivalPlanner",

        "_type": "json"

    })


    try:


        response = requests.get(
            url,
            params=params,
            timeout=20
        )


        if response.status_code != 200:

            return []



        data = response.json()


        body = (
            data
            .get("response", {})
            .get("body", {})
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



    except Exception:


        return []



# =====================================
# 축제 API
# =====================================

@st.cache_data(ttl=3600)
def load_festivals():


    today = datetime.now()


    return api_request(

        FESTIVAL_URL,

        {

            "pageNo":1,

            "numOfRows":500,

            "eventStartDate":
                f"{today.year}0101",

            "eventEndDate":
                f"{today.year}1231"

        }

    )



festivals = load_festivals()



if not festivals:

    st.error(
        "축제 정보를 불러오지 못했습니다."
    )

    st.stop()



df = pd.DataFrame(
    festivals
)



# =====================================
# 축제 검색
# =====================================

st.header(
    "🎪 축제 검색"
)


col1,col2 = st.columns(2)



with col1:


    keyword = st.text_input(
        "축제 이름 검색"
    )



with col2:


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
        "지역 선택",
        regions
    )



show_df = df.copy()



if keyword:


    show_df = show_df[
        show_df["title"]
        .str.contains(
            keyword,
            case=False,
            na=False
        )
    ]



if region != "전체":


    show_df = show_df[
        show_df["addr1"]
        ==
        region
    ]



st.success(
    f"검색 결과 : {len(show_df)}개"
)



# =====================================
# 랜덤 추천
# =====================================

st.divider()


st.header(
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
# MBTI 축제 추천
# =====================================

st.divider()

st.header(
    "🧭 나의 축제 여행 MBTI"
)



col1, col2 = st.columns(2)



with col1:


    people = st.radio(
        "여행 분위기",
        [
            "사람 많은 축제",
            "조용한 축제"
        ]
    )


    activity = st.radio(
        "즐기는 방식",
        [
            "먹거리 중심",
            "체험 중심"
        ]
    )



with col2:


    feeling = st.radio(
        "여행 느낌",
        [
            "전통/역사",
            "감성/사진"
        ]
    )


    schedule = st.radio(
        "여행 스타일",
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
        if people == "사람 많은 축제"
        else "I"
    )


    result += (
        "S"
        if activity == "먹거리 중심"
        else "N"
    )


    result += (
        "T"
        if feeling == "전통/역사"
        else "F"
    )


    result += (
        "J"
        if schedule == "계획형"
        else "P"
    )


    st.session_state.mbti = result



if st.session_state.mbti:


    mbti = st.session_state.mbti


    st.success(
        f"🎉 당신의 축제 여행 유형 : {mbti}"
    )



    mbti_description = {


        "ENFP":
        "사람들과 어울리는 활기찬 축제 탐험가!",


        "INFP":
        "감성과 사진을 즐기는 힐링 여행자!",


        "ESTP":
        "체험과 이벤트를 좋아하는 모험가!",


        "ISFJ":
        "따뜻한 지역 문화를 즐기는 여행자!",


        "ISTJ":
        "계획적인 전통문화 탐방가!",


        "ESFP":
        "즐거움과 먹거리를 찾아가는 축제 스타!"

    }



    st.info(
        mbti_description.get(
            mbti,
            "새로운 경험을 찾아 떠나는 축제 탐험가!"
        )
    )



    # MBTI 기반 키워드 검색


    keyword_map = {


        "E":
        [
            "축제",
            "공연",
            "행사"
        ],


        "I":
        [
            "꽃",
            "문화",
            "전통"
        ],


        "S":
        [
            "음식",
            "먹거리",
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
            "역사",
            "전통"
        ],


        "F":
        [
            "사진",
            "꽃",
            "힐링"
        ]

    }



    search_words = []


    for char in mbti:

        search_words += keyword_map.get(
            char,
            []
        )



    pattern = "|".join(
        search_words
    )



    recommended = df[
        df["title"]
        .str.contains(
            pattern,
            case=False,
            na=False
        )
    ]



    if len(recommended) > 0:


        pick = random.choice(
            recommended.to_dict(
                "records"
            )
        )


    else:


        pick = random.choice(
            df.to_dict(
                "records"
            )
        )



    st.subheader(
        "🎪 MBTI 추천 축제"
    )


    st.write(
        f"""
### {pick['title']}

📍 {pick.get('addr1','')}

📅
{pick.get('eventstartdate','')}
~
{pick.get('eventenddate','')}
"""
    )


    st.session_state.selected_festival = pick



# =====================================
# 축제 상세 선택
# =====================================

st.divider()

st.header(
    "🎪 축제 상세 보기"
)



festival_names = df["title"].tolist()



selected_name = st.selectbox(
    "상세 정보를 볼 축제 선택",
    festival_names
)



selected = df[
    df["title"]
    ==
    selected_name
].iloc[0].to_dict()



st.session_state.selected_festival = selected



if selected.get(
    "firstimage"
):

    st.image(
        selected["firstimage"],
        width=400
    )



st.subheader(
    selected.get(
        "title"
    )
)



st.write(
    "📍",
    selected.get(
        "addr1",
        ""
    )
)


st.write(
    "📅",
    selected.get(
        "eventstartdate",
        ""
    ),
    "~",
    selected.get(
        "eventenddate",
        ""
    )
)



# =====================================
# 주변 관광지 검색 함수
# =====================================


def search_nearby_places(
    lat,
    lon
):


    return api_request(

        LOCATION_URL,

        {

            "mapX": lon,

            "mapY": lat,

            "radius": 5000,

            "numOfRows": 10,

            "pageNo": 1,

            "arrange": "A"

        }

    )



# =====================================
# 주변 관광지
# =====================================


st.divider()

st.header(
    "📍 주변 여행 추천"
)



if st.button(
    "주변 관광지 찾기"
):


    try:


        places = search_nearby_places(

            selected["mapy"],

            selected["mapx"]

        )


        st.session_state.nearby_places = places



    except:


        st.warning(
            "위치 정보를 찾을 수 없습니다."
        )



if "nearby_places" in st.session_state:


    st.subheader(
        "🏞️ 주변 관광지"
    )


    for p in st.session_state.nearby_places:


        st.write(
            "📌",
            p.get(
                "title"
            )
        )


        st.write(
            p.get(
                "addr1",
                ""
            )
        )

# =====================================
# 음식점 / 숙박 검색
# =====================================


def search_keyword(
    keyword
):


    return api_request(

        KEYWORD_URL,

        {

            "keyword":
                keyword,

            "numOfRows":
                10,

            "pageNo":
                1,

            "arrange":
                "A"

        }

    )



st.divider()

st.header(
    "🍚 주변 맛집 추천"
)



if st.button(
    "맛집 찾기"
):


    address = selected.get(
        "addr1",
        ""
    )


    if address:


        food_keyword = (
            address.split()[0]
            +
            " 맛집"
        )


        foods = search_keyword(
            food_keyword
        )


        st.session_state.foods = foods



if "foods" in st.session_state:


    if st.session_state.foods:


        for food in st.session_state.foods:


            st.write(
                "🍚",
                food.get(
                    "title"
                )
            )


            st.write(
                food.get(
                    "addr1",
                    ""
                )
            )


            if food.get(
                "firstimage"
            ):

                st.image(
                    food["firstimage"],
                    width=200
                )


    else:

        st.info(
            "주변 맛집 정보를 찾지 못했습니다."
        )



# =====================================
# 숙박 추천
# =====================================


st.header(
    "🏨 주변 숙소 추천"
)



if st.button(
    "숙소 찾기"
):


    address = selected.get(
        "addr1",
        ""
    )


    if address:


        hotel_keyword = (
            address.split()[0]
            +
            " 숙소"
        )


        hotels = search_keyword(
            hotel_keyword
        )


        st.session_state.hotels = hotels



if "hotels" in st.session_state:


    for hotel in st.session_state.hotels:


        st.write(
            "🏨",
            hotel.get(
                "title"
            )
        )


        st.write(
            hotel.get(
                "addr1",
                ""
            )
        )



# =====================================
# 무료 AI 여행 플래너
# =====================================


st.divider()


st.header(
    "🤖 AI 여행 코스 플래너"
)


st.caption(
    "AI API 없이 축제 데이터 기반으로 자동 생성됩니다."
)



duration = st.selectbox(

    "여행 기간",

    [

        "당일치기",

        "1박 2일",

        "2박 3일"

    ]

)



if st.button(
    "✨ 여행 코스 만들기"
):


    festival_name = selected.get(
        "title",
        ""
    )


    style = (
        st.session_state.mbti
        if st.session_state.mbti
        else "일반"
    )



    plan = []



    if duration == "당일치기":


        plan = [

            "10:00 주변 카페 또는 관광지 방문",

            f"13:00 {festival_name} 참여",

            "16:00 주변 명소 산책",

            "18:00 지역 맛집 방문"

        ]



    elif duration == "1박 2일":


        plan = [

            "첫째날 오전 : 주변 관광",

            f"첫째날 오후 : {festival_name} 방문",

            "저녁 : 지역 음식 체험",

            "둘째날 : 근처 관광지 여행"

        ]



    else:


        plan = [

            "1일차 : 지역 관광 및 축제 준비",

            f"2일차 : {festival_name} 집중 체험",

            "3일차 : 주변 명소와 맛집 여행"

        ]



    st.success(
        f"""
🎉 추천 여행 스타일 : {style}

📅 일정 : {duration}
"""
    )



    for item in plan:

        st.write(
            "➡️",
            item
        )



# =====================================
# 준비물 추천
# =====================================


st.divider()


st.header(
    "🎒 축제 준비물 추천"
)



festival_title = selected.get(
    "title",
    ""
)



items = []


if "꽃" in festival_title:

    items += [
        "📷 카메라",
        "🧺 돗자리",
        "🌸 편한 신발"
    ]


elif "물" in festival_title:


    items += [

        "👕 여벌 옷",

        "🧴 수건",

        "💧 물"

    ]


else:


    items += [

        "📱 휴대폰 보조배터리",

        "👟 편한 신발",

        "💳 카드 또는 현금"

    ]



for item in items:

    st.write(
        item
    )



# =====================================
# 지도
# =====================================


st.divider()


st.header(
    "🗺️ 축제 여행 지도"
)



try:


    festival_lat = float(
        selected["mapy"]
    )


    festival_lon = float(
        selected["mapx"]
    )



    m = folium.Map(

        location=[

            festival_lat,

            festival_lon

        ],

        zoom_start=13

    )



    folium.Marker(

        [

            festival_lat,

            festival_lon

        ],

        popup=

        selected["title"],

        tooltip="축제 위치"

    ).add_to(m)



    if "nearby_places" in st.session_state:


        for p in st.session_state.nearby_places:


            try:


                folium.Marker(

                    [

                        float(
                            p["mapy"]
                        ),

                        float(
                            p["mapx"]
                        )

                    ],

                    popup=p["title"],

                    icon=folium.Icon(
                        color="green"
                    )

                ).add_to(m)


            except:

                pass



    st_folium(

        m,

        width=900,

        height=600

    )



except:


    st.info(
        "지도 정보를 표시할 수 없습니다."
    )



# =====================================
# 즐겨찾기
# =====================================


st.divider()


st.header(
    "⭐ 즐겨찾기"
)



if st.button(
    "현재 축제 저장"
):


    if selected not in st.session_state.favorites:


        st.session_state.favorites.append(
            selected
        )


        st.success(
            "저장되었습니다!"
        )



if st.session_state.favorites:


    for f in st.session_state.favorites:


        st.write(

            "⭐",

            f.get(
                "title"
            )

        )
        
