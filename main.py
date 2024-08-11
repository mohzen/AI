import os
import json
import streamlit as st
import base64
from dotenv import load_dotenv
from langchain_chroma import Chroma
from vector_store import get_retriever
from llm import setup_chain
from langchain_experimental.open_clip import OpenCLIPEmbeddings

from openai import OpenAI
import torch.nn as nn

# helper imports
from tqdm import tqdm
import json
import os
import numpy as np
import pickle
from typing import List, Union, Tuple
# Load environment variables
def set_environment_variables():
    load_dotenv()  # This loads environment variables from the .env file

# Setup vector store and chain for RAG once, when the app is initialized
def initialize_rag_system():
    vectorstore = Chroma(
        persist_directory="./chroma_db",
        embedding_function=OpenCLIPEmbeddings(),
        collection_name="mm_rag_clip_photos"
    )
    retriever = get_retriever(vectorstore)
    chain = setup_chain(retriever)
    return chain

# Function to handle RAG query
def rag_query(chain, prompt):
    result = chain.invoke(prompt)
    return result

# Function to encode image in base64 format
def encode_image(image_path):
    with open(image_path, 'rb') as image_file:
        encoded_image = base64.b64encode(image_file.read())
        return encoded_image.decode('utf-8')

# Function to handle image query
def image_query(query, image_path):
    # Assuming you have a setup for client.chat.completions.create
    client = OpenAI()
    response = client.chat.completions.create(
        model='gpt-4o',
        messages=[
            {
            "role": "user",
            "content": [
                {
                "type": "text",
                "text": query,
                },
                {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{encode_image(image_path)}",
                },
                }
            ],
            }
        ],
        max_tokens=300,
    )
    # Extract relevant features from the response
    return response.choices[0].message.content

# Main function for the Streamlit app
def main():
    set_environment_variables()

    # Initialize the RAG system (only once)
    if "chain" not in st.session_state:
        with tqdm(total=2, desc="Initializing System", unit="step") as pbar:
            st.session_state.chain = initialize_rag_system()
            pbar.update(2)

    # Set up the app UI
    st.title("Manufacturing Q&A")
    mode = st.radio("Choose Query Type:", ("RAG (Document Query)", "Visual Question Answering"))

    # RAG flow
    if mode == "RAG (Document Query)":
        st.header("AI/ML Manufacturing Query System")

        # Initialize the chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display existing chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Handle user input
        if prompt := st.chat_input("Ask me anything about manufacturing"):
            # Append user's message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate the AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    result = rag_query(st.session_state.chain, prompt)
                    st.markdown(result)

            # Append the assistant's response
            st.session_state.messages.append({"role": "assistant", "content": result})

    # Image Question Answering flow
    elif mode == "Visual Question Answering":
        st.header("Visual Manufacturing Question & Answering")

        uploaded_file = st.file_uploader("Upload an Image", type=["jpg", "jpeg", "png"])
        # Ensure the temp directory exists
        temp_dir = "temp"
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)

        # Save the uploaded image
        # Validate and save the uploaded image
        if uploaded_file.name:
            image_path = os.path.join(temp_dir, uploaded_file.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())


        if uploaded_file is not None:
            # Save the uploaded image
            image_path = os.path.join("temp", uploaded_file.name)
            with open(image_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Handle user input
            query = st.text_input("Ask a question about the image:")
            if query:
                with st.spinner("Analyzing the image and generating response..."):
                    result = image_query(query, image_path)
                    st.markdown(f"**Answer:** {result}")

    # Footer (Optional)
    st.markdown("---")
    st.markdown("Made with ❤️ by (https://yourwebsite.com)")

if __name__ == "__main__":
    main()
