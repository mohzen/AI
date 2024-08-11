import os
from langchain_chroma import Chroma
from langchain_experimental.open_clip import OpenCLIPEmbeddings

def setup_chroma_vectorstore(path, collection_name="mm_rag_clip_photos"):
    vectorstore = Chroma(
        collection_name=collection_name,
        embedding_function=OpenCLIPEmbeddings(),
        persist_directory="./chroma_db"
    )
    
    image_uris = sorted(
        [
            os.path.join(path, image_name)
            for image_name in os.listdir(path)
            if image_name.endswith(".jpg")
        ]
    )
    
    vectorstore.add_images(uris=image_uris)
    return vectorstore

def add_texts_to_vectorstore(vectorstore, texts):
    vectorstore.add_texts(texts=texts)

def get_retriever(vectorstore):
    return vectorstore.as_retriever()
