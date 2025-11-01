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

import chardet

def parse_file(path):
    data = {}
    with open(path, "rb") as f:
        raw = f.read()
        encoding = chardet.detect(raw)["encoding"] or "utf-8"
        text = raw.decode(encoding, errors="ignore")
        for line in text.splitlines():
            line = line.strip()
            match = re.match(r"(\d+:\d+\.\d+)\s+(.*)", line)
            if match:
                key = match.group(1).strip()
                data[key] = match.group(2).strip()
    return data

            for line in f:
                line = line.strip()
                match = re.match(r"\s*(\d{1,3}:\d{1,2}\.\d{1,3})\s+(.*)", line)
                if match:
                    key = match.group(1).strip()
                    data[key] = match.group(2).strip()
        return data
    return parse_file(KO_PATH), parse_file(EN_PATH)

@st.cache_data
def load_glossary():
    df = pd.read_excel(GLOSSARY_PATH)
    df.columns = df.columns.str.lower()
    return df

ko_texts, en_texts = load_texts()
glossary = load_glossary()

# --- Streamlit UI ---
st.title("📘 Urantia Book Viewer")
st.caption("Dual-language parallel viewer with glossary reference")

input_ref = st.text_input("Enter reference (e.g. 111:7.5)", "")

# --- 검색 로직 ---
if input_ref:
    input_ref = input_ref.strip()
    if input_ref in ko_texts:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("🇰🇷 Korean Translation")
            st.write(ko_texts[input_ref])
        with col2:
            st.subheader("🇺🇸 English Original")
            st.write(en_texts.get(input_ref, "❌ No English text found for this reference."))
    else:
        st.warning("No matching text found. Try nearby references or check your input.")

# --- 용어집 검색 ---
search_term = st.text_input("🔍 Search glossary term (English or Korean):", "")
if search_term:
    results = glossary[
        glossary["term-ko"].str.contains(search_term, case=False, na=False) |
        glossary["termmen"].str.contains(search_term, case=False, na=False)
    ]
    if not results.empty:
        st.write("### 📖 Glossary Results")
        for _, row in results.iterrows():
            st.markdown(f"**{row['term-ko']}** / *{row['termmen']}* — {row['description']}")
    else:
        st.info("No matching term found in glossary.")
