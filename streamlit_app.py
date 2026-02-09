import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# 1. Page config
st.set_page_config(page_title="터널 밴드보고 작성기", layout="wide")

# 2. CSS 스타일
st.markdown("""
<style>
.main-title { font-size:22px !important; font-weight:bold; color:#007BFF; margin-bottom:15px; }
.sub-title { font-size:17px !important; font-weight:bold; margin-top:10px; color:#333333; }
.stSelectbox label, .stTextInput label, .stRadio label { font-size:14px !important; }
div[data-testid="stVerticalBlock"] { gap: 0.7rem !important; }
</style>
""", unsafe_allow_html=True)

# 3. Band 설정
BAND_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
TARGET_BAND_KEY = "YOUR_BAND_KEY"

# 4. 터널 데이터
TUNNELS = {
    "국도19호선 느릅재터널": (["괴산", "괴산IC", "양방향"], False),
    "국도3호선 용관터널": (["수안보", "제천", "양방향"], True),
    "국도36호선 토계울1터널": (["청주", "충주", "양방향"], True),
    "국도36호선 토계울2터널": (["청주", "충주", "양방향"], True),
    "국도36호선 주덕터널": (["청주", "충주", "양방향"], True),
}

ACCIDENT_TYPES = ["차량사고", "화재사고", "공사"]
REPORT_TYPES = ["최초", "중간", "최종"]
LOC_DETAILS = ["터널내", "입구부", "출구부"]
LANES = ["1차로", "2차로", "갓길", "전차로"]

# --- 함수 정의 ---
def get_now_str():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)
    wk = ["월","화","수","목","금","토","일"]
    return now.strftime(f"%Y.%m.%d({wk[now.weekday()]}) %H:%M")

def upload_image_to_band(image_file):
    url = "https://openapi.band.us/v2/album/photo/create"
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY}
    try:
        files = {"image": (image_file.name, image_file.getvalue(), image_file.type)}
        res = requests.post(url, params=params, files=files, timeout=20).json()
        return res.get("result_data", {}).get("photos", [{}])[0].get("photo_id")
    except:
        return None

def post_to_band(content, photo_id=None):
    url = "https://openapi.band.us/v2/band/post/create"
    data = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY, "content": content, "do_push": True}
    if photo_id:
        data["photos"] = photo_id
    return requests.post(url, data=data, timeout=20).json()

# --- 세션 상태 ---
if "report_time" not in st.session_state:
    st.session_state.report_time = get_now_str()

# --- 메인 레이아웃 ---
st.markdown('<p class="main-title">🚀 터널 밴드보고 작성기</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1.2])

with col1:
    st.markdown('<p class="sub-title">📝 정보 입력</p>', unsafe_allow_html=True)
    a_type = st.selectbox("유형 선택", ACCIDENT_TYPES)
    tunnel_name = st.selectbox("터널 선택", list(TUNNELS.keys()))

    directions, lane_needed = TUNNELS[tunnel_name]
    direction_val = st.selectbox("방향", directions)
    direction_tag = direction_val if direction_val == "양방향" else f"{direction_val}방향"

    st.divider()

    # ===== [유지] 공사 파트 (느릅재 특화 로직 포함) =====
    if a_type == "공사":
        work_name = st.text_input("공사명", value="터널 물청소 작업")
        if "느릅재터널" in tunnel_name:
            control = st.radio("통제 방식", ["전면차단통제", "부분통제"], horizontal=True)
            if control == "전면차단통제":
                flow = "우회중"
                report_text = f"[{tunnel_name}]\n\n{direction_tag} {work_name} 전면차단통제 {flow} 안전운전하세요."
            else:
                flow = st.selectbox("차량 소통 방식", ["차량교차운행중", "우회중"], index=0)
                report_text = f"[{tunnel_name}]\n\n{direction_tag} {work_name} 부분통제 {flow} 안전운전하세요."
        else:
            lane = st.selectbox("차단 차로", LANES) if lane_needed else ""
            lane_str = f" {lane}" if lane else ""
            report_text = f"[{tunnel_name}]\n\n{direction_tag} {work_name}{lane_str} 통제\n안전운전하세요."

    # ===== [기존 고도화안] 사고 / 화재 파트 =====
    else:
        r_type = st.selectbox("보고 단계", REPORT_TYPES, index=0)
        loc_detail = st.radio("상세 위치", LOC_DETAILS, horizontal=True)

        c_pos1, c_pos2 = st.columns(2)
        with c_pos1:
            lane = st.selectbox("사고 차로", LANES) if lane_needed else ""
        with c_pos2:
            dist = st.text_input("거리(m)", placeholder="예: 100")

        time_str = st.text_input("일시", st.session_state.report_time)
        detect_way = st.text_input("최초 인지", value="느릅재터널 CCTV 확인")
        manager = st.text_input("관리 부서", "충주국토관리사무소")
        desc = st.text_input("사고 내용", placeholder="내용 입력")
        status = st.text_input("진행 상황", "현장 출동 중" if r_type == "최초" else "상황 종료")
        cause = st.text_input("사고 원인", "확인중")
        human = st.text_input("인명 피해", "없음")
        traffic = st.text_input("정체 현황", "원활")

        pos_lane = f" {lane}" if lane else ""
        pos_dist = f" {dist}m" if dist else ""

        report_text = (
            f"[{tunnel_name} {a_type} ({r_type}) 보고]\n\n"
            f"ㅇ일시 : {time_str}분경\n"
            f"ㅇ최초인지 : {detect_way}\n"
            f"ㅇ위치 : {tunnel_name} {loc_detail}{pos_lane}{pos_dist} ({direction_tag})\n"
            f"ㅇ관리 : {manager}\n"
            f"ㅇ내용 : {desc if desc else '내용 확인 중'}\n"
            f"ㅇ진행상황 : {status}\n"
            f"ㅇ원인 : {cause}\n"
            f"ㅇ인명피해 : {human}\n"
            f"ㅇ정체현황 : {traffic}"
        )

    st.divider()
    uploaded_file = st.file_uploader("📷 사진 첨부", type=["jpg", "jpeg", "png"])
    if uploaded_file:
        st.image(uploaded_file, caption="업로드 대기 중", width=250)

with col2:
    st.markdown('<p class="sub-title">📋 보고서 미리보기</p>', unsafe_allow_html=True)
    final_report = st.text_area("결과물 (수정 가능)", report_text, height=450)

    if st.button("📢 밴드에 즉시 게시", use_container_width=True):
        if BAND_ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
            st.warning("밴드 토큰을 입력해 주세요.")
        else:
            with st.spinner("전송 중..."):
                photo_id = upload_image_to_band(uploaded_file) if uploaded_file else None
                result = post_to_band(final_report, photo_id)
                if result.get("result_code") == 1:
                    st.success("✅ 게시 성공!")
                else:
                    st.error(f"❌ 실패: {result}")

    if st.button("🔄 시간 새로고침", use_container_width=True):
        st.session_state.report_time = get_now_str()
        st.rerun()
