import streamlit as st

st.set_page_config(page_title="Cirencester Foodbank Dashboard", layout="wide")

# Define navigation with `st.navigation`
pages = st.navigation(
    [
        st.Page("pages/Crisis_Analysis.py", title="📖 Crisis Analysis"),
        st.Page("pages/Geographical_Analysis.py", title="📖 Geographical Analysis"),
        st.Page("pages/Individual_Client_Journey.py", title="📖 Individual Client Journey"),
    ]
)

# Run the selected page
pages.run()
