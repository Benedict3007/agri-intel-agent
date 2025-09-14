from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os

from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.tools.retriever import create_retriever_tool

from src.agent.tools import get_crop_price_data, plot_crop_price_chart

# CONSTANTS
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CHROMA_PATH = os.path.join(PROJECT_ROOT, "data", "chroma")
CHARTS_DIR = os.path.join(PROJECT_ROOT, "data", "charts")
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
OLLAMA_MODEL = "llama3.1:8b-instruct-q4_K_M"

# --- Pydantic Model for Request Body ---
class Query(BaseModel):
    text: str

# --- Initialize FastAPI App ---
app = FastAPI()
app.mount("/charts", StaticFiles(directory=CHARTS_DIR), name="charts")

# --- Load Models and Vector Store on Startup --- 
print("Loading vector store and models...")
embeddings = HuggingFaceEmbeddings(model_name=EMBEDDING_MODEL)
vector_store = Chroma(persist_directory=CHROMA_PATH, embedding_function=embeddings)
retriever = vector_store.as_retriever(search_kwargs={"k": 3}) # Retrieve top 3 chunks
llm = ChatOllama(model=OLLAMA_MODEL)
print("Loading complete.")

# --- Agent Tools Definition ---
# Tool 1: RAG System (Document-Analysis)
retriever_tool = create_retriever_tool(
    retriever,
    "report_analyst_tool",
    "Searches through the EU agricultural reports to answer questions on content, predictions and market analysis. Useful to understand the 'why' behind market decisions."
)

# Tool 2: API-Tool (Quantitive-Analysis)
price_tools = [get_crop_price_data, plot_crop_price_chart]

# Combination of tools
tools = [retriever_tool] + price_tools

# --- Agent-Prompt creation ---
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an intelligent assistant for the agricultural market. Use available tools to answer the users questions."
            " IMPORTANT: When you use the 'plot_crop_price_chart' tool, you MUST include the exact chart path (e.g., '/charts/chart_name.png') "
            "it returns in your final answer. The user interface relies on this path to display the image."
        ),
        ("user", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ]
)

# --- Agent creation ---
agent = create_tool_calling_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True) # Show "Thought"-Process

# --- Define the API Endpoint ---
@app.post("/query")
async def process_query(query: Query):
    """
    Porcesses a user query using the RAG chain
    """
    print(f"Received query: {query.text}")
    response = agent_executor.invoke({"input": query.text})
    return {"response": response.get("output", "Couldn't find an answer.")}