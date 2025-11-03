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
    df = pd.read_excel(GLOSSARY_PATH)
    df.columns = df.columns.str.lower()
    return df

ko_texts, en_texts = load_texts()
glossary = load_glossary()

# ------------------------------------------------------------
# 참조 검색 로직
# ------------------------------------------------------------
def get_pairs_by_ref(ref: str):
    pairs = []
    if re.match(r"^\d+:\d+\.\d+$", ref):  # 절
        if ref in ko_texts:
            pairs.append((ref, ko_texts[ref], en_texts.get(ref, "")))
        return pairs
    if re.match(r"^\d+:\d+$", ref):  # 장
        prefix = ref + "."
        for k in ko_texts:
            if k.startswith(prefix):
                pairs.append((k, ko_texts[k], en_texts.get(k, "")))
        return pairs
    if re.match(r"^\d+$", ref):  # 편
        prefix = ref + ":"
        for k in ko_texts:
            if k.startswith(prefix):
                pairs.append((k, ko_texts[k], en_texts.get(k, "")))
        return pairs
    return pairs

# ------------------------------------------------------------
# 스타일
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container { max-width: 95vw !important; }
.viewer-wrapper { width: 100%; margin: 0 auto; }
.verse-row { display: flex; gap: 20px; margin-bottom: 14px; align-items: flex-start; }
.verse-col {
  flex: 1;
  padding: 18px;
  background: #f9f9f9;
  border-radius: 12px;
  box-shadow: 0 0 8px rgba(0,0,0,0.05);
  line-height: 1.8;
  font-size: 17px;
  min-height: 100%;
}
.section-title { font-weight: bold; margin-bottom: 6px; }
.glossary-box {
  background: #f0f0ff;
  border-radius: 8px;
  padding: 10px 14px;
  margin-top: 18px;
}
</style>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("📘 Urantia Book Viewer")
st.caption("Parallel Korean-English text with glossary search and wide layout")

# 🔹 참조 검색
ref = st.text_input("참조를 입력하세요 (예: 196, 196:2, 196:2.3)", "", key="ref_input").strip()

if ref:
    pairs = get_pairs_by_ref(ref)
    if not pairs:
        st.warning("일치하는 본문이 없습니다. 예: 196, 196:2, 196:2.3 형식으로 입력해 보세요.")
    else:
        if re.match(r"^\d+:\d+\.\d+$", ref):
            st.markdown(f"### {ref}")
        elif re.match(r"^\d+:\d+$", ref):
            st.markdown(f"### 📖 Section {ref}")
        else:
            st.markdown(f"### 📜 Paper {ref}")

        html = []
        for k, ko, en in pairs:
            html.append(f"""
            <div class='verse-row'>
                <div class='verse-col'><b>{k}</b><br>{ko}</div>
                <div class='verse-col'><b>{k}</b><br>{en}</div>
            </div>
            """)
        st.markdown("<div class='viewer-wrapper'>" + "\n".join(html) + "</div>", unsafe_allow_html=True)
else:
    st.info("예: 196 (편), 196:2 (장), 196:2.3 (절) 형태로 검색해 보세요.")

# ------------------------------------------------------------
# 🔍 용어 검색
# ------------------------------------------------------------
st.markdown("---")
st.subheader("🔍 용어 검색 (Glossary Search)")
term = st.text_input("찾고 싶은 용어 (영어 또는 한국어):", "", key="glossary_input")

if term:
    results = glossary[
        glossary["term-ko"].str.contains(term, case=False, na=False)
        | glossary["term-en"].str.contains(term, case=False, na=False)
    ]
    if not results.empty:
        st.markdown("#### 📖 검색 결과")
        for _, row in results.iterrows():
            st.markdown(f"""
            <div class='glossary-box'>
            <b>{row['term-ko']}</b> / *{row['term-en']}*  
            — {row['description']}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("일치하는 용어가 없습니다. 예: ‘신비 모니터’, ‘Thought Adjuster’, ‘Nebadon’ 등을 입력해 보세요.")
else:
    st.caption("예: ‘신비 모니터’, ‘Thought Adjuster’, ‘Nebadon’ 등을 입력해 보세요.")



