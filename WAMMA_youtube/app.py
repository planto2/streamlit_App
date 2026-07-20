##############################################################
# YouTube Comment Analyzer
# Version 1.0
# Part 1
##############################################################

import streamlit as st
import pandas as pd
import numpy as np
import requests
import plotly.express as px
import plotly.graph_objects as go

from wordcloud import WordCloud
from PIL import Image

import matplotlib.pyplot as plt

from googleapiclient.discovery import build

from collections import Counter

from io import BytesIO

import requests
import re
import os
import tempfile

from kiwipiepy import Kiwi

##############################################################
# Streamlit
##############################################################

st.set_page_config(
    page_title="YouTube 댓글 분석기",
    page_icon="📊",
    layout="wide"
)

##############################################################
# 제목
##############################################################

st.title("📊 YouTube 댓글 분석기")

st.caption(
    "YouTube Data API를 이용하여 댓글을 분석합니다."
)

##############################################################
# Sidebar
##############################################################

st.sidebar.title("설정")

API_KEY = st.sidebar.text_input(
    "YouTube API Key",
    type="password"
)

MAX_COMMENTS = st.sidebar.slider(
    "댓글 개수",
    100,
    5000,
    500,
    100
)

##############################################################
# URL 입력
##############################################################

youtube_url = st.text_input(
    "유튜브 URL 입력",
    placeholder="https://www.youtube.com/watch?v=xxxxxxxx"
)

##############################################################
# Video ID 추출
##############################################################

def extract_video_id(url):

    patterns = [

        r"youtu\.be\/([^?&]+)",

        r"youtube\.com\/watch\?v=([^&]+)",

        r"youtube\.com\/embed\/([^?&]+)",

        r"youtube\.com\/shorts\/([^?&]+)"

    ]

    for p in patterns:

        m = re.search(p, url)

        if m:

            return m.group(1)

    return None

##############################################################
# API 연결
##############################################################

def youtube_service(api_key):

    youtube = build(
        "youtube",
        "v3",
        developerKey=api_key
    )

    return youtube

##############################################################
# 영상 정보 가져오기
##############################################################

def get_video_info(youtube, video_id):

    request = youtube.videos().list(

        part="snippet,statistics",

        id=video_id

    )

    response = request.execute()

    if len(response["items"]) == 0:

        return None

    item = response["items"][0]

    info = {

        "title":

        item["snippet"]["title"],

        "channel":

        item["snippet"]["channelTitle"],

        "published":

        item["snippet"]["publishedAt"],

        "thumbnail":

        item["snippet"]["thumbnails"]["high"]["url"],

        "views":

        int(item["statistics"].get("viewCount",0)),

        "likes":

        int(item["statistics"].get("likeCount",0)),

        "comments":

        int(item["statistics"].get("commentCount",0))

    }

    return info

##############################################################
# 댓글 가져오기
##############################################################

def get_comments(

    youtube,

    video_id,

    max_comments

):

    comments=[]

    nextPageToken=None

    while True:

        request=youtube.commentThreads().list(

            part="snippet",

            videoId=video_id,

            maxResults=100,

            pageToken=nextPageToken,

            textFormat="plainText",

            order="time"

        )

        response=request.execute()

        for item in response["items"]:

            c=item["snippet"]["topLevelComment"]["snippet"]

            comments.append({

                "작성자":c["authorDisplayName"],

                "댓글":c["textDisplay"],

                "좋아요":c["likeCount"],

                "작성일":c["publishedAt"]

            })

            if len(comments)>=max_comments:

                return pd.DataFrame(comments)

        nextPageToken=response.get("nextPageToken")

        if nextPageToken is None:

            break

    return pd.DataFrame(comments)

##############################################################
# DataFrame 전처리
##############################################################

def preprocess(df):

    df["작성일"]=pd.to_datetime(df["작성일"])

    df["날짜"]=df["작성일"].dt.date

    df["시간"]=df["작성일"].dt.hour

    df["댓글길이"]=df["댓글"].str.len()

    return df

##############################################################
# 형태소 분석
##############################################################

kiwi=Kiwi()

