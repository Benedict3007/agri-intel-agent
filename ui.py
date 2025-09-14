import streamlit as st
import requests
import json
import os
import re

# --- Configuration ---
API_URL ="http://127.0.0.1:8000/query"
st.set_page_config(page_title="Agri_Intel Agent", layout="wide")

# --- UI Elements ---
st.title("Agri-Intel Agent")
st.markdown("Ask a question abou European agricultural markets based on the latest reports.")

# Initialize session state for conversation history
if 'history' not in st.session_state:
    st.session_state['history'] = []

# Display conversation history
for chat in st.session_state.history:
    with st.chat_message(chat["role"]):
        st.markdown(chat["content"])
        if chat.get("image_path"):
            st.image(chat["image_path"])

# User input
if prompt := st.chat_input("What are the wheat production forecasts?"):
    # Add user message to history and display it
    st.session_state.history.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Prepare and send the request to the API
    headers = {"Content-Type": "application/json"}
    data = {"text": prompt}

    with st.spinner("Thinking..."):
        try:
            response = requests.post(API_URL, headers=headers, data=json.dumps(data))
            response.raise_for_status() # Raise an exception for bad status codes

            # Get the agents response
            result = response.json()
            answer = result.get("response", "Sorry, I couldn't get a response.")

            image_url = None
            match = re.search(r'(/charts/[a-zA-Z0-9/\\_.-]+\.png)', answer)

            if match:
                image_path_segment = match.group(1)
                base_api_url = API_URL.rsplit('/', 1)[0]
                image_url = f"{base_api_url}{image_path_segment}"

            assistant_respone = {"role": "assistant", "content": answer}
            if image_url:
                assistant_respone["image_path"] = image_url 
            st.session_state.history.append(assistant_respone)

            with st.chat_message("assistant"):
                st.markdown(answer)
                if image_url:
                    st.image(image_url)

        except requests.exceptions.RequestException as e:
            st.error(f"Could not connect to the API. Make sure it's running. Error: {e}")