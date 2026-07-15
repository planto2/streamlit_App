import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium


# ==================================
# 페이지 설정
# ==================================

st.set_page_config(
    page_title="공영주차장 안내",
    layout="wide"
)


st.title("🚗 공영주차장 정보 안내")


# ==================================
# CSV 자동 읽기 함수
# ==================================

def load_csv(file):

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr",
        "latin1"
    ]

    for enc in encodings:

        try:
            file.seek(0)

            df = pd.read_csv(
                file,
                encoding=enc,
                sep=None,
                engine="python"
            )

            return df


        except Exception:

            continue


    raise ValueError(
        "CSV 파일을 읽을 수 없습니다. "
        "인코딩 형식을 확인해주세요."
    )



# ==================================
# 데이터 컬럼 확인
# ==================================

def check_columns(df):

    required_columns = [
        "주차장명",
        "주소",
        "위도",
        "경도",
        "기본 주차 요금",
        "추가 단위 요금"
    ]


    missing = []

    for col in required_columns:

        if col not in df.columns:
            missing.append(col)


    return missing



# ==================================
# CSV 업로드
# ==================================

uploaded_file = st.file_uploader(
    "📂 공영주차장 CSV 파일 업로드",
    type=["csv"]
)



# ==================================
# 업로드 후 실행
# ==================================

if uploaded_file is not None:


    # CSV 읽기

    try:

        df = load_csv(uploaded_file)

    except Exception as e:

        st.error(e)
        st.stop()



    # 컬럼명 앞뒤 공백 제거

    df.columns = df.columns.str.strip()



    # 필요한 컬럼 확인

    missing_columns = check_columns(df)


    if missing_columns:

        st.error(
            "필요한 컬럼이 없습니다.\n\n"
            + ", ".join(missing_columns)
        )

        st.stop()



    st.success(
        f"✅ 데이터 로드 완료 "
        f"({len(df):,}개 주차장)"
    )



    # 데이터 미리보기

    with st.expander("📄 CSV 데이터 보기"):

        st.dataframe(df)



    # ==================================
    # 검색 기능
    # ==================================

    st.subheader("🔍 주소 검색")


    keyword = st.text_input(
        "주소 또는 주차장명을 입력하세요"
    )


    search_result = df.copy()



    if keyword:


        search_result = df[
            df["주소"]
            .astype(str)
            .str.contains(
                keyword,
                case=False,
                na=False
            )
            |
            df["주차장명"]
            .astype(str)
            .str.contains(
                keyword,
                case=False,
                na=False
            )
        ]



        if len(search_result) > 0:


            st.success(
                f"{len(search_result)}개의 주차장을 찾았습니다."
            )


            st.dataframe(
                search_result[
                    [
                        "주차장명",
                        "주소",
                        "기본 주차 요금",
                        "추가 단위 요금"
                    ]
                ]
            )


        else:

            st.warning(
                "검색 결과가 없습니다."
            )


    # ==================================
    # 지도 시각화
    # ==================================

    st.subheader("🗺️ 공영주차장 지도")


    # 위도 경도 숫자 변환

    df["위도"] = pd.to_numeric(
        df["위도"],
        errors="coerce"
    )

    df["경도"] = pd.to_numeric(
        df["경도"],
        errors="coerce"
    )


    # 좌표 없는 데이터 제거

    map_df = df.dropna(
        subset=[
            "위도",
            "경도"
        ]
    )


    if len(map_df) == 0:

        st.error(
            "지도에 표시할 좌표 데이터가 없습니다."
        )

        st.stop()



    # 지도 중심 좌표

    center = [
        map_df["위도"].mean(),
        map_df["경도"].mean()
    ]



    # 지도 생성

    m = folium.Map(
        location=center,
        zoom_start=12,
        tiles="OpenStreetMap"
    )



    # 마커 클러스터 생성

    cluster = MarkerCluster().add_to(m)



    # ==================================
    # 마커 생성
    # ==================================

    for _, row in map_df.iterrows():


        # 요금 데이터 처리

        basic_fee = row["기본 주차 요금"]

        if pd.isna(basic_fee):

            basic_fee = "정보 없음"



        extra_fee = row["추가 단위 요금"]

        if pd.isna(extra_fee):

            extra_fee = "정보 없음"



        # 운영시간 처리

        weekday_start = row.get(
            "평일 운영 시작시각(HHMM)",
            "정보 없음"
        )


        weekday_end = row.get(
            "평일 운영 종료시각(HHMM)",
            "정보 없음"
        )



        # 유무료 여부

        free_type = row.get(
            "유무료구분명",
            "정보 없음"
        )



        # 팝업 내용

        popup_html = f"""

        <div style="width:250px">

        <h4>
        🚗 {row['주차장명']}
        </h4>

        <hr>

        📍 <b>주소</b><br>
        {row['주소']}

        <br><br>


        💰 <b>기본 요금</b><br>
        {basic_fee}원


        <br><br>


        ⏱️ <b>추가 요금</b><br>
        {extra_fee}원


        <br><br>


        🅿️ <b>주차 구분</b><br>
        {free_type}


        <br><br>


        🕒 <b>운영시간</b><br>
        {weekday_start}
        ~
        {weekday_end}


        <br><br>


        🚘 <b>주차면</b><br>
        {row['총 주차면']}면


        <br><br>


        ☎️ <b>전화번호</b><br>
        {row['전화번호']}

        </div>

        """



        # 검색 결과 강조

        if keyword and (
            keyword in str(row["주소"])
            or keyword in str(row["주차장명"])
        ):

            marker_color = "red"

        else:

            marker_color = "blue"



        # 마커 추가

        folium.Marker(

            location=[
                row["위도"],
                row["경도"]
            ],

            tooltip=row["주차장명"],


            popup=folium.Popup(
                popup_html,
                max_width=350
            ),


            icon=folium.Icon(
                color=marker_color,
                icon="info-sign"
            )

        ).add_to(cluster)



    # ==================================
    # Streamlit 지도 출력
    # ==================================

    st_folium(

        m,

        width=1200,

        height=650

    )
