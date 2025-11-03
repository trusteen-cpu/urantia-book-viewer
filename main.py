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

    def format_paragraphs(texts):
        formatted = []
        for k, v in texts.items():
            if k.startswith(input_ref + ":"):
                formatted.append(f"<b>{k}</b> — {clean_text(v)}")
        return formatted

    is_paper = re.match(r"^\d+$", input_ref)
    is_section = re.match(r"^\d+:\d+\.\d+$", input_ref)

    # CSS 병렬 높이 맞추기
    st.markdown("""
        <style>
        .viewer-container {
            display: flex;
            gap: 10px;
        }
        .viewer-box {
            width: 50%;
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 10px;
            overflow-y: auto;
            height: 75vh;
            line-height: 1.8;
            font-size: 16px;
        }
        </style>
    """, unsafe_allow_html=True)

    if is_section and input_ref in ko_texts:
        st.markdown(f"### {input_ref}")
        st.markdown(f"""
        <div class="viewer-container">
            <div class="viewer-box">
                <h4>🇰🇷 Korean</h4>
                <p><b>{input_ref}</b> — {clean_text(ko_texts[input_ref])}</p>
            </div>
            <div class="viewer-box">
                <h4>🇺🇸 English</h4>
                <p><b>{input_ref}</b> — {clean_text(en_texts.get(input_ref, "❌ No English text found."))}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif is_paper:
        # 한 편 전체 보기 (예: 196)
        ko_paras = format_paragraphs(ko_texts)
        en_paras = format_paragraphs(en_texts)

        if not ko_paras:
            st.warning(f"No text found for paper {input_ref}")
        else:
            st.markdown(f"### 📜 Paper {input_ref}")
            st.markdown(f"""
            <div class="viewer-container">
                <div class="viewer-box">
                    <h4>🇰🇷 Korean Translation</h4>
                    {'<br><br>'.join(ko_paras)}
                </div>
                <div class="viewer-box">
                    <h4>🇺🇸 English Original</h4>
                    {'<br><br>'.join(en_paras)}
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.warning("No matching text found. Try '196' or '111:7.5'")
