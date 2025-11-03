import streamlit as st
import pandas as pd
import re
import os

# --- 파일 경로 ---
KO_PATH = os.path.join("data", "urantia_ko.txt")
EN_PATH = os.path.join("data", "urantia_en.txt")
GLOSSARY_PATH = os.path.join("data", "glossary.xlsx")

# --- 데이터 로드 ---
@st.cache_data
def load_texts():
    def parse_file(path):
        data = {}
        import chardet

        try:
            with open(path, "rb") as fb:
                raw = fb.read()
                enc = chardet.detect(raw)["encoding"]
                text = raw.decode(enc, errors="replace").splitlines()
            for line in text:
                line = line.strip()
                match = re.match(r"(\d+:\d+\.\d+)\s+(.*)", line)
                if match:
                    key = match.group(1).strip()
                    data[key] = match.group(2).strip()
        except Exception as e:
            st.error(f"❌ 파일 읽기 오류: {path} — {e}")
        return data or {}

    ko_data = parse_file(KO_PATH)
    en_data = parse_file(EN_PATH)
    return ko_data, en_data


@st.cache_data
def load_glossary():
    df = pd.read_excel(GLOSSARY_PATH)
    df.columns = df.columns.str.lower()
    return df

ko_texts, en_texts = load_texts()
glossary = load_glossary()

# --- 기본 UI ---
st.set_page_config(layout="wide")
st.title("📘 Urantia Book Viewer – 편/장 단위 병렬 보기")
st.caption("한글과 영어 절별 병렬 정렬 + 스크롤 동기화")

input_ref = st.text_input("Enter reference (예: 111:7 or 196)", "")

# --- 검색 함수 ---
def get_texts(prefix):
    """편(예 196) 또는 장(예 111:7)을 인식해 전체 구절을 반환"""
    if ":" in prefix:
        ko_matches = {k: v for k, v in ko_texts.items() if k.startswith(prefix + ".")}
        en_matches = {k: v for k, v in en_texts.items() if k.startswith(prefix + ".")}
    else:
        ko_matches = {k: v for k, v in ko_texts.items() if k.startswith(prefix + ":")}
        en_matches = {k: v for k, v in en_texts.items() if k.startswith(prefix + ":")}
    return ko_matches, en_matches

# --- CSS (동기 스크롤 포함) ---
st.markdown("""
<style>
.container {
  display: flex;
  gap: 8px;
  width: 100%;
  overflow: hidden;
}
.text-column {
  width: 50%;
  height: 70vh;
  overflow-y: scroll;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 8px;
  background: #fafafa;
}
.verse {
  margin-bottom: 12px;
  line-height: 1.5;
}
.verse-num {
  font-weight: bold;
  color: #444;
}
</style>

<script>
const syncScroll = () => {
  const left = window.parent.document.querySelectorAll('.text-column')[0];
  const right = window.parent.document.querySelectorAll('.text-column')[1];
  if (left && right) {
    left.addEventListener('scroll', () => { right.scrollTop = left.scrollTop; });
    right.addEventListener('scroll', () => { left.scrollTop = right.scrollTop; });
  }
};
window.addEventListener('load', syncScroll);
</script>
""", unsafe_allow_html=True)

# --- 본문 렌더링 ---
if input_ref:
    ko_matches, en_matches = get_texts(input_ref)
    if ko_matches:
        st.markdown(f"### 📖 {input_ref} 전체 보기")

        left_col, right_col = st.columns(2)
        with left_col:
            st.markdown("#### 🇰🇷 Korean Translation")
            st.markdown('<div class="text-column">', unsafe_allow_html=True)
            for key in sorted(ko_matches.keys(), key=lambda x: list(map(float, re.findall(r'\\d+', x)))):
                st.markdown(f'<div class="verse"><span class="verse-num">{key}</span> {ko_matches[key]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with right_col:
            st.markdown("#### 🇺🇸 English Original")
            st.markdown('<div class="text-column">', unsafe_allow_html=True)
            for key in sorted(en_matches.keys(), key=lambda x: list(map(float, re.findall(r'\\d+', x)))):
                st.markdown(f'<div class="verse"><span class="verse-num">{key}</span> {en_matches[key]}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.warning("⚠️ 해당 편 또는 장을 찾을 수 없습니다. 예: 111:7 또는 196 형태로 입력하세요.")

# --- 용어집 ---
st.divider()
st.subheader("📚 용어집 검색")
search_term = st.text_input("용어나 단어 검색 (한글 또는 영어):", "")
if search_term:
    results = glossary[
        glossary["term-ko"].str.contains(search_term, case=False, na=False) |
        glossary["term-en"].str.contains(search_term, case=False, na=False)
    ]
    if not results.empty:
        st.write("### 🔍 Glossary Results")
        for _, row in results.iterrows():
            st.markdown(f"**{row['term-ko']}** / *{row['term-en']}* — {row['description']}")
    else:
        st.info("No matching term found in glossary.")

