import streamlit as st
import pandas as pd
import plotly.express as px

from stars import stars
from database import add_letter,get_letters

st.set_page_config(
    page_title="⭐ Letters to the Stars",
    layout="wide"
)

st.title("🌌 Letters to the Stars")

st.write("별 하나를 선택해서 편지를 남겨보세요.")

df = pd.DataFrame(stars)

fig = px.scatter(
    df,
    x="x",
    y="y",
    hover_name="name",
    size=[20]*len(df),
)

fig.update_layout(
    paper_bgcolor="black",
    plot_bgcolor="black",
    font_color="white",
)

fig.update_traces(marker=dict(color="yellow"))

event = st.plotly_chart(
    fig,
    use_container_width=True,
)

star = st.selectbox(
    "별 선택",
    df["name"]
)

st.header(f"⭐ {star}")

tab1,tab2 = st.tabs(["편지 쓰기","편지 보기"])

with tab1:

    nickname = st.text_input("닉네임")

    text = st.text_area("편지")

    if st.button("별에게 보내기 ⭐"):

        add_letter(star,nickname,text)

        st.success("편지가 우주로 전송되었습니다!")

with tab2:

    letters = get_letters(star)

    if len(letters)==0:

        st.info("아직 편지가 없습니다.")

    else:

        for letter in letters[::-1]:

            st.markdown(f"""
### ✨ {letter['nickname']}

{letter['letter']}

---
""")
