import streamlit as st
from user_query import user_query
from location_agent import agent
import subprocess


def handle_voice_input():
    st.info("🎤 Handling voice input...")
    # Add voice processing logic here
    user_query.process_query("rathish", "voice")
    st.success("Voice processed successfully!")

def handle_chat_input(query):
    st.info(f"🧠 Handling chat input: '{query}'")
    # Add query handling / LLM call here
    return user_query.process_query("rathish", "text", query)

# Page config
st.set_page_config(page_title="Tachyon-5", layout="wide")

# Title
st.title("Tachyon-5")

# Layout: Sidebar for Notifications
with st.sidebar:
    # result = subprocess.run(['adk', 'run', './location_agent'], capture_output=True, text=True, check=True)
    st.header("Notifications")
    notLi = [ "Probable purchase at Starbucks, HSR", "You've recently purchased clothes from Zudio, HSR. Wanna try again?",
      "Mani's Dum Biryani seems to be your go to restraunt. Its nearby",
      "Seems like you've visited Koramangala, but no bills?"
    ]
    for i in range(4):
        with st.container():
            st.write(f"🔔 {notLi[i]}")
            st.divider()

# Main Chat-like Interface
st.markdown("## Chat Interface")
chat_history = st.container()

# Upload section
st.markdown("### Upload a Bill Receipt")
uploaded_file = st.file_uploader("Upload bill receipt (PDF/Image)", type=["pdf", "png", "jpg", "jpeg"])

if uploaded_file:
    st.success(f"Uploaded: {uploaded_file.name}")

# # Voice Input Placeholder (Real-time voice integration can be added later)
# st.markdown("### Ask Using Voice")
# if st.button("🎙️ Click to Speak"):
#     st.info("Voice input feature coming soon...")

# # Chat Input
# user_input = st.text_input("Type your query about the receipt...")

# if user_input:
#     with chat_history:
#         st.chat_message("user").write(user_input)
#         st.chat_message("assistant").write("Answer will be generated here.")

# Voice Input Button
st.markdown("### Ask Using Voice")
if st.button("🎙️ Click to Speak"):
    handle_voice_input()

# Chat Input
user_input = st.text_input("Type your query about the receipt...")

if st.button("💬 Send Query"):
    if user_input.strip():
        with chat_history:
            st.chat_message("user").write(user_input)
            response = handle_chat_input(user_input)
            print("TRACE: ", response)
            st.chat_message("assistant").write(response)
    else:
        st.warning("Please type something before sending.")
