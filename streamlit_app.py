import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# 페이지 설정
st.set_page_config(page_title="터널 현장보고 작성기", layout="wide")

# --- 밴드 설정 (발급받은 토큰과 키를 입력하세요) ---
BAND_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN" 
TARGET_BAND_KEY = "YOUR_BAND_KEY"

# 1. 데이터 설정
TUNNELS = {
    "국도19호선 느릅재터널": [["괴산", "괴산IC", "양방향"], False],
    "국도3호선 용관터널": [["수안보", "제천", "양방향"], True],
    "국도36호선 토계울1터널": [["청주", "충주", "양방향"], True],
    "국도36호선 토계울2터널": [["청주", "충주", "양방향"], True],
    "국도36호선 주덕터널": [["청주", "충주", "양방향"], True]
}

# 사고 유형에 공사 포함
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
    files = {'image': image_file.getvalue()}
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY}
    try:
        res = requests.post(url, params=params, files=files).json()
        return res.get("result_data", {}).get("photos", [{}])[0].get("photo_id")
    except: return None

def post_to_band(content, photo_id=None):
    url = "https://openapi.band.us/v2/band/post/create"
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY, "content": content, "do_push": True}
    if photo_id: params["photos"] = photo_id
    return requests.post(url, data=params).json()

if 'report_time' not in st.session_state:
    st.session_state.report_time = get_now_str()

st.title("🚀 터널 현장보고 작성기")

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 정보 입력")
    
    # 유형 선택 (교통사고, 화재사고, 공사)
    a_type = st.selectbox("유형 선택", ACCIDENT_TYPES)
    
    # 공사일 때와 사고일 때 입력 폼 분리
    tunnel_name = st.selectbox("터널 선택", list(TUNNELS.keys()))
    directions = TUNNELS[tunnel_name][0]
    direction = st.selectbox("방향", directions)

    st.divider()

    if a_type == "공사":
        # --- 공사 전용 입력 ---
        work_name = st.text_input("공사명", placeholder="예: 터널 투광등 교체 작업")
        work_method = st.text_input("통제방법", placeholder="예: 1차로 차단")
        
        # 공사 보고서 양식 (요청하신 대로 제목에서 단계 삭제 및 본문 간소화)
        report_text = f"[{tunnel_name}]\n\n{direction}방향 {work_name} {work_method}\n안전운전하세요."

    else:
        # --- 교통사고 / 화재사고 전용 입력 ---
        r_type = st.selectbox("보고 단계", REPORT_TYPES, index=0)
        lane_needed = TUNNELS[tunnel_name][1]
        loc_detail = st.radio("상세 위치", LOC_DETAILS, horizontal=True)
        
        c_pos1, c_pos2 = st.columns(2)
        with c_pos1: lane = st.selectbox("차로", LANES) if lane_needed else ""
        with c_pos2: dist = st.text_input("거리(m)", placeholder="숫자만 입력")

        time_str = st.text_input("일시", st.session_state.report_time)
        detect_way = st.text_input("최초 인지", "CCTV 확인")
        manager = st.text_input("관리 부서", "충주국토관리사무소")
        desc = st.text_input("사고 내용", placeholder="예: 승용차 2대 추돌")
        status = st.text_input("진행 상황", "현장 출동 및 파악 중" if r_type == "최초" else "상황 종료")
        cause = st.text_input("사고 원인", "확인중")
        human = st.text_input("인명 피해", "없음")
        traffic = st.text_input("정체 현황", "원활")

        # 사고 보고서 양식
        report_text = f"""[{tunnel_name} {a_type} ({r_type}) 보고]

ㅇ일시 : {time_str}분경
ㅇ최초인지 : {detect_way}
ㅇ위치 : {tunnel_name} {loc_detail}{f' {lane}' if lane else ''}{f' {dist}m' if dist else ''} ({direction}방향)
ㅇ관리 : {manager}
ㅇ내용 : {desc if desc else '내용 확인 중'}
ㅇ진행상황 : {status}
ㅇ원인 : {cause}
ㅇ인명피해 : {human}
ㅇ정체현황 : {traffic}"""

    st.divider()
    uploaded_file = st.file_uploader("📷 현장 사진 첨부 (카메라/갤러리)", type=['jpg', 'jpeg', 'png'])

with col2:
    st.subheader("📋 보고서 미리보기")
    st.text_area("결과물", report_text, height=400)
    
    if st.button("📢 네이버 밴드에 즉시 게시"):
        if BAND_ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
            st.warning("먼저 밴드 토큰을 입력해주세요.")
        else:
            with st.spinner("밴드 전송 중..."):
                photo_id = None
                if uploaded_file:
                    photo_id = upload_image_to_band(uploaded_file)
                
                result = post_to_band(report_text, photo_id)
                if result.get("result_code") == 1:
                    st.success("✅ 성공적으로 게시되었습니다!")
                else:
                    st.error("❌ 게시 실패. API 설정을 확인하세요.")
