import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# =========================
# Page config
# =========================
st.set_page_config(page_title="터널 밴드보고 작성기", layout="wide")

# =========================
# CSS
# =========================
st.markdown("""
<style>
.main-title { font-size:22px; font-weight:bold; color:#007BFF; margin-bottom:15px; }
.sub-title { font-size:17px; font-weight:bold; margin-top:10px; }
.stSelectbox label, .stTextInput label, .stRadio label { font-size:14px; }
</style>
""", unsafe_allow_html=True)

# =========================
# Band 설정
# =========================
BAND_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
TARGET_BAND_KEY = "YOUR_BAND_KEY"

# =========================
# 데이터
# =========================
TUNNELS = {
    "국도19호선 느릅재터널": (["괴산", "괴산IC", "양방향"], False),
    "국도3호선 용관터널": (["수안보", "제천", "양방향"], True),
    "국도36호선 토계울1터널": (["청주", "충주", "양방향"], True),
    "국도36호선 토계울2터널": (["청주", "충주", "양방향"], True),
    "국도36호선 주덕터널": (["청주", "충주", "양방향"], True),
}

ACCIDENT_TYPES = ["교통사고", "화재사고", "공사"]
REPORT_TYPES = ["최초", "중간", "최종"]
LOC_DETAILS = ["터널내", "입구부", "출구부"]
LANES = ["1차로", "2차로", "갓길", "전차로"]

# =========================
# 함수
# =========================
def get_now_str():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    wk = ["월","화","수","목","금","토","일"]
    return now.strftime(f"%Y.%m.%d({wk[now.weekday()]}) %H:%M")

def upload_image_to_band(image):
    url = "https://openapi.band.us/v2/album/photo/create"
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY}
    files = {"image": (image.name, image.getvalue(), image.type)}
    try:
        res = requests.post(url, params=params, files=files, timeout=20).json()
        return res.get("result_data", {}).get("photos", [{}])[0].get("photo_id")
    except:
        return None

def post_to_band(content, photo_id=None):
    url = "https://openapi.band.us/v2/band/post/create"
    data = {
        "access_token": BAND_ACCESS_TOKEN,
        "band_key": TARGET_BAND_KEY,
        "content": content,
        "do_push": True,
    }
    if photo_id:
        data["photos"] = photo_id
    return requests.post(url, data=data, timeout=20).json()

# =========================
# 세션
# =========================
if "report_time" not in st.session_state:
    st.session_state.report_time = get_now_str()

# =========================
# UI
# =========================
st.markdown('<p class="main-title">🚀 터널 밴드보고 작성기</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

# =========================
# 입력
# =========================
with col1:
    st.markdown('<p class="sub-title">📝 정보 입력</p>', unsafe_allow_html=True)

    a_type = st.selectbox("유형", ACCIDENT_TYPES)
    tunnel_name = st.selectbox("터널", list(TUNNELS.keys()))

    directions, lane_needed = TUNNELS[tunnel_name]
    direction_val = st.selectbox("방향", directions)

    direction_tag = direction_val if direction_val == "양방향" else f"{direction_val}방향"

    st.divider()

    # ===== 공사 =====
    if a_type == "공사":
        work_name = st.text_input("공사명", "터널 물청소 작업")

        # 느릅재터널
        if "느릅재터널" in tunnel_name:
            control = st.radio(
                "통제 방식",
                ["전면차단통제", "부분통제"],
                horizontal=True
            )

            if control == "전면차단통제":
                flow = "우회중"
                st.info("전면차단통제 시 차량 소통 방식은 '우회중'으로 고정됩니다.")
                report_text = (
                    f"[{tunnel_name}]\n\n"
                    f"{direction_tag} {work_name} 전면차단통제 "
                    f"{flow} 안전운전하세요."
                )
            else:
                flow = st.selectbox("차량 소통 방식", ["차량교차운행중", "우회중"], index=0)
                report_text = (
                    f"[{tunnel_name}]\n\n"
                    f"{direction_tag} {work_name} 부분통제 "
                    f"{flow} 안전운전하세요."
                )

        # 기타 터널
        else:
            lane = st.selectbox("차단 차로", LANES) if lane_needed else ""
            lane_str = f" {lane}" if lane else ""
            report_text = (
                f"[{tunnel_name}]\n\n"
                f"{direction_tag} {work_name}{lane_str} 통제\n"
                f"안전운전하세요."
            )

    # ===== 사고 / 화재 =====
    else:
        r_type = st.selectbox("보고 단계", REPORT_TYPES)
        loc = st.radio("위치", LOC_DETAILS, horizontal=True)

        c1, c2 = st.columns(2)
        with c1:
            lane = st.selectbox("차로", LANES) if lane_needed else ""
        with c2:
            dist = st.text_input("거리(m)")

        report_text = (
            f"[{tunnel_name} {a_type} ({r_type}) 보고]\n\n"
            f"ㅇ일시 : {st.session_state.report_time}\n"
            f"ㅇ위치 : {tunnel_name} {loc} {direction_tag}\n"
            f"ㅇ차로 : {lane if lane else '미확인'}\n"
            f"ㅇ내용 : 확인 중"
        )

    uploaded_file = st.file_uploader("📷 사진 첨부", type=["jpg","jpeg","png"])

# =========================
# 미리보기 / 전송
# =========================
with col2:
    st.markdown('<p class="sub-title">📋 보고서 미리보기</p>', unsafe_allow_html=True)
    st.text_area("결과물", report_text, height=350)

    if st.button("📢 밴드에 즉시 게시", use_container_width=True):
        if BAND_ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
            st.warning("밴드 토큰을 입력하세요.")
        else:
            with st.spinner("전송 중..."):
                photo_id = upload_image_to_band(uploaded_file) if uploaded_file else None
                res = post_to_band(report_text, photo_id)
                if res.get("result_code") == 1:
                    st.success("게시 완료")
                else:
                    st.error(res)

    if st.button("🔄 시간 새로고침", use_container_width=True):
        st.session_state.report_time = get_now_str()
        st.rerun()
