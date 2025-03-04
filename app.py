import streamlit as st

# Set the title of the app
st.title("Simple Greeting App")

# Input field for user's name
name = st.text_input("Enter your name:", "")

# Display greeting message
if name:
    st.success(f"Hello, {name}! Welcome to Streamlit 🎉")
