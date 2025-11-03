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
# 참조 / 검색 공용 함수
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

def make_parallel_html(pairs):
    html = """
    <html><head><meta charset='utf-8'>
    <style>
    body { font-family: 'Noto Sans KR', sans-serif; margin: 0; padding: 20px; background: #f7f7f7; }
    .pair { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 14px; }
    .box { background: #fff; padding: 16px 20px; border-radius: 10px;
           box-shadow: 0 0 6px rgba(0,0,0,0.05); line-height: 1.9; font-size: 17px; }
    .box b { color: #003366; }
    </style></head><body>
    """
    for k, ko, en in pairs:
        html += f"""
        <div class='pair'>
            <div class='box'><b>{k}</b><br>{ko}</div>
            <div class='box'><b>{k}</b><br>{en}</div>
        </div>
        """
    html += "</body></html>"
    return html

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("📘 Urantia Book Viewer")
st.caption("왼쪽 한글 / 오른쪽 영어 병렬 보기 + 본문 단어 검색 + 용어 검색")

# --- 참조 입력 ---
ref = st.text_input("참조 입력 (예: 196, 196:2, 196:2.3)", "", key="ref_input").strip()

# --- 본문 검색 ---
keyword = st.text_input("본문 단어 검색 (예: 조절자, Adjuster 등)", "", key="keyword_search").strip()

# ------------------------------------------------------------
# 참조 검색 결과
# ------------------------------------------------------------
if ref:
    pairs = get_pairs_by_ref(ref)
    if pairs:
        html = make_parallel_html(pairs)
        st.components.v1.html(html, height=6000, scrolling=True)
    else:
        st.warning("일치하는 본문이 없습니다. 예: 196, 196:2, 196:2.3")

# ------------------------------------------------------------
# 단어 검색 결과
# ------------------------------------------------------------
elif keyword:
    matches = []
    for ref_, text in ko_texts.items():
        if keyword in text:
            matches.append((ref_, text, en_texts.get(ref_, "")))
    for ref_, text in en_texts.items():
        if keyword.lower() in text.lower() and ref_ not in [m[0] for m in matches]:
            matches.append((ref_, ko_texts.get(ref_, ""), text))

    if matches:
        st.markdown(f"**🔍 '{keyword}' 검색 결과 — {len(matches)}개 절**")
        html = make_parallel_html(matches[:100])
        st.components.v1.html(html, height=6000, scrolling=True)
    else:
        st.info(f"'{keyword}' 가 포함된 본문을 찾을 수 없습니다.")

# ------------------------------------------------------------
# 용어 검색
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
        html = """
        <html><head><meta charset='utf-8'><style>
        body { font-family: 'Noto Sans KR', sans-serif; background:#f7f7f7; margin:0; padding:20px; }
        .term { background:#eef2ff; padding:12px 16px; border-radius:8px; margin-bottom:10px;
                line-height:1.7; font-size:16px; }
        </style></head><body>
        """
        for _, row in results.iterrows():
            html += f"<div class='term'><b>{row['term-ko']}</b> / *{row['term-en']}* — {row['description']}</div>"
        html += "</body></html>"
        st.components.v1.html(html, height=2000, scrolling=True)
    else:
        st.info("일치하는 용어가 없습니다.")
else:
    st.caption("예: ‘신비 모니터’, ‘Thought Adjuster’, ‘Nebadon’ 등을 입력해 보세요.")



