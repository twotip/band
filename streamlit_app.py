import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

st.set_page_config(page_title="터널 밴드보고 작성기", layout="wide")

st.markdown("""
    <style>
    .main-title { font-size: 20px !important; font-weight: bold; margin-bottom: 10px; color: #FFFFFF; }
    .sub-title { font-size: 16px !important; font-weight: bold; margin-top: 5px; }
    .stSelectbox label, .stTextInput label, .stRadio label { font-size: 13px !important; }
    div[data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
    </style>
""", unsafe_allow_html=True)

# ✅ secrets 권장 (없으면 기존 값 fallback)
BAND_ACCESS_TOKEN = st.secrets.get("BAND_ACCESS_TOKEN", "YOUR_ACCESS_TOKEN")
TARGET_BAND_KEY = st.secrets.get("TARGET_BAND_KEY", "YOUR_BAND_KEY")

# ✅ 방향은 "문자열 리스트"로 (이중 리스트 제거)
TUNNELS = {
    "국도19호선 느릅재터널": (["괴산→괴산IC", "괴산IC→괴산", "양방향"], False),
    "국도3호선 용관터널": (["수안보→제천", "제천→수안보", "양방향"], True),
    "국도36호선 토계울1터널": (["청주→충주", "충주→청주", "양방향"], True),
    "국도36호선 토계울2터널": (["청주→충주", "충주→청주", "양방향"], True),
    "국도36호선 주덕터널": (["청주→충주", "충주→청주", "양방향"], True),
}

ACCIDENT_TYPES = ["교통사고", "화재사고", "공사"]
REPORT_TYPES = ["최초", "중간", "최종"]
LOC_DETAILS = ["터널내", "입구부", "출구부"]
LANES = ["1차로", "2차로", "갓길", "전차로"]

def get_now_str():
    kst = timezone(timedelta(hours=9))
    now_kst = datetime.now(kst)
    weekday_map = ["월", "화", "수", "목", "금", "토", "일"]
    return now_kst.strftime(f"%Y.%m.%d({weekday_map[now_kst.weekday()]}) %H:%M")

def upload_image_to_band(image_file):
    url = "https://openapi.band.us/v2/album/photo/create"
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY}

    # ✅ files 형식 수정
    files = {
        "image": (image_file.name, image_file.getvalue(), image_file.type)
    }

    try:
        res = requests.post(url, params=params, files=files, timeout=20).json()
        return res.get("result_data", {}).get("photos", [{}])[0].get("photo_id")
    except Exception:
        return None

def post_to_band(content, photo_id=None):
    url = "https://openapi.band.us/v2/band/post/create"
    data = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY, "content": content, "do_push": True}
    if photo_id:
        data["photos"] = photo_id
    return requests.post(url, data=data, timeout=20).json()

if "report_time" not in st.session_state:
    st.session_state.report_time = get_now_str()

st.markdown('<p class="main-title">🚀 터널 밴드보고 작성기</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="sub-title">📝 정보 입력</p>', unsafe_allow_html=True)

    a_type = st.selectbox("유형 선택", ACCIDENT_TYPES)
    tunnel_name = st.selectbox("터널 선택", list(TUNNELS.keys()))

    directions, lane_needed = TUNNELS[tunnel_name]
    direction_val = st.selectbox("방향", directions)

    # ✅ 표시용 방향 문구
    disp_direction = "양방향" if direction_val == "양방향" else f"{direction_val} 방향"

    st.divider()

    if a_type == "공사":
        work_name = st.text_input("공사명", value="터널 물청소 작업")
        work_lane = st.selectbox("차단 차로", LANES) if lane_needed else ""

        lane_str = f" {work_lane}" if work_lane else ""
        report_text = f"[{tunnel_name}]\n\n{disp_direction} {work_name}{lane_str} 차단\n안전운전하세요."

    else:
        r_type = st.selectbox("보고 단계", REPORT_TYPES, index=0)
        loc_detail = st.radio("상세 위치", LOC_DETAILS, horizontal=True)

        c_pos1, c_pos2 = st.columns(2)
        with c_pos1:
            lane = st.selectbox("사고 차로", LANES) if lane_needed else ""
        with c_pos2:
            dist = st.text_input("거리(m)", placeholder="예: 100")

        time_str = st.text_input("일시", st.session_state.report_time)
        detect_way = st.text_input("최초 인지", "CCTV 확인")
        manager = st.text_input("관리 부서", "충주국토관리사무소")
        desc = st.text_input("사고 내용", placeholder="내용 입력")
        status = st.text_input("진행 상황", "현장 출동 중" if r_type == "최초" else "상황 종료")
        cause = st.text_input("사고 원인", "확인중")
        human = st.text_input("인명 피해", "없음")
        traffic = st.text_input("정체 현황", "원활")

        report_text = f"""[{tunnel_name} {a_type} ({r_type}) 보고]

ㅇ일시 : {time_str}분경
ㅇ최초인지 : {detect_way}
ㅇ위치 : {tunnel_name} {loc_detail}{f' {lane}' if lane else ''}{f' {dist}m' if dist else ''} ({disp_direction})
ㅇ관리 : {manager}
ㅇ내용 : {desc if desc else '내용 확인 중'}
ㅇ진행상황 : {status}
ㅇ원인 : {cause}
ㅇ인명피해 : {human}
ㅇ정체현황 : {traffic}"""

    st.divider()
    uploaded_file = st.file_uploader("📷 사진 첨부 (카메라)", type=["jpg", "jpeg", "png"])

with col2:
    st.markdown('<p class="sub-title">📋 보고서 미리보기</p>', unsafe_allow_html=True)
    st.text_area("결과물", report_text, height=300)

    if st.button("📢 밴드에 즉시 게시"):
        if BAND_ACCESS_TOKEN == "YOUR_ACCESS_TOKEN" or TARGET_BAND_KEY == "YOUR_BAND_KEY":
            st.warning("밴드 토큰/키를 설정해 주세요. (secrets.toml 권장)")
        else:
            with st.spinner("전송 중..."):
                photo_id = upload_image_to_band(uploaded_file) if uploaded_file else None
                result = post_to_band(report_text, photo_id)

                if result.get("result_code") == 1:
                    st.success("✅ 게시 성공!")
                else:
                    st.error(f"❌ 실패: {result}")
