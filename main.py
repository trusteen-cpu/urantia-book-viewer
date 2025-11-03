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

    def get_pairs(ref):
        # 절 기준으로 양쪽 문단을 쌍으로 묶음
        pairs = []
        for k, v in ko_texts.items():
            if k.startswith(ref):
                ko_line = f"<b>{k}</b> — {clean_text(v)}"
                en_line = f"<b>{k}</b> — {clean_text(en_texts.get(k, ''))}"
                pairs.append((ko_line, en_line))
        return pairs

    # CSS 스타일 및 JS 동기 스크롤 추가
    st.markdown("""
        <style>
        .viewer-container {
            display: flex;
            gap: 15px;
        }
        .viewer-col {
            width: 50%;
            padding: 10px 20px;
            background-color: #f9f9f9;
            border-radius: 10px;
            overflow-y: scroll;
            height: 80vh;
            line-height: 1.8;
            font-size: 16px;
        }
        .viewer-row {
            display: flex;
            flex-direction: row;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 20px;
        }
        .viewer-text {
            width: 48%;
            word-wrap: break-word;
        }
        </style>
        <script>
        const syncScroll = () => {
            const left = document.getElementById('ko-col');
            const right = document.getElementById('en-col');
            let isSyncingLeftScroll = false;
            let isSyncingRightScroll = false;

            left.onscroll = function() {
                if (!isSyncingLeftScroll) {
                    isSyncingRightScroll = true;
                    right.scrollTop = left.scrollTop;
                }
                isSyncingLeftScroll = false;
            };
            right.onscroll = function() {
                if (!isSyncingRightScroll) {
                    isSyncingLeftScroll = true;
                    left.scrollTop = right.scrollTop;
                }
                isSyncingRightScroll = false;
            };
        };
        window.addEventListener('load', syncScroll);
        </script>
    """, unsafe_allow_html=True)

    pairs = []
    is_paper = re.match(r"^\d+$", input_ref)
    is_chapter = re.match(r"^\d+:\d+$", input_ref)
    is_section = re.match(r"^\d+:\d+\.\d+$", input_ref)

    if is_section and input_ref in ko_texts:
        pairs = [(f"<b>{input_ref}</b> — {clean_text(ko_texts[input_ref])}",
                  f"<b>{input_ref}</b> — {clean_text(en_texts.get(input_ref, ''))}")]
    elif is_chapter:
        pairs = get_pairs(input_ref + ".")
    elif is_paper:
        pairs = get_pairs(input_ref + ":")
    else:
        st.warning("No matching text found. Try '196', '196:2', or '196:2.3'")

    if pairs:
        left_html = "<br><br>".join([f"<div class='viewer-text'>{k}</div>" for k, _ in pairs])
        right_html = "<br><br>".join([f"<div class='viewer-text'>{e}</div>" for _, e in pairs])
        st.markdown(f"""
        <div class="viewer-container">
            <div id="ko-col" class="viewer-col">
                <h4>🇰🇷 Korean Translation</h4>
                {left_html}
            </div>
            <div id="en-col" class="viewer-col">
                <h4>🇺🇸 English Original</h4>
                {right_html}
            </div>
        </div>
        """, unsafe_allow_html=True)

