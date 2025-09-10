import os
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# CONSTANTS
DATA_PATH = os.path.join("data", "reports")
CHROMA_PATH = os.path.join("data", "chroma")
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"

def main():
    """
    Main function to load, split, and embed documents, then store them in ChromaDB
    """
    print("--- Starting Ingestion Process ---")
    
    # 1. Load documents from the specified dir
    print(f"Loading documents from: {DATA_PATH}")
    loader = PyPDFDirectoryLoader(DATA_PATH)
    documents = loader.load()
    if not documents:
        print("No documents found. Please check the DATA_PATH.")
        return
    print(f"Loaded {len(documents)} document(s).")

    # 2. Split the documents into smaller chunks
    print("Splitting documents into smaller chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = text_splitter.split_documents(documents)

    # 3. Create embeddings and store them in ChromaDB
    print(f"Creating embeddings using '{EMBEDDING_MODEL}' and storing in ChromaDB at: {CHROMA_PATH}")
    
    # Initialize embedding model
    # model_kwargs = {'device': 'cuda'}
    encode_kwargs = {'normalize_embeddings': True}
    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        # model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs
    )

    # Create or load the Chroma vector store
    # This will create the DB on the first run and add to it on subsequent runs
    vectore_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=CHROMA_PATH
    )

    print("\n--- Ingestion Process Complete ---")
    print(f"Vector store created/updated at:{CHROMA_PATH}")

if __name__ == "__main__":
    main()