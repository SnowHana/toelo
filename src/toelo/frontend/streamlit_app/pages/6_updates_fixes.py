from pathlib import Path
import streamlit as st


def read_markdown_file(markdown_file):
    return Path(markdown_file).read_text()


st.set_page_config(page_title="Updates & Fixes & Enhancements", page_icon="💡")

st.sidebar.header("Updates & Fixes & Enhancements")


DOC_PATH = Path(__file__).resolve().parents[5] / "docs" / "updates.md"


update_md = read_markdown_file(DOC_PATH)
st.markdown(update_md)
# print(DOC_PATH)
