import streamlit as st


def main():
    st.set_page_config(page_title="Welcome", page_icon="⚽️")
    st.write("# Welcome to ToELO! ⚽️")
    st.sidebar.success("Select a demo above.")
    st.markdown(
        """
        ToELO is a football player analyser.
        ### Featrues
        Currently focuesd on analysing football players ELO
        """
    )


if __name__ == "__main__":
    main()