def extract_keywords(df):

    nouns=[]

    for text in df["댓글"]:

        try:

            tokens=kiwi.tokenize(text)

            for t in tokens:

                if t.tag.startswith("NN"):

                    if len(t.form)>=2:

                        nouns.append(t.form)

        except:

            pass

    return nouns
##############################################################
# 감성 분석 (간단한 사전 기반)
##############################################################

positive_words = [
    "좋다","최고","대박","감동","멋지다","추천","사랑","행복",
    "감사","훌륭","재밌다","재미있다","웃기다","완벽","응원",
    "존경","킹","레전드","최강","굿","awesome","love","best"
]

negative_words = [
    "싫다","최악","별로","실망","나쁘다","짜증","화난다","욕",
    "끔찍","구리다","노잼","재미없다","쓰레기","망했다",
    "불편","거짓","실패","실수","terrible","bad","worst"
]

def sentiment_score(text):

    text = str(text).lower()

    score = 0

    for word in positive_words:
        if word.lower() in text:
            score += 1

    for word in negative_words:
        if word.lower() in text:
            score -= 1

    if score > 0:
        return "긍정"

    elif score < 0:
        return "부정"

    return "중립"


##############################################################
# 감성 분석
##############################################################

def analyze_sentiment(df):

    df["감성"] = df["댓글"].apply(sentiment_score)

    return df


##############################################################
# WordCloud
##############################################################

def create_wordcloud(words):

    if len(words) == 0:
        return None

    text = " ".join(words)

    font_path = "NanumGothic.ttf"

    # Streamlit Cloud에서 폰트가 없으면 다운로드
    if not os.path.exists(font_path):

        url = (
            "https://github.com/google/fonts/raw/main/"
            "ofl/nanumgothic/NanumGothic-Regular.ttf"
        )

        r = requests.get(url)

        with open(font_path, "wb") as f:
            f.write(r.content)


    wc = WordCloud(

        font_path=font_path,

        width=1200,

        height=700,

        background_color="white",

        colormap="tab20"

    ).generate(text)


    return wc


##############################################################
# 키워드 빈도
##############################################################

def keyword_dataframe(words):

    counter = Counter(words)

    top = counter.most_common(30)

    return pd.DataFrame(

        top,

        columns=["키워드","빈도"]

    )


##############################################################
# 시간대별 댓글
##############################################################

def chart_hour(df):

    temp = (

        df.groupby("시간")

        .size()

        .reset_index(name="댓글수")

    )

    fig = px.line(

        temp,

        x="시간",

        y="댓글수",

        markers=True,

        title="시간대별 댓글 작성 추이"

    )

    fig.update_layout(

        xaxis_title="시간",

        yaxis_title="댓글 수"

    )

    return fig


##############################################################
# 날짜별 댓글
##############################################################

def chart_date(df):

    temp = (

        df.groupby("날짜")

        .size()

        .reset_index(name="댓글수")

    )

    fig = px.bar(

        temp,

        x="날짜",

        y="댓글수",

        title="날짜별 댓글 추이"

    )

    return fig


##############################################################
# 감성 차트
##############################################################

def chart_sentiment(df):

    temp = (

        df["감성"]

        .value_counts()

        .reset_index()

    )

    temp.columns=["감성","개수"]

    fig = px.pie(

        temp,

        names="감성",

        values="개수",

        hole=0.4,

        title="감성 분석"

    )

    return fig


##############################################################
# 키워드 TOP30
##############################################################

def chart_keywords(df):

    fig = px.bar(

        df,

        x="빈도",

        y="키워드",

        orientation="h",

        title="키워드 TOP30"

    )

    fig.update_layout(

        yaxis={"categoryorder":"total ascending"}

    )

    return fig


##############################################################
# CSV 다운로드
##############################################################

def csv_download(df):

    return df.to_csv(

        index=False,

        encoding="utf-8-sig"

    ).encode("utf-8-sig")


##############################################################
# Excel 다운로드
##############################################################

def excel_download(df):

    output = BytesIO()

    with pd.ExcelWriter(

        output,

        engine="xlsxwriter"

    ) as writer:

        df.to_excel(

            writer,

            index=False

        )

    return output.getvalue()
