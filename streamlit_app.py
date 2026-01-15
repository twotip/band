import streamlit as st
from datetime import datetime

# 페이지 설정 (웹 브라우저 탭 이름 및 아이콘)
st.set_page_config(page_title="터널 사고보고 작성기", layout="wide")

# 1. 데이터 설정
TUNNELS = {
    "국도19호선 느릅재터널": [["괴산", "괴산IC", "양방향"], False],
    "국도3호선 용관터널": [["수안보", "제천", "양방향"], True],
    "국도36호선 토계울1터널": [["청주", "충주", "양방향"], True],
    "국도36호선 토계울2터널": [["청주", "충주", "양방향"], True],
    "국도36호선 주덕터널": [["청주", "충주", "양방향"], True]
}

REPORT_TYPES = ["최초", "중간", "최종"]
ACCIDENT_TYPES = ["교통사고", "화재사고"]
LOC_DETAILS = ["터널내", "입구부", "출구부"]
LANES = ["1차로", "2차로", "갓길", "전차로"]

def get_now_str():
    now = datetime.now()
    weekday_map = ["월", "화", "수", "목", "금", "토", "일"]
    return now.strftime(f"%Y.%m.%d({weekday_map[now.weekday()]}) %H:%M")

st.title("🚀 터널 사고보고 실시간 작성기 (Mobile)")

# 좌우 레이아웃 나누기 (스마트폰에서는 자동으로 위아래로 바뀜)
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📝 사고 정보 입력")
    
    r_type = st.selectbox("보고 단계", REPORT_TYPES)
    a_type = st.selectbox("사고 유형", ACCIDENT_TYPES)
    tunnel_name = st.selectbox("터널 선택", list(TUNNELS.keys()))
    
    # 터널 정보에 따른 방향 및 차로 설정
    directions = TUNNELS[tunnel_name][0]
    lane_needed = TUNNELS[tunnel_name][1]
    
    loc_detail = st.radio("상세 위치", LOC_DETAILS, horizontal=True)
    
    c1, c2, c3 = st.columns(3)
    with c1:
        direction = st.selectbox("방향", directions)
    with c2:
        lane = st.selectbox("차로", LANES) if lane_needed else ""
    with c3:
        dist = st.text_input("거리(m)", "")

    # 기본값 자동 설정 로직
    default_status = "현장 출동 및 파악 중" if r_type == "최초" else ("상황 종료 및 소통 원활" if r_type == "최종" else "")
    default_etc = "확인중" if r_type == "최초" else "없음"

    time_str = st.text_input("사고 일시", get_now_str())
    detect_way = st.text_input("최초 인지", "CCTV 확인")
    manager = st.text_input("관리 부서", "충주국토관리사무소")
    desc = st.text_input("사고 내용", "")
    status = st.text_input("진행 상황", default_status)
    cause = st.text_input("사고 원인", default_etc if r_type == "최초" else "")
    human = st.text_input("인명 피해", default_etc)
    facility = st.text_input("시설물 피해", default_etc)
    traffic = st.text_input("정체 현황", "원활")
    
    view_mode = st.radio("출력 모드", ["밴드용( : )", "이프넷용(:)"], horizontal=True)

# 보고서 생성 로직
lane_str = f" {lane}" if lane else ""
dist_str = f" {dist}m 지점" if dist else ""
full_location = f"{tunnel_name} {loc_detail}{lane_str}{dist_str} ({direction}방향)"
sep = " : " if "밴드" in view_mode else ":"

report_text = f"""[{tunnel_name} {a_type} ({r_type}) 보고]

ㅇ일시{sep}{time_str}분경
ㅇ최초인지{sep}{detect_way}
ㅇ위치{sep}{full_location}
ㅇ관리{sep}{manager}
ㅇ내용{sep}{desc}
ㅇ진행상황{sep}{status}
ㅇ원인{sep}{cause}
ㅇ인명피해{sep}{human}
ㅇ시설물피해{sep}{facility}
ㅇ정체현황{sep}{traffic}"""

with col2:
    st.subheader("📋 실시간 미리보기")
    st.text_area("복사할 내용", report_text, height=500)
    st.info("💡 위 박스의 내용을 길게 누르거나 전체 선택하여 복사하세요.")
    
    if st.button("🔄 시간 새로고침"):
        st.rerun()
