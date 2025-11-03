import streamlit as st
import re
import os

# ------------------------------------------------------------
# Page Config
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
    encodings_to_try = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "utf-16", "latin-1"]
    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.readlines()
        except Exception:
            continue
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.readlines()

def clean_text(t: str) -> str:
    return t.replace("\ufeff", "").replace("�", "").strip()

@st.cache_data
def load_texts():
    def parse_file(path):
        data = {}
        lines = safe_read_lines(path)
        for line in lines:
            line = line.strip()
            m = re.match(r"^(\d+:\d+\.\d+)\s+(.*)$", line)
            if m:
                key = m.group(1).strip()
                val = clean_text(m.group(2))
                data[key] = val
        return data

    ko = parse_file(KO_PATH)
    en = parse_file(EN_PATH)
    return ko, en

ko_texts, en_texts = load_texts()

# ------------------------------------------------------------
# ref별 (절번호, 한글, 영어) 쌍 만들기
# ------------------------------------------------------------
def get_pairs_by_ref(ref: str):
    pairs = []

    # 절
    if re.match(r"^\d+:\d+\.\d+$", ref):
        if ref in ko_texts:
            pairs.append((ref, ko_texts[ref], en_texts.get(ref, "")))
        return pairs

    # 장
    if re.match(r"^\d+:\d+$", ref):
        prefix = ref + "."
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append((k, v, en_texts.get(k, "")))
        return pairs

    # 편
    if re.match(r"^\d+$", ref):
        prefix = ref + ":"
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append((k, v, en_texts.get(k, "")))
        return pairs

    return pairs

# ------------------------------------------------------------
# 스타일
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container {
  max-width: 98vw !important;
  padding-left: 1vw !important;
  padding-right: 1vw !important;
}

/* 전체 폭 꽉 채우기 */
.viewer-wrapper {
  width: 98vw;
  margin: 0 auto;
}

/* 절별 행: 좌우 정렬 */
.verse-row {
  display: flex;
  gap: 20px;
  align-items: stretch;
  justify-content: space-between;
  margin-bottom: 22px;
}

/* 각 칼럼 (한글/영문) */
.verse-col {
  flex: 1 1 50%;
  background: #fff;
  border-left: 4px solid #ddd;
  border-radius: 6px;
  padding: 10px 14px;
  line-height: 1.8;
  font-size: 17px;
  word-wrap: break-word;
}

/* 절 번호 */
.ref-tag {
  color: #666;
  font-weight: bold;
  display: block;
  margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("📘 Urantia Book Viewer")
st.caption("Side-by-side Korean & English | Paper / Section / Paragraph lookup")

ref = st.text_input("참조 입력 (예: 196, 196:2, 196:2.3)", "").strip()

if ref:
    pairs = get_pairs_by_ref(ref)

    if not pairs:
        st.warning("일치하는 본문이 없습니다. 예: 196, 196:2, 196:2.3 형태로 입력해 보세요.")
    else:
        html_parts = []
        for key, ko, en in pairs:
            html_parts.append(f"""
            <div class="verse-row">
                <div class="verse-col">
                    <span class="ref-tag">{key}</span>
                    {clean_text(ko)}
                </div>
                <div class="verse-col">
                    <span class="ref-tag">{key}</span>
                    {clean_text(en)}
                </div>
            </div>
            """)
        full_html = "<div class='viewer-wrapper'>" + "".join(html_parts) + "</div>"
        st.components.v1.html(full_html, height=8000, scrolling=True)
else:
    st.info("예: 196 (편), 196:2 (장), 196:2.3 (절) 형태로 입력해 보세요.")
