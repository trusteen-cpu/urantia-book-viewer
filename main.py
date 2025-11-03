import streamlit as st
import pandas as pd
import re
import os
import chardet

KO_PATH = os.path.join("data", "urantia_ko.txt")
EN_PATH = os.path.join("data", "urantia_en.txt")
GLOSSARY_PATH = os.path.join("data", "glossary.xlsx")

# --- 데이터 로드 ---
@st.cache_data
def load_texts():
    def parse_file(path):
        data = {}
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

    return parse_file(KO_PATH), parse_file(EN_PATH)

@st.cache_data
def load_glossary():
    try:
        df = pd.read_excel(GLOSSARY_PATH)
        df.columns = df.columns.str.lower()
        return df
    except Exception as e:
        st.warning(f"⚠️ 용어집 불러오기 오류: {e}")
        return pd.DataFrame(columns=["term-ko", "term-en", "description"])

ko_texts, en_texts = load_texts()
glossary = load_glossary()

# --- UI ---
st.title("📘 Urantia Book Viewer")
st.caption("Parallel Korean-English Viewer with Glossary")

input_ref = st.text_input("Enter reference (e.g. 111:7.5)", "")

# --- 검색 로직 ---
if input_ref:
    input_ref = input_ref.strip()

    def clean_text(t):
        return t.replace("\ufeff", "").replace("�", "").strip()

    if input_ref in ko_texts:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"### 🇰🇷 {input_ref}")
            st.markdown(
                f"""
                <div style="background-color:#f8f8f8; padding:10px; border-radius:10px; line-height:1.8;">
                    {clean_text(ko_texts[input_ref])}
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(f"### 🇺🇸 {input_ref}")
            st.markdown(
                f"""
                <div style="background-color:#f8f8f8; padding:10px; border-radius:10px; line-height:1.8;">
                    {clean_text(en_texts.get(input_ref, "❌ No English text found."))}
                </div>
                """,
                unsafe_allow_html=True,
            )
    else:
        st.warning("No matching text found. Try nearby references or check your input.")

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
            st.markdown(f"**{row['term-ko']}** / *{row['term-en']}* — {row['description']}")
    else:
        st.info("No matching term found in glossary.")
