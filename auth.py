import bcrypt
import streamlit as st

# Fake users for now (we'll use database later)
# Format: username -> hashed password
users = {
    "testuser": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
}

def hash_password(password):
    """Turn plain password into secret code"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_password(password, hashed):
    """Check if password matches the secret code"""
    return bcrypt.checkpw(password.encode('utf-8'), hashed)

def register_user(username, password):
    """Add a new user (fake for now)"""
    if username in users:
        return False, "Username already taken!"
    hashed = hash_password(password)
    users[username] = hashed
    return True, "Registration successful! You can now log in."

def login_user(username, password):
    """Check if login is correct"""
    if username in users and check_password(password, users[username]):
        return True, "Login successful!"
    return False, "Wrong username or password."