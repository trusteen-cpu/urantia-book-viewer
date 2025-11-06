import streamlit as st
import os
import re
from html import escape

# -----------------------
# 기본 설정
# -----------------------
st.set_page_config(page_title="Urantia Theme Study", layout="wide")

# 헤더
st.markdown(
    """
    # 📘 Urantia Theme Study – AI Theological Report + 5 Slides  
    *Enter a Urantia-related theme → highlighted passages → AI report + 5-slide outline with notes.*
    """
)

# -----------------------
# 🔑 GitHub Secrets 또는 Render 환경 변수에서 API Key 자동 불러오기
# -----------------------
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("⚠️ OpenAI API 키를 찾을 수 없습니다. Render 또는 GitHub Secrets에 등록하세요.")
    st.stop()

# -----------------------
# 데이터 로드
# -----------------------
DATA_DIR = "data"
EN_PATH = os.path.join(DATA_DIR, "urantia_en.txt")

def safe_read_text(path: str) -> list[str]:
    encodings = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin-1"]
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc) as f:
                return f.readlines()
        except:
            continue
    return []

@st.cache_data
def load_urantia_en():
    if not os.path.exists(EN_PATH):
        return []
    return safe_read_text(EN_PATH)

urantia_lines = load_urantia_en()

# -----------------------
# 검색 + 하이라이트 기능
# -----------------------
def highlight_term(text: str, term: str) -> str:
    """검색된 용어를 형광색으로 강조"""
    if not term:
        return escape(text)
    pattern = re.compile(re.escape(term), re.IGNORECASE)
    highlighted = pattern.sub(lambda m: f"<mark style='background-color:#fffd75'>{escape(m.group(0))}</mark>", text)
    return highlighted

def search_passages(keyword: str, lines: list[str], limit: int = 200):
    if not keyword:
        return []
    key = keyword.lower()
    results = [l.strip() for l in lines if key in l.lower()]
    return results[:limit]

# -----------------------
# GPT 보고서 + 슬라이드 생성
# -----------------------
def generate_gpt_report_and_slides(term: str, passages: list[str]):
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
    except Exception as e:
        return f"⚠️ OpenAI 라이브러리 로드 오류: {e}"

    joined_passages = "\n".join(passages) or "No passages found."

    prompt = f"""
You are a theological researcher of *The Urantia Book*.

Theme: "{term}"

Below are Urantia Book passages that mention or relate to this theme.

---

## Part 1. Theological Report
Write an academic-style synthesis (500–800 words) explaining:
- The Urantia meaning and origin of this theme  
- Theological and cosmological significance  
- Its role in relation to the Father, the Supreme, and Adjusters  
- Philosophical implications for mortal ascension  
- Lessons for human faith and experience

---

## Part 2. 5-Slide Outline with Speaker Notes
Create **exactly 5 slides**.

Each slide should include:
- Title  
- 3–5 concise bullet points  
- `Speaker Notes:` (200–500 characters) — a short oral commentary

Format strictly as markdown.

# Slide 1: <title>
- point
- point
Speaker Notes: ...

# Slide 2: ...
...

---

### Source Passages:
{joined_passages}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Urantia scholar skilled in theological interpretation and teaching."},
                {"role": "user", "content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"⚠️ GPT 오류 발생: {e}"

# -----------------------
# UI
# -----------------------
st.header("1️⃣ Enter a Urantia theme or concept")

# 👇 여기에 key 추가 (중복 방지용)
term = st.text_input(
    "예: Supreme Being, Thought Adjuster, Michael of Nebadon, Faith, Survival, Morontia",
    "",
    key="urantia_theme_input"
)

passages = search_passages(term, urantia_lines) if term else []

st.header("2️⃣ Related Passages in The Urantia Book")
if not urantia_lines:
    st.error("📂 data/urantia_en.txt 파일이 없습니다. data 폴더에 추가하세요.")
elif term and passages:
    for i, line in enumerate(passages, 1):
        st.markdown(f"<b>{i}.</b> {highlight_term(line, term)}", unsafe_allow_html=True)
elif term:
    st.info("No passages found. Try another related term.")

st.header("3️⃣ Generate Theological Report + 5 Slides")
st.caption("AI will analyze the passages and create both a report and a slide outline with notes.")

if st.button("✨ Generate AI Report & Slides", key="generate_btn"):
    with st.spinner("AI is writing a theological synthesis and slides..."):
        result = generate_gpt_report_and_slides(term, passages)
    st.markdown(result)
else:
    st.info("주제 입력 후 버튼을 눌러 보고서 + 슬라이드를 생성하세요.")




