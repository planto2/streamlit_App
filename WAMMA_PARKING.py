import streamlit as st
import pandas as pd
import folium
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
