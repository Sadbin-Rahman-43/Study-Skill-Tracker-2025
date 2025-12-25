import streamlit as st
from auth import register_user, login_user

# Sticky note to remember if logged in
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'page' not in st.session_state:
    st.session_state.page = "login"

# Sidebar menu (like a navigation bar)
# Sidebar menu (like a navigation bar)
st.sidebar.title("📚 Study Tracker")

if st.session_state.logged_in:
    st.sidebar.write(f"Welcome, {st.session_state.username}!")
    
    if st.sidebar.button("Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()  # This makes the page refresh and show the new content
    
    if st.sidebar.button("Log Out"):
        st.session_state.logged_in = False
        st.session_state.page = "login"
        st.rerun()
else:
    # When NOT logged in, show Login & Register buttons
    if st.sidebar.button("Login"):
        st.session_state.page = "login"
        st.rerun()
    
    if st.sidebar.button("Register"):
        st.session_state.page = "register"
        st.rerun()

# Main content based on current page
st.title("Study & Skill Tracker")

if not st.session_state.logged_in:
    if st.session_state.page == "login":
        st.header("Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Log In")

        if submitted:
            success, message = login_user(username, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.page = "dashboard"
                st.success(message)
                st.rerun()  # ← Add this line! It refreshes the page immediately
            else:
                st.error(message)

    elif st.session_state.page == "register":
        st.header("Register")
        with st.form("register_form"):
            new_username = st.text_input("Choose Username")
            new_password = st.text_input("Choose Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            submitted = st.form_submit_button("Sign Up")

        if submitted:
            if new_password != confirm_password:
                st.error("Passwords don't match!")
            elif not new_username or not new_password:
                st.error("Please fill all fields!")
            else:
                success, message = register_user(new_username, new_password)
                if success:
                    st.success(message + " Now log in!")
                    st.session_state.page = "login"
                else:
                    st.error(message)

else:
    # Dashboard page
    st.header(f"Welcome to your Dashboard, {st.session_state.username}! 🚀")
    st.write("Your study journey starts here! 🎓")
    st.info("Coming soon: Add skills, log study hours, see charts!")