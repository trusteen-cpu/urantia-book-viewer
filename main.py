import streamlit as st
import re
import os

# ------------------------------------------------------------
# 페이지 설정
# ------------------------------------------------------------
st.set_page_config(page_title="Urantia Viewer", layout="wide")

# ------------------------------------------------------------
# 파일 경로
# ------------------------------------------------------------
KO_PATH = os.path.join("data", "urantia_ko.txt")
EN_PATH = os.path.join("data", "urantia_en.txt")

# ------------------------------------------------------------
# 안전한 파일 읽기
# ------------------------------------------------------------
def safe_read_lines(path):
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "utf-16", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.readlines()
        except Exception:
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()

def clean_text(t):
    return t.replace("\ufeff", "").replace("�", "").strip()

@st.cache_data
def load_texts():
    def parse_file(path):
        data = {}
        for line in safe_read_lines(path):
            line = line.strip()
            m = re.match(r"^(\d+:\d+\.\d+)\s+(.*)$", line)
            if m:
                key = m.group(1)
                val = clean_text(m.group(2))
                data[key] = val
        return data

    return parse_file(KO_PATH), parse_file(EN_PATH)

ko_texts, en_texts = load_texts()

# ------------------------------------------------------------
# ref별로 구절 쌍 추출
# ------------------------------------------------------------
def get_pairs_by_ref(ref):
    pairs = []
    if re.match(r"^\d+:\d+\.\d+$", ref):
        if ref in ko_texts:
            pairs.append((ref, ko_texts[ref], en_texts.get(ref, "")))
    elif re.match(r"^\d+:\d+$", ref):
        prefix = ref + "."
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append((k, v, en_texts.get(k, "")))
    elif re.match(r"^\d+$", ref):
        prefix = ref + ":"
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append((k, v, en_texts.get(k, "")))
    return pairs

# ------------------------------------------------------------
# 스타일
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container {
  max-width: 98vw !important;
  padding: 40px 2vw 2vw 2vw !important;  /* 상단에 여유 40px */
}
.paragraph-box {
  background-color: #ffffff;
  border-radius: 8px;
  padding: 14px 18px;
  margin-bottom: 20px;
  box-shadow: 0 0 8px rgba(0,0,0,0.05);
  line-height: 1.8;
  font-size: 17px;
}
.ref-tag {
  font-weight: bold;
  color: #555;
  margin-bottom: 6px;
  display: block;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("📘 Urantia Book Viewer")
st.caption("Left: Korean | Right: English — Paper / Section / Paragraph Lookup")

ref = st.text_input("참조 입력 (예: 196, 196:2, 196:2.3)", "").strip()

if ref:
    pairs = get_pairs_by_ref(ref)

    if not pairs:
        st.warning("일치하는 본문이 없습니다. 예: 196, 196:2, 196:2.3 형식으로 입력해 보세요.")
    else:
        for key, ko, en in pairs:
            col1, col2 = st.columns(2, gap="large")
            with col1:
                st.markdown(f"<div class='paragraph-box'><span class='ref-tag'>{key}</span>{clean_text(ko)}</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='paragraph-box'><span class='ref-tag'>{key}</span>{clean_text(en)}</div>", unsafe_allow_html=True)
else:
    st.info("예: 196 (편), 196:2 (장), 196:2.3 (절) 형태로 검색해 보세요.")