##############################################################
# 메인 실행부
##############################################################

if youtube_url:

    video_id = extract_video_id(youtube_url)


    if video_id is None:

        st.error(
            "올바른 YouTube URL을 입력해주세요."
        )

    else:

        st.video(
            youtube_url
        )


        if API_KEY:


            try:

                youtube = youtube_service(
                    API_KEY
                )


                ##########################################
                # 영상 정보
                ##########################################

                video_info = get_video_info(

                    youtube,

                    video_id

                )


                if video_info:


                    st.divider()

                    col1, col2 = st.columns(
                        [1,2]
                    )


                    with col1:

                        st.image(

                            video_info["thumbnail"]

                        )


                    with col2:

                        st.subheader(

                            video_info["title"]

                        )

                        st.write(

                            "채널 : ",

                            video_info["channel"]

                        )

                        st.write(

                            "게시일 : ",

                            video_info["published"]

                        )


                        c1,c2,c3 = st.columns(3)


                        c1.metric(

                            "조회수",

                            f'{video_info["views"]:,}'

                        )


                        c2.metric(

                            "좋아요",

                            f'{video_info["likes"]:,}'

                        )


                        c3.metric(

                            "댓글",

                            f'{video_info["comments"]:,}'

                        )


                    st.divider()


                    ##########################################
                    # 분석 버튼
                    ##########################################

                    if st.button(
                        "🚀 댓글 분석 시작"
                    ):


                        progress = st.progress(
                            0
                        )


                        status = st.empty()


                        status.info(
                            "댓글 수집 중..."
                        )


                        progress.progress(
                            20
                        )


                        ##################################
                        # 댓글 가져오기
                        ##################################

                        comments_df = get_comments(

                            youtube,

                            video_id,

                            MAX_COMMENTS

                        )


                        if len(comments_df)==0:


                            st.warning(

                                "댓글이 없습니다."

                            )


                            st.stop()



                        progress.progress(
                            50
                        )


                        status.info(

                            "댓글 분석 중..."

                        )


                        ##################################
                        # 전처리
                        ##################################

                        comments_df = preprocess(

                            comments_df

                        )


                        ##################################
                        # 감성 분석
                        ##################################

                        comments_df = analyze_sentiment(

                            comments_df

                        )


                        ##################################
                        # 키워드 추출
                        ##################################

                        keywords = extract_keywords(

                            comments_df

                        )


                        keyword_df = keyword_dataframe(

                            keywords

                        )


                        progress.progress(
                            80
                        )


                        status.info(

                            "결과 생성 중..."

                        )


                        ##################################
                        # 결과 저장
                        ##################################

                        st.session_state["data"] = comments_df

                        st.session_state["keywords"] = keyword_df



                        progress.progress(
                            100
                        )


                        status.success(

                            "분석 완료!"

                        )



            except Exception as e:


                st.error(

                    f"오류 발생 : {e}"

                )


        else:

            st.info(

                "왼쪽 사이드바에서 YouTube API Key를 입력하세요."

            )



##############################################################
# 분석 결과 출력
##############################################################

