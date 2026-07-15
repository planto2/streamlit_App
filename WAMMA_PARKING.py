import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium

st.set_page_config(page_title="공영주차장 안내", layout="wide")

st.title("🚗 공영주차장 정보 안내")

# ==========================
# CSV 읽기 함수
# ==========================
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
            return pd.read_csv(
                file,
                encoding=enc,
                sep=None,
                engine="python"
            )
        except Exception:
            continue

    raise ValueError(
        "지원하지 않는 CSV 형식입니다."
    )


# ==========================
# 파일 업로드
# ==========================
uploaded_file = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

# ==========================
# CSV 읽기
# ==========================
if uploaded_file is not None:

    df = load_csv(uploaded_file)

    st.success("데이터를 불러왔습니다.")
    st.dataframe(df)

    # 여기부터 주소검색, 지도 등을 작성

# ==========================
# 주소 검색
# ==========================

st.subheader("🔍 주소 검색")

address = st.text_input("주소를 입력하세요.")

if address:

    result = df[df["주소"].astype(str).str.contains(address, case=False, na=False)]

    if len(result) > 0:

        st.success(f"{len(result)}개의 주차장을 찾았습니다.")

        st.dataframe(result)

    else:

        st.warning("검색 결과가 없습니다.")

# ==========================
# 지도 시각화
# ==========================

st.subheader("🗺️ 공영주차장 지도")

# 위도, 경도 숫자로 변환
df["위도"] = pd.to_numeric(df["위도"], errors="coerce")
df["경도"] = pd.to_numeric(df["경도"], errors="coerce")

# 좌표 없는 행 제거
map_df = df.dropna(subset=["위도", "경도"])

# 지도 중심
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

# MarkerCluster 생성
cluster = MarkerCluster().add_to(m)

# 마커 추가
for _, row in map_df.iterrows():

    popup_html = f"""
    <h4>{row['주차장명']}</h4>

    <hr>

    <b>주소</b><br>
    {row['주소']}<br><br>

    <b>기본요금</b><br>
    {row['기본요금']}<br><br>

    <b>추가요금</b><br>
    {row['추가요금']}
    """

    folium.Marker(
        location=[row["위도"], row["경도"]],
        tooltip=row["주차장명"],
        popup=folium.Popup(
            popup_html,
            max_width=350
        ),
        icon=folium.Icon(
            color="blue",
            icon="info-sign"
        )
    ).add_to(cluster)

st_folium(
    m,
    width=1200,
    height=650
)
