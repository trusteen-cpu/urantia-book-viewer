import streamlit as st
import re
import os

# ------------------------------------------------------------
# Page Config (전체 폭 넓게)
# ------------------------------------------------------------
st.set_page_config(page_title="Urantia Viewer", layout="wide")

# ------------------------------------------------------------
# 데이터 경로
# ------------------------------------------------------------
KO_PATH = os.path.join("data", "urantia_ko.txt")
EN_PATH = os.path.join("data", "urantia_en.txt")

# ------------------------------------------------------------
# 안전한 파일 읽기 (인코딩 자동 판별 시도)
# ------------------------------------------------------------
def safe_read_lines(path):
    encodings_to_try = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "utf-16", "latin-1"]
    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.readlines()
        except Exception:
            continue
    # 최후 수단
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
                key = m.group(1).strip()
                val = clean_text(m.group(2))
                data[key] = val
        return data

    ko = parse_file(KO_PATH)
    en = parse_file(EN_PATH)
    return ko, en

ko_texts, en_texts = load_texts()

# ------------------------------------------------------------
# 헬퍼: ref에 맞는 (절번호, 한글, 영문) 쌍 만들기
# ------------------------------------------------------------
def get_pairs_by_ref(ref: str):
    pairs = []

    # 절 (e.g., 196:2.3)
    if re.match(r"^\d+:\d+\.\d+$", ref):
        if ref in ko_texts:
            pairs.append((ref, ko_texts[ref], en_texts.get(ref, "")))
        return pairs

    # 장 (e.g., 196:2)
    if re.match(r"^\d+:\d+$", ref):
        prefix = ref + "."
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append((k, v, en_texts.get(k, "")))
        return pairs

    # 편 (e.g., 196)
    if re.match(r"^\d+$", ref):
        prefix = ref + ":"
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append((k, v, en_texts.get(k, "")))
        return pairs

    return pairs

# ------------------------------------------------------------
# 스타일 & 스크립트
# ------------------------------------------------------------
st.markdown("""
<style>
.block-container {max-width: 96vw !important;}
.viewer-wrapper {width: 96vw; margin: 0 auto;}
.verse-row {display: flex; gap: 20px; align-items: stretch; margin-bottom: 18px;}
.verse-col {
  flex: 1 1 50%;
  background: #fafafa;
  border-radius: 12px;
  padding: 16px 18px;
  line-height: 1.9;
  font-size: 17px;
  word-wrap: break-word;
  box-shadow: 0 0 8px rgba(0,0,0,0.04);
}
.section-title {margin: 6px 0 16px 0;}
.tools {margin-top: 8px; display: flex; gap: 6px; flex-wrap: wrap;}
.tools button {
  background: #f1f1f1; border: none; padding: 4px 8px; border-radius: 8px;
  cursor: pointer; font-size: 14px;
}
.tools button:hover {background: #e7e7e7;}
</style>

<script>
function copyText(divId){
  const el=document.getElementById(divId);
  if(!el) return;
  navigator.clipboard.writeText(el.innerText);
}
function readText(divId){
  const el=document.getElementById(divId);
  if(!el) return;
  const u=new SpeechSynthesisUtterance(el.innerText);
  u.lang=/[가-힣]/.test(el.innerText)?'ko-KR':'en-US';
  speechSynthesis.speak(u);
}
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("📘 Urantia Book Viewer")
st.caption("Paper/Section/Paragraph lookup with side-by-side KO/EN layout.")

ref = st.text_input("참조를 입력하세요 (예: 196, 196:2, 196:2.3)", "").strip()

if ref:
    pairs = get_pairs_by_ref(ref)

    if not pairs:
        st.warning("일치하는 본문이 없습니다. 예: 196, 196:2, 196:2.3 형식으로 입력해 보세요.")
    else:
        html = []
        for key, ko, en in pairs:
            html.append(f"""
            <div class="verse-row">
              <div class="verse-col" id="ko-{key}">
                <div class="section-title"><b>🇰🇷 Korean</b></div>
                <div><b>{key}</b> — {clean_text(ko)}</div>
                <div class="tools">
                  <button onclick="copyText('ko-{key}')">📋 복사</button>
                  <button onclick="readText('ko-{key}')">🔊 낭독</button>
                </div>
              </div>
              <div class="verse-col" id="en-{key}">
                <div class="section-title"><b>🇺🇸 English</b></div>
                <div><b>{key}</b> — {clean_text(en)}</div>
                <div class="tools">
                  <button onclick="copyText('en-{key}')">📋 Copy</button>
                  <button onclick="readText('en-{key}')">🔊 Read</button>
                </div>
              </div>
            </div>
            """)

        full_html = "<div class='viewer-wrapper'>" + "".join(html) + "</div>"
        st.components.v1.html(full_html, height=8000, scrolling=True)
else:
    st.info("예: 196 (편), 196:2 (장), 196:2.3 (절) 형태로 검색해 보세요.")
