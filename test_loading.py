import streamlit as st
import time

st.set_page_config(layout="centered")

def loading_animation():
    placeholder = st.empty()
    
    # CSS for the animation
    html_code = """
    <div class="loading-container">
        <div class="logo-text">NexGen Inventory</div>
        <div class="made-by">Made by Ganesh</div>
        <div class="loader"></div>
    </div>
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&display=swap');
    
    .loading-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        height: 60vh;
        background: radial-gradient(circle at center, #1e1b4b 0%, #020617 100%);
        border-radius: 20px;
        box-shadow: 0 0 50px rgba(99, 102, 241, 0.2);
        color: white;
        font-family: 'Inter', sans-serif;
        animation: fadeIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
        text-align: center;
    }
    
    .logo-text {
        font-family: 'Orbitron', sans-serif;
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #a5b4fc 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 15px;
        opacity: 0;
        animation: slideDown 1s cubic-bezier(0.4, 0, 0.2, 1) 0.2s forwards;
    }
    
    .made-by {
        font-size: 1.2rem;
        color: #94a3b8;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-bottom: 50px;
        opacity: 0;
        animation: slideUp 1s cubic-bezier(0.4, 0, 0.2, 1) 0.6s forwards;
    }
    
    .loader {
        width: 60px;
        height: 60px;
        position: relative;
        opacity: 0;
        animation: fadeIn 1s ease-in 1s forwards;
    }
    
    .loader:before, .loader:after {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        border: 4px solid transparent;
        border-top-color: #818cf8;
        animation: spin 1.5s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite;
    }
    
    .loader:after {
        border-top-color: #c084fc;
        animation: spin 1s cubic-bezier(0.68, -0.55, 0.265, 1.55) infinite reverse;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg) scale(1); }
        50% { transform: rotate(180deg) scale(1.1); }
        100% { transform: rotate(360deg) scale(1); }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }
    </style>
    """
    
    placeholder.markdown(html_code, unsafe_allow_html=True)
    time.sleep(3.5)
    placeholder.empty()

if 'show_loading' in st.session_state and st.session_state['show_loading']:
    loading_animation()
    st.session_state['show_loading'] = False
    st.session_state['logged_in'] = True
    st.rerun()

if 'logged_in' not in st.session_state:
    if st.button("Simulate Login"):
        st.session_state['show_loading'] = True
        st.rerun()
else:
    st.title("Main App Dashboard")
    st.success("You are now logged in and viewing the dashboard!")
    if st.button("Logout"):
        st.session_state.clear()
        st.rerun()
