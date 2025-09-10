from fastapi import FastAPI
from pydantic import BaseModel
import os

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# CONSTANTS
CHROMA_PATH = os.path.join("..", "..", "data", "chroma")
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
OLLAMA_MODEL = "qwen2:1.5b"

# --- Pydantic Model for Request Body ---
class Query(BaseModel):
    text: str

# --- Initialize FastAPI App ---
app = FastAPI()

# --- Load Models and Vector Store on Startup --- 
print("Loading vector store and models...")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # Retrieve top 3 chunks
llm = ChatOllama(model=OLLAMA_MODEL)
print("Loading complete.")

# --- Define the RAG Chain ---
PROMTP_TEMPLATE = """
Answer the question based only on the following context:
{context}
---
Answer the question based on the above context: {question}
"""
prompt = ChatPromptTemplate.from_template(PROMTP_TEMPLATE)

chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# --- Define the API Endpoint ---
@app.post("/query")
async def process_query(query: Query):
    """
    Porcesses a user query using the RAG chain
    """
    print(f"Received query: {query.text}")
    response = chain.invoke(query.text)
    return {"response": response}