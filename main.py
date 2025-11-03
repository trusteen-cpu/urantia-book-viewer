import streamlit as st
import pandas as pd
import re
import os
import chardet

# --- 파일 경로 설정 ---
KO_PATH = os.path.join("data", "urantia_ko.txt")
EN_PATH = os.path.join("data", "urantia_en.txt")
GLOSSARY_PATH = os.path.join("data", "glossary.xlsx")

# --- 텍스트 파일 인코딩 자동 감지 ---
def detect_encoding(path):
    with open(path, "rb") as f:
        result = chardet.detect(f.read())
    return result["encoding"] or "utf-8"

# --- 텍스트 파일 로드 ---
@st.cache_data
def load_texts():
    def parse_file(path):
        data = {}
        encoding = detect_encoding(path)
        with open(path, "r", encoding=encoding, errors="ignore") as f:
            for line in f:
                line = line.strip()
               match = re.match(r"(\d+(?::\d+(?:\.\d+)?)?)\s+(.*)", line)
                if match:
                    key = match.group(1).strip()
                    text = match.group(2).strip()
                    data[key] = text
        return data
    return parse_file(KO_PATH), parse_file(EN_PATH)

# --- 용어집 로드 ---
@st.cache_data
def load_glossary():
    df = pd.read_excel(GLOSSARY_PATH)
    df.columns = df.columns.str.lower()
    expected_cols = {"term-ko", "term-en", "description"}
    missing = expected_cols - set(df.columns)
    if missing:
        st.warning(f"⚠️ 용어집에 다음 열이 없습니다: {missing}")
    return df

ko_texts, en_texts = load_texts()
glossary = load_glossary()

# --- UI 제목 ---
st.title("📘 Urantia Book Viewer")
st.caption("Parallel English–Korean viewer with glossary reference")

# --- 입력창 ---
input_ref = st.text_input("Enter reference (예: 111:7 또는 111:7.5)", "")

# --- 검색 로직 ---
def get_section_texts(ref):
    """111:7 형식 입력 시 해당 장 전체 반환"""
    if "." not in ref:  # 장 단위 검색
        prefix = ref + "."
        ko_results = {k: v for k, v in ko_texts.items() if k.startswith(prefix)}
        en_results = {k: v for k, v in en_texts.items() if k.startswith(prefix)}
    else:  # 절 단위 검색
        ko_results = {ref: ko_texts.get(ref, "❌ 한글 본문 없음")}
        en_results = {ref: en_texts.get(ref, "❌ 영어 본문 없음")}
    return ko_results, en_results

if input_ref:
    input_ref = input_ref.strip()
    ko_results, en_results = get_section_texts(input_ref)

    if ko_results:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇰🇷 Korean Translation")
            for k, v in ko_results.items():
                st.markdown(f"**{k}**  \n{v}")
        with col2:
            st.subheader("🇺🇸 English Original")
            for k, v in en_results.items():
                st.markdown(f"**{k}**  \n{v}")
    else:
        st.warning("❌ No matching text found. Check your reference (예: 111:7.5).")

# --- 용어집 검색 ---
search_term = st.text_input("🔍 Search glossary term (English or Korean):", "")
if search_term:
    results = glossary[
        glossary["term-ko"].str.contains(search_term, case=False, na=False)
        | glossary["term-en"].str.contains(search_term, case=False, na=False)
    ]
    if not results.empty:
        st.write("### 📖 Glossary Results")
        for _, row in results.iterrows():
            term_ko = row.get("term-ko", "")
            term_en = row.get("term-en", "")
            desc = row.get("description", "")
            st.markdown(f"**{term_ko}** / *{term_en}* — {desc}")
    else:
        st.info("No matching term found in glossary.")