if "data" in st.session_state:


    df = st.session_state["data"]

    keyword_df = st.session_state["keywords"]


    st.divider()


    st.header(
        "📊 분석 결과"
    )


    #############################################
    # 기본 통계
    #############################################

    a,b,c,d = st.columns(4)


    a.metric(

        "총 댓글",

        len(df)

    )


    b.metric(

        "평균 댓글 길이",

        f'{df["댓글길이"].mean():.1f}'

    )


    c.metric(

        "최고 댓글 좋아요",

        f'{df["좋아요"].max():,}'

    )


    d.metric(

        "분석 키워드",

        len(keyword_df)

    )


    st.divider()


    #############################################
    # 그래프 영역
    #############################################

    left,right = st.columns(2)


    with left:


        st.plotly_chart(

            chart_hour(df),

            use_container_width=True

        )


    with right:


        st.plotly_chart(

            chart_date(df),

            use_container_width=True

        )



    st.plotly_chart(

        chart_sentiment(df),

        use_container_width=True

    )


    st.plotly_chart(

        chart_keywords(keyword_df),

        use_container_width=True

    )



    #############################################
    # 워드클라우드
    #############################################

    st.subheader(

        "☁️ 한글 워드클라우드"

    )


    words = extract_keywords(df)


    wc = create_wordcloud(

        words

    )


    if wc:


        fig,ax = plt.subplots(

            figsize=(12,7)

        )


        ax.imshow(

            wc

        )


        ax.axis(

            "off"

        )


        st.pyplot(

            fig

        )


    #############################################
    # 데이터
    #############################################

    st.subheader(

        "💬 댓글 데이터"

    )


    st.dataframe(

        df,

        use_container_width=True

    )


    #############################################
    # 다운로드
    #############################################

    col1,col2 = st.columns(2)


    with col1:


        st.download_button(

            "CSV 다운로드",

            csv_download(df),

            "youtube_comments.csv",

            "text/csv"

        )


    with col2:


        st.download_button(

            "Excel 다운로드",

            excel_download(df),

            "youtube_comments.xlsx"

        )
##############################################################
# 추가 분석 기능
##############################################################

def top_liked_comments(df, n=10):

    result = (

        df.sort_values(
            "좋아요",
            ascending=False
        )

        .head(n)

    )

    return result[
        [
            "작성자",
            "댓글",
            "좋아요"
        ]
    ]



##############################################################
# 작성자 TOP
##############################################################

def top_users(df, n=10):

    result = (

        df["작성자"]

        .value_counts()

        .head(n)

        .reset_index()

    )

    result.columns=[
        "작성자",
        "댓글수"
    ]

    return result



##############################################################
# 이모지 분석
##############################################################

def extract_emojis(text):

    emoji_pattern = re.compile(

        "["

        "\U0001F300-\U0001F64F"

        "\U0001F680-\U0001F6FF"

        "\U0001F900-\U0001F9FF"

        "]",

        flags=re.UNICODE

    )

    return emoji_pattern.findall(str(text))



def emoji_analysis(df):

    emojis=[]

    for text in df["댓글"]:

        emojis.extend(
            extract_emojis(text)
        )

    return pd.DataFrame(

        Counter(emojis)

        .most_common(20),

        columns=[
            "이모지",
            "사용횟수"
        ]

    )



##############################################################
# 해시태그 분석
##############################################################

def hashtag_analysis(df):

    tags=[]

    for text in df["댓글"]:

        result=re.findall(

            r"#\w+",

            str(text)

        )

        tags.extend(result)


    return pd.DataFrame(

        Counter(tags)

        .most_common(20),

        columns=[
            "해시태그",
            "횟수"
        ]

    )



##############################################################
# 추가 결과 화면
##############################################################

if "data" in st.session_state:


    df=st.session_state["data"]


    st.divider()

    st.header(
        "🔥 추가 분석"
    )


    tab1,tab2,tab3,tab4 = st.tabs(

        [
            "👍 인기 댓글",
            "👤 작성자",
            "😀 이모지",
            "#️⃣ 해시태그"
        ]

    )


    with tab1:

        liked = top_liked_comments(df)


        st.dataframe(

            liked,

            use_container_width=True

        )


    with tab2:


        users = top_users(df)


        st.plotly_chart(

            px.bar(

                users,

                x="댓글수",

                y="작성자",

                orientation="h",

                title="댓글 작성자 TOP10"

            ),

            use_container_width=True

        )


    with tab3:


        emojis = emoji_analysis(df)


        if len(emojis)>0:


            st.dataframe(

                emojis,

                use_container_width=True

            )

        else:

            st.info(

                "사용된 이모지가 없습니다."

            )


    with tab4:


        tags=hashtag_analysis(df)


        if len(tags)>0:


            st.dataframe(

                tags,

                use_container_width=True

            )

        else:

            st.info(

                "해시태그가 없습니다."

            )


##############################################################
# Footer
##############################################################

st.sidebar.divider()

st.sidebar.caption(

    "YouTube Comment Analyzer v1.0"

)

