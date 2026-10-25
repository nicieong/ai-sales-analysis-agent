import streamlit as st

st.set_page_config(
    page_title="AI Sales & Inventory Analyst",
    page_icon="📊",
    layout="wide",
)

main_page = st.Page(
    "main_page.py",
    title="Main Page",
    default=True,
)

supplementary_page = st.Page(
    "pages/1_Supplementary_Sales_Analysis.py",
    title="Supplementary Sales Analysis",
)

navigation = st.navigation([
    main_page,
    supplementary_page,
])

navigation.run()