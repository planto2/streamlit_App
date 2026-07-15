import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(page_title="공영주차장 안내", layout="wide")

st.title("🚗 공영주차장 정보 안내")

uploaded_file = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

if uploaded_file:

    df = pd.read_csv(uploaded_file)

    st.success("데이터 업로드 완료!")

    st.subheader("데이터 미리보기")
    st.dataframe(df)

    ###################################
    # 주소 검색
    ###################################

    st.subheader("주소 검색")

    address = st.text_input("주소를 입력하세요")

    if address:

        result = df[df["주소"].str.contains(address, case=False, na=False)]

        if len(result):

            st.success(f"{len(result)}개의 주차장을 찾았습니다.")

            for _, row in result.iterrows():

                st.markdown(f"""
### {row['주차장명']}

**주소**

{row['주소']}

**기본요금**

{row['기본요금']}

**추가요금**

{row['추가요금']}
""")

        else:

            st.error("검색 결과가 없습니다.")

    ###################################
    # 지도
    ###################################

    st.subheader("공영주차장 지도")

    center_lat = df["위도"].mean()
    center_lon = df["경도"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12
    )

    for _, row in df.iterrows():

        popup = f"""
<b>{row['주차장명']}</b><br>
주소 : {row['주소']}<br>
기본요금 : {row['기본요금']}<br>
추가요금 : {row['추가요금']}
"""

        tooltip = f"""
{row['주차장명']}
"""

        folium.Marker(
            [row["위도"], row["경도"]],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color="blue", icon="info-sign")
        ).add_to(m)

    st_folium(
        m,
        width=1000,
        height=600
    )
