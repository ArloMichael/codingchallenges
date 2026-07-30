import streamlit as st
from zxcvbn import zxcvbn

def evaluate_password(password):
    if not password:
        return
    
    try:
        result = zxcvbn(password)
    except ValueError:
        st.error("Password must not exceed 72 characters.")
        return
    
    score = result['score']
    feedback_data = result['feedback']
    warning = feedback_data.get('warning')
    suggestions = feedback_data.get('suggestions', [])
    message = f"Broken in **{result['crack_times_display']['offline_fast_hashing_1e10_per_second']}** *(offline)* to **{result['crack_times_display']['online_throttling_100_per_hour']}** *(online & throttled)*." if result['crack_times_display']['offline_fast_hashing_1e10_per_second'] != "centuries" else "Broken in **centuries**."

    st.progress(score / 4, text="Strength")

    st.info(message, title="Brute Force Complexity")

    if warning:
        st.error(warning, title="Reason")
        
    if suggestions:
        for tip in suggestions:
            st.success(tip, title="Improvement")
            
    if score < 3 and not suggestions:
        st.write("Add more length, unique words, or mixed character types.")

st.set_page_config(
    page_title="Password Strength Checker",
)

st.write("# Password Strength Checker")

password = st.text_input("Password", type="password")
evaluate_password(password)