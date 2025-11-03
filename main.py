import streamlit as st
import pandas as pd
import re
import os

# ------------------------------------------------------------
# 페이지 설정
# ------------------------------------------------------------
st.set_page_config(page_title="Urantia Book Viewer", layout="wide")

# ------------------------------------------------------------
# 파일 경로
# ------------------------------------------------------------
KO_PATH = os.path.join("data", "urantia_ko.txt")
EN_PATH = os.path.join("data", "urantia_en.txt")
GLOSSARY_PATH = os.path.join("data", "glossary.xlsx")

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
                data[m.group(1)] = clean_text(m.group(2))
        return data

    ko = parse_file(KO_PATH)
    en = parse_file(EN_PATH)
    return ko, en

@st.cache_data
def load_glossary():
    try:
        df = pd.read_excel(GLOSSARY_PATH)
        df.columns = df.columns.str.lower()
        return df
    except Exception:
        return pd.DataFrame(columns=["term-ko", "term-en", "description"])

ko_texts, en_texts = load_texts()
glossary = load_glossary()

# ------------------------------------------------------------
# 참조 검색
# ------------------------------------------------------------
def get_pairs_by_ref(ref: str):
    pairs = []
    if re.match(r"^\d+:\d+\.\d+$", ref):
        if ref in ko_texts:
            pairs.append((ref, ko_texts[ref], en_texts.get(ref, "")))
        return pairs
    if re.match(r"^\d+:\d+$", ref):
        prefix = ref + "."
        for k in ko_texts:
            if k.startswith(prefix):
                pairs.append((k, ko_texts[k], en_texts.get(k, "")))
        return pairs
    if re.match(r"^\d+$", ref):
        prefix = ref + ":"
        for k in ko_texts:
            if k.startswith(prefix):
                pairs.append((k, ko_texts[k], en_texts.get(k, "")))
        return pairs
    return pairs

# ------------------------------------------------------------
# CSS 스타일
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container {
  max-width: 98vw !important;
  padding: 0 2vw;
}

.viewer-wrapper { width: 100%; margin: 0 auto; }

.pair {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 16px;
}

.box {
  background: #ffffff;
  padding: 16px 20px;
  border-radius: 10px;
  box-shadow: 0 0 6px rgba(0,0,0,0.05);
  line-height: 1.9;
  font-size: 17px;
  word-wrap: break-word;
}

.box b { color: #003366; }

.glossary-box {
  background: #eef2ff;
  border-radius: 8px;
  padding: 10px 14px;
  margin-top: 18px;
  font-size: 16px;
  line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# UI — 본문 조회
# ------------------------------------------------------------
st.title("📘 Urantia Book Viewer")
st.caption("왼쪽 한글 / 오른쪽 영어 병렬 보기 + 본문 단어 검색")

ref = st.text_input("참조 입력 (예: 196, 196:2, 196:2.3)", "", key="ref_input").strip()

if ref:
    pairs = get_pairs_by_ref(ref)
    if not pairs:
        st.warning("일치하는 본문이 없습니다.")
    else:
        html = "<div class='viewer-wrapper'>"
        for k, ko, en in pairs:
            html += f"""
            <div class='pair'>
                <div class='box'><b>{k}</b><br>{ko}</div>
                <div class='box'><b>{k}</b><br>{en}</div>
            </div>
            """
        html += "</div>"
        st.components.v1.html(html, height=6000, scrolling=True)
else:
    st.info("예: 196 (편), 196:2 (장), 196:2.3 (절) 형태로 검색해 보세요.")

# ------------------------------------------------------------
# 🔍 본문 단어 검색
# ------------------------------------------------------------
st.markdown("---")
st.subheader("🔎 본문 단어 검색 (Keyword Search in Text)")

keyword = st.text_input("찾을 단어를 입력하세요 (예: 조절자, Thought Adjuster 등)", "", key="keyword_search")

if keyword:
    matches = []
    for ref, text in ko_texts.items():
        if keyword in text:
            matches.append((ref, text, en_texts.get(ref, "")))
    for ref, text in en_texts.items():
        if keyword.lower() in text.lower() and ref not in [m[0] for m in matches]:
            matches.append((ref, ko_texts.get(ref, ""), text))

    if matches:
        st.markdown(f"**🔍 '{keyword}' 검색 결과 — {len(matches)}개 절 발견**")
        html = "<div class='viewer-wrapper'>"
        for k, ko, en in matches[:100]:  # 100절 제한 (너무 많으면 느려짐)
            html += f"""
            <div class='pair'>
                <div class='box'><b>{k}</b><br>{ko}</div>
                <div class='box'><b>{k}</b><br>{en}</div>
            </div>
            """
        html += "</div>"
        st.components.v1.html(html, height=6000, scrolling=True)
    else:
        st.info(f"'{keyword}' 가 포함된 본문을 찾을 수 없습니다.")

# ------------------------------------------------------------
# 🔍 용어 검색
# ------------------------------------------------------------
st.markdown("---")
st.subheader("📚 용어 검색 (Glossary Search)")
term = st.text_input("찾고 싶은 용어 (영어 또는 한국어):", "", key="glossary_input")

if term:
    results = glossary[
        glossary["term-ko"].str.contains(term, case=False, na=False)
        | glossary["term-en"].str.contains(term, case=False, na=False)
    ]
    if not results.empty:
        for _, row in results.iterrows():
            st.markdown(f"""
            <div class='glossary-box'>
            <b>{row['term-ko']}</b> / *{row['term-en']}*  
            — {row['description']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("일치하는 용어가 없습니다.")
else:
    st.caption("예: ‘신비 모니터’, ‘Thought Adjuster’, ‘Nebadon’ 등을 입력해 보세요.")


