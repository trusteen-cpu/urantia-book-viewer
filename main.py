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

    def format_with_numbers(texts, ref):
        result = []
        for k, v in texts.items():
            if k.startswith(ref):
                result.append(f"<b>{k}</b> — {clean_text(v)}")
        return "<br><br>".join(result)

    is_paper = re.match(r"^\d+$", input_ref)
    is_chapter = re.match(r"^\d+:\d+$", input_ref)
    is_section = re.match(r"^\d+:\d+\.\d+$", input_ref)

    # CSS - 전체 펼침형
    st.markdown("""
        <style>
        .viewer-flex {
            display: flex;
            gap: 20px;
        }
        .viewer-col {
            width: 50%;
            background-color: #f8f8f8;
            padding: 15px;
            border-radius: 10px;
            line-height: 1.8;
            font-size: 16px;
            overflow-wrap: break-word;
        }
        </style>
    """, unsafe_allow_html=True)

    if is_section and input_ref in ko_texts:
        st.markdown(f"### {input_ref}")
        st.markdown(f"""
        <div class="viewer-flex">
            <div class="viewer-col">
                <h4>🇰🇷 Korean</h4>
                <p><b>{input_ref}</b> — {clean_text(ko_texts[input_ref])}</p>
            </div>
            <div class="viewer-col">
                <h4>🇺🇸 English</h4>
                <p><b>{input_ref}</b> — {clean_text(en_texts.get(input_ref, '❌ No English text found.'))}</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif is_chapter:
        # 장 단위 (예: 196:2)
        ko_html = format_with_numbers(ko_texts, input_ref + ".")
        en_html = format_with_numbers(en_texts, input_ref + ".")
        st.markdown(f"### 📖 Section {input_ref}")
        st.markdown(f"""
        <div class="viewer-flex">
            <div class="viewer-col">
                <h4>🇰🇷 Korean Translation</h4>{ko_html}
            </div>
            <div class="viewer-col">
                <h4>🇺🇸 English Original</h4>{en_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    elif is_paper:
        # 편 전체 (예: 196)
        ko_html = format_with_numbers(ko_texts, input_ref + ":")
        en_html = format_with_numbers(en_texts, input_ref + ":")
        st.markdown(f"### 📜 Paper {input_ref}")
        st.markdown(f"""
        <div class="viewer-flex">
            <div class="viewer-col">
                <h4>🇰🇷 Korean Translation</h4>{ko_html}
            </div>
            <div class="viewer-col">
                <h4>🇺🇸 English Original</h4>{en_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

    else:
        st.warning("No matching text found. Try '196', '196:2', or '196:2.3'")

