import streamlit as st
import pandas as pd
import re
import os
import chardet

# --- 파일 경로 설정 ---
KO_PATH = os.path.join("data", "urantia_ko.txt")
EN_PATH = os.path.join("data", "urantia_en.txt")
GLOSSARY_PATH = os.path.join("data", "glossary.xlsx")

# --- 자동 인코딩 감지 및 텍스트 파싱 ---
def parse_file(path):
    data = {}
    with open(path, "rb") as f:
        raw = f.read()
        detected = chardet.detect(raw)
        encoding = detected.get("encoding", "utf-8")
        text = raw.decode(encoding, errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            match = re.match(r"(\d+:\d+\.\d+)\s+(.*)", line)
            if match:
                key = match.group(1).strip()
                data[key] = match.group(2).strip()
    return data

# --- 데이터 로드 (캐시 적용) ---
@st.cache_data
def load_texts():
    return parse_file(KO_PATH), parse_file(EN_PATH)

@st.cache_data
def load_glossary():
    df = pd.read_excel(GLOSSARY_PATH)
    df.columns = df.columns.str.lower()
    return df

# --- 실제 데이터 불러오기 ---
try:
    ko_texts, en_texts = load_texts()
    glossary = load_glossary()
except Exception as e:
    st.error(f"데이터 로드 오류: {e}")
    st.stop()

# --- Streamlit UI ---
st.title("📘 Urantia Book Viewer")
st.caption("Korean-English parallel viewer with glossary reference")

input_ref = st.text_input("🔎 Enter reference (e.g. 111:7.5):", "")

# --- 검색 기능 ---
if input_ref:
    ref = input_ref.strip()
    if ref in ko_texts:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇰🇷 Korean Translation")
            st.write(f"**{ref}**  {ko_texts[ref]}")
        with col2:
            st.subheader("🇺🇸 English Original")
            st.write(f"**{ref}**  {en_texts.get(ref, '❌ No English text found for this reference.')}")
    else:
        st.warning("No matching text found. Try nearby references or check your input.")

# --- 용어집 검색 ---
st.markdown("---")
search_term = st.text_input("📖 Search glossary term (Korean or English):", "")

if search_term:
    search_term = search_term.strip()
    results = glossary[
        glossary["term-ko"].str.contains(search_term, case=False, na=False)
        | glossary["termmen"].str.contains(search_term, case=False, na=False)
    ]
    if not results.empty:
        st.subheader("Glossary Results")
        for _, row in results.iterrows():
            term_ko = row.get("term-ko", "")
            term_en = row.get("termmen", "")
            desc = row.get("description", "")
            st.markdown(f"**{term_ko}** / *{term_en}* — {desc}")
    else:
        st.info("No matching term found in glossary.")
