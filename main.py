import streamlit as st
import pandas as pd

st.set_page_config(page_title="Urantia Book Viewer", layout="wide")

st.title("📘 Urantia Book Viewer")

# Load data files
try:
    with open("data/urantia_en.txt", "r", encoding="utf-8") as f:
        en_text = f.read().splitlines()
    with open("data/urantia_ko.txt", "r", encoding="utf-8") as f:
        ko_text = f.read().splitlines()
except FileNotFoundError:
    st.error("❌ Data files not found. Please upload urantia_en.txt and urantia_ko.txt to the data folder.")
    st.stop()

# Load glossary
try:
    glossary = pd.read_excel("data/glossary.xlsx")
except:
    glossary = pd.DataFrame(columns=["term-ko", "term-en", "description"])

# Input section
ref = st.text_input("Enter reference (e.g., 111:1.1):")

if ref:
    results_en = [line for line in en_text if ref in line]
    results_ko = [line for line in ko_text if ref in line]
    
    if results_en and results_ko:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Korean")
            st.write("\n\n".join(results_ko))
        with col2:
            st.subheader("English")
            st.write("\n\n".join(results_en))
    else:
        st.warning("No matching text found. Check your reference (e.g., 111:1.1).")

st.divider()
st.subheader("📚 Glossary Search")

term = st.text_input("Search term (Korean or English):")

if term:
    filtered = glossary[
        glossary.apply(lambda row: term.lower() in str(row["term-ko"]).lower() 
                       or term.lower() in str(row["term-en"]).lower(), axis=1)
    ]
    if len(filtered) > 0:
        for _, row in filtered.iterrows():
            st.markdown(f"**{row['term-ko']} ({row['term-en']})** — {row['description']}")
    else:
        st.info("No glossary entry found.")
