import streamlit as st

# This is like a sticky note that remembers if someone is logged in
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

# Fake user for today (we'll use real database later)
FAKE_USERNAME = "testuser"
FAKE_PASSWORD = "password123"

# Title of the app
st.title("📚 Study & Skill Tracker")

# If user is NOT logged in → show login form
if not st.session_state.logged_in:
    st.header("Login to Your Study Diary")

    # Make a nice form
    with st.form(key="login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")  # hides the letters
        login_button = st.form_submit_button("Log In")

    # When they click the button
    if login_button:
        if username == FAKE_USERNAME and password == FAKE_PASSWORD:
            st.session_state.logged_in = True
            st.success("Welcome back! 🎉 You are now logged in!")
            st.balloons()
        else:
            st.error("Oops! Wrong username or password. Try again.")

# If user IS logged in → show the main app
else:
    st.header("Welcome to your Dashboard! 🚀")
    st.write("You are logged in as: " + FAKE_USERNAME)
    
    # Logout button
    if st.button("Log Out"):
        st.session_state.logged_in = False
        st.success("You have been logged out. See you soon! 👋")
        st.rerun()  # Refresh the page