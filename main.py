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
    last_err = None
    for enc in encodings_to_try:
        try:
            with open(path, "r", encoding=enc, errors="strict") as f:
                return f.readlines()
        except Exception as e:
            last_err = e
    # 최후: 대체문자로라도 연다
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
            pairs.append( (ref,
                           f"<b>{ref}</b> — {clean_text(ko_texts[ref])}",
                           f"<b>{ref}</b> — {clean_text(en_texts.get(ref, ''))}") )
        return pairs

    # 장 (e.g., 196:2)
    if re.match(r"^\d+:\d+$", ref):
        prefix = ref + "."
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append( (k,
                               f"<b>{k}</b> — {clean_text(v)}",
                               f"<b>{k}</b> — {clean_text(en_texts.get(k, ''))}") )
        return pairs

    # 편 (e.g., 196)
    if re.match(r"^\d+$", ref):
        prefix = ref + ":"
        for k, v in ko_texts.items():
            if k.startswith(prefix):
                pairs.append( (k,
                               f"<b>{k}</b> — {clean_text(v)}",
                               f"<b>{k}</b> — {clean_text(en_texts.get(k, ''))}") )
        return pairs

    return pairs

# ------------------------------------------------------------
# 스타일 & 툴(JS)
# ------------------------------------------------------------
st.markdown("""
<style>
/* Streamlit 기본 컨테이너 폭 확장 */
.block-container {
  padding-left: 2vw !important;
  padding-right: 2vw !important;
  max-width: 96vw !important;
}

/* 두 컬럼 래퍼: 화면 거의 꽉 채우기 */
.viewer-wrapper {
  width: 96vw;
  margin: 0 auto;
}

/* 행 단위로 KO/EN를 나란히: 같은 행에서 높이 자동 맞춤 */
.verse-row {
  display: flex;
  gap: 18px;
  align-items: stretch;   /* 같은 행에서 양쪽 칸 높이를 자동 같게 */
  margin-bottom: 18px;
}

/* 각 칼럼(한글/영문) */
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

/* 절 도구 버튼 줄 */
.tools {
  margin-top: 8px;
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}
.tools button {
  background: #f1f1f1;
  border: none;
  padding: 4px 8px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}
.tools button:hover {
  background: #e7e7e7;
}

/* 섹션 제목 */
.section-title {
  margin: 6px 0 16px 0;
}
</style>

<script>
// 복사
function copyText(divId) {
  const el = document.getElementById(divId);
  if (!el) return;
  const txt = el.innerText;
  navigator.clipboard.writeText(txt);
}

// 낭독 (브라우저 TTS)
function readText(divId) {
  const el = document.getElementById(divId);
  if (!el) return;
  const txt = el.innerText;
  const u = new SpeechSynthesisUtterance(txt);
  // 한글 포함 여부로 음성 선택
  u.lang = /[가-힣]/.test(txt) ? 'ko-KR' : 'en-US';
  speechSynthesis.speak(u);
}

// 북마크 (로컬 저장)
function bookmark(refId) {
  try {
    const key = 'urantia_bookmarks';
    const raw = localStorage.getItem(key);
    let arr = raw ? JSON.parse(raw) : [];
    if (!arr.includes(refId)) {
      arr.push(refId);
      localStorage.setItem(key, JSON.stringify(arr));
      alert('🔖 북마크 추가: ' + refId);
    } else {
      alert('이미 북마크되어 있습니다: ' + refId);
    }
  } catch(e) {
    alert('북마크 저장 중 오류가 발생했습니다.');
  }
}
</script>
""", unsafe_allow_html=True)

# ------------------------------------------------------------
# UI
# ------------------------------------------------------------
st.title("📘 Urantia Book Viewer")
st.caption("Paper/Section/Paragraph lookup with side-by-side KO/EN, full-width page layout.")

ref = st.text_input("참조를 입력하세요 (예: 196, 196:2, 196:2.3)", "").strip()

if ref:
    pairs = get_pairs_by_ref(ref)

    if not pairs:
        st.warning("일치하는 본문이 없습니다. 예: 196, 196:2, 196:2.3 형식으로 입력해 보세요.")
    else:
        # 헤더
        if re.match(r"^\d+:\d+\.\d+$", ref):
            st.markdown(f"### {ref}")
        elif re.match(r"^\d+:\d+$", ref):
            st.markdown(f"### 📖 Section {ref}")
        else:
            st.markdown(f"### 📜 Paper {ref}")

        # 본문: 네모 스크롤 박스 제거, 페이지 전체로 자연스럽게 흐르게
        full_html = "<div class='viewer-wrapper'>" + "".join(html) + "</div>"
st.components.v1.html(full_html, height=8000, scrolling=True)

else:
    st.info("예: 196 (편), 196:2 (장), 196:2.3 (절) 형태로 검색해 보세요.")
