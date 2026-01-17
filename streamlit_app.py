import streamlit as st
import requests
from datetime import datetime, timedelta, timezone

# 1. 페이지 설정
st.set_page_config(page_title="터널 밴드보고 작성기", layout="wide")

# 2. 모바일 최적화 스타일
st.markdown("""
    <style>
    .main-title {
        font-size: 20px !important;
        font-weight: bold;
        margin-bottom: 10px;
        color: #FFFFFF;
    }
    .sub-title {
        font-size: 16px !important;
        font-weight: bold;
        margin-top: 5px;
    }
    .stSelectbox label, .stTextInput label, .stRadio label {
        font-size: 13px !important;
    }
    div[data-testid="stVerticalBlock"] {
        gap: 0.5rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 밴드 설정 (발급받은 토큰과 키를 입력하세요) ---
BAND_ACCESS_TOKEN = "YOUR_ACCESS_TOKEN"
TARGET_BAND_KEY = "YOUR_BAND_KEY"

# 3. 터널 데이터 설정 (느릅재터널은 두번째 값이 False로 차로 비활성)
# ✅ 방향 리스트가 "이중 리스트"가 되지 않도록 수정
TUNNELS = {
    "국도19호선 느릅재터널": (["괴산", "괴산IC", "양방향"], False),
    "국도3호선 용관터널": (["수안보", "제천", "양방향"], True),
    "국도36호선 토계울1터널": (["청주", "충주", "양방향"], True),
    "국도36호선 토계울2터널": (["청주", "충주", "양방향"], True),
    "국도36호선 주덕터널": (["청주", "충주", "양방향"], True)
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
    # ✅ requests files 형식 개선(권장)
    files = {"image": (image_file.name, image_file.getvalue(), image_file.type)}
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY}
    try:
        res = requests.post(url, params=params, files=files).json()
        return res.get("result_data", {}).get("photos", [{}])[0].get("photo_id")
    except:
        return None

def post_to_band(content, photo_id=None):
    url = "https://openapi.band.us/v2/band/post/create"
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY, "content": content, "do_push": True}
    if photo_id:
        params["photos"] = photo_id
    return requests.post(url, data=params).json()

# ✅ 기본 보고 시간
if "report_time" not in st.session_state:
    st.session_state.report_time = get_now_str()

# ✅ 최초인지 기본값(세션에 없을 때만 세팅)
if "detect_way" not in st.session_state:
    st.session_state.detect_way = "느릅재터널 CCTV 확인"

# --- 화면 레이아웃 ---
st.markdown('<p class="main-title">🚀 터널 밴드보고 작성기</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="sub-title">📝 정보 입력</p>', unsafe_allow_html=True)

    a_type = st.selectbox("유형 선택", ACCIDENT_TYPES)
    tunnel_name = st.selectbox("터널 선택", list(TUNNELS.keys()))

    # 해당 터널의 방향 리스트와 차로 필요 여부 가져오기
    directions = TUNNELS[tunnel_name][0]
    lane_needed = TUNNELS[tunnel_name][1]

    direction_val = st.selectbox("방향", directions)

    # ✅ "괴산/괴산IC/양방향" 기존 입력 유지 + 표기만 안정적으로
    if direction_val == "양방향":
        disp_direction = "양방향"
    else:
        disp_direction = f"{direction_val} 방향"

    st.divider()

    if a_type == "공사":
        work_name = st.text_input("공사명", value="터널 물청소 작업")

        # 차로가 필요한 터널(용관, 주덕 등)일 때만 차단 차로 입력창 표시
        work_lane = ""
        if lane_needed:
            work_lane = st.selectbox("차단 차로", LANES)

        # 공사 보고 양식 (차로가 없으면 공백으로 처리됨)
        lane_str = f" {work_lane}" if work_lane else ""
        report_text = f"[{tunnel_name}]\n\n{disp_direction} {work_name}{lane_str} 차단\n안전운전하세요."

    else:
        # 교통사고/화재사고 양식
        r_type = st.selectbox("보고 단계", REPORT_TYPES, index=0)
        loc_detail = st.radio("상세 위치", LOC_DETAILS, horizontal=True)

        c_pos1, c_pos2 = st.columns(2)
        with c_pos1:
            lane = st.selectbox("사고 차로", LANES) if lane_needed else ""
        with c_pos2:
            dist = st.text_input("거리(m)", placeholder="예: 100")

        time_str = st.text_input("일시", st.session_state.report_time)

        # ✅ key 사용(세션값 우선) + 기본값은 위에서 세팅됨
        detect_way = st.text_input("최초 인지", key="detect_way")

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

    # ✅ 필요 시 세션값 초기화 버튼(선택)
    if st.button("🔄 최초인지 기본값으로 초기화"):
        st.session_state.detect_way = "느릅재터널 CCTV 확인"
        st.rerun()

    if st.button("📢 밴드에 즉시 게시"):
        if BAND_ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
            st.warning("밴드 토큰을 입력해 주세요.")
        else:
            with st.spinner("전송 중..."):
                photo_id = None
                if uploaded_file:
                    photo_id = upload_image_to_band(uploaded_file)

                result = post_to_band(report_text, photo_id)
                if result.get("result_code") == 1:
                    st.success("✅ 게시 성공!")
                else:
                    st.error("❌ 실패: 설정을 확인하세요.")TUNNELS = {
    "국도19호선 느릅재터널": (["괴산", "괴산IC", "양방향"], False),
    "국도3호선 용관터널": (["수안보", "제천", "양방향"], True),
    "국도36호선 토계울1터널": (["청주", "충주", "양방향"], True),
    "국도36호선 토계울2터널": (["청주", "충주", "양방향"], True),
    "국도36호선 주덕터널": (["청주", "충주", "양방향"], True)
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
    # ✅ requests files 형식 개선(권장): (filename, bytes, mimetype)
    files = {'image': (image_file.name, image_file.getvalue(), image_file.type)}
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY}
    try:
        res = requests.post(url, params=params, files=files).json()
        return res.get("result_data", {}).get("photos", [{}])[0].get("photo_id")
    except:
        return None

def post_to_band(content, photo_id=None):
    url = "https://openapi.band.us/v2/band/post/create"
    params = {"access_token": BAND_ACCESS_TOKEN, "band_key": TARGET_BAND_KEY, "content": content, "do_push": True}
    if photo_id:
        params["photos"] = photo_id
    return requests.post(url, data=params).json()

if 'report_time' not in st.session_state:
    st.session_state.report_time = get_now_str()

# --- 화면 레이아웃 ---
st.markdown('<p class="main-title">🚀 터널 밴드보고 작성기</p>', unsafe_allow_html=True)

col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="sub-title">📝 정보 입력</p>', unsafe_allow_html=True)

    a_type = st.selectbox("유형 선택", ACCIDENT_TYPES)
    tunnel_name = st.selectbox("터널 선택", list(TUNNELS.keys()))

    # 해당 터널의 방향 리스트와 차로 필요 여부 가져오기
    directions = TUNNELS[tunnel_name][0]
    lane_needed = TUNNELS[tunnel_name][1]

    direction_val = st.selectbox("방향", directions)

    # ✅ "괴산/괴산IC/양방향" 기존 입력 유지 + 표기만 안정적으로
    if direction_val == "양방향":
        disp_direction = "양방향"
    else:
        disp_direction = f"{direction_val} 방향"

    st.divider()

    if a_type == "공사":
        work_name = st.text_input("공사명", value="터널 물청소 작업")

        # 차로가 필요한 터널(용관, 주덕 등)일 때만 차단 차로 입력창 표시
        work_lane = ""
        if lane_needed:
            work_lane = st.selectbox("차단 차로", LANES)

        # 공사 보고 양식 (차로가 없으면 공백으로 처리됨)
        lane_str = f" {work_lane}" if work_lane else ""
        report_text = f"[{tunnel_name}]\n\n{disp_direction} {work_name}{lane_str} 차단\n안전운전하세요."

    else:
        # 교통사고/화재사고 양식
        r_type = st.selectbox("보고 단계", REPORT_TYPES, index=0)
        loc_detail = st.radio("상세 위치", LOC_DETAILS, horizontal=True)

        c_pos1, c_pos2 = st.columns(2)
        with c_pos1:
            lane = st.selectbox("사고 차로", LANES) if lane_needed else ""
        with c_pos2:
            dist = st.text_input("거리(m)", placeholder="예: 100")

        time_str = st.text_input("일시", st.session_state.report_time)
        # ✅ 기본값 변경: "CCTV 확인" -> "느릅재터널 CCTV 확인"
        detect_way = st.text_input("최초 인지", "느릅재터널 CCTV 확인")
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
    uploaded_file = st.file_uploader("📷 사진 첨부 (카메라)", type=['jpg', 'jpeg', 'png'])

with col2:
    st.markdown('<p class="sub-title">📋 보고서 미리보기</p>', unsafe_allow_html=True)
    st.text_area("결과물", report_text, height=300)

    if st.button("📢 밴드에 즉시 게시"):
        if BAND_ACCESS_TOKEN == "YOUR_ACCESS_TOKEN":
            st.warning("밴드 토큰을 입력해 주세요.")
        else:
            with st.spinner("전송 중..."):
                photo_id = None
                if uploaded_file:
                    photo_id = upload_image_to_band(uploaded_file)

                result = post_to_band(report_text, photo_id)
                if result.get("result_code") == 1:
                    st.success("✅ 게시 성공!")
                else:
                    st.error("❌ 실패: 설정을 확인하세요.")
