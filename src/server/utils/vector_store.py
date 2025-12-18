import os
import chromadb
from typing import List
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

class VectorStoreManager:
    def __init__(self, agent_id: str = None, data_path: str = "data"):
        self.data_path = data_path
        self.agent_id = agent_id
        # Use agent-specific collection name if agent_id provided
        self.collection_name = f"agent_{agent_id}" if agent_id else "nexus_mind_docs"
        
        base_url = os.getenv("OPENAI_BASE_URL")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", base_url=base_url)
        self.vector_store = None
        
        chroma_host = os.getenv("CHROMA_HOST", "localhost")
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        
        try:
            self.client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
            print(f"Connected to ChromaDB at {chroma_host}:{chroma_port}")
        except Exception as e:
            print(f"Failed to connect to ChromaDB: {e}")
            self.client = None

    def ingest_data(self):
        """Loads data from the data directory and ingests into ChromaDB."""
        if not self.client:
            print("ChromaDB client not initialized. Is the Docker container running?")
            return

        if not os.path.exists(self.data_path):
            print(f"Data directory {self.data_path} not found.")
            return

        # Load text files
        loader = DirectoryLoader(self.data_path, glob="**/*.txt", loader_cls=TextLoader)
        docs = loader.load()
        
        if not docs:
            print("No documents found to ingest.")
            return

        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)

        # Ingest into Chroma
        self.vector_store = Chroma(
            client=self.client,
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
        )
        self.vector_store.add_documents(documents=splits)
        
        print(f"Ingested {len(splits)} chunks into ChromaDB.")

    def ingest_file(self, filepath: str, file_id: str = None):
        """Ingest a single file into the vector store with metadata for tracking."""
        if not self.client:
            raise ValueError("ChromaDB client not initialized. Is the Docker container running?")
        
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Load the file
        loader = TextLoader(filepath)
        docs = loader.load()
        
        if not docs:
            print(f"No content found in file: {filepath}")
            return
        
        # Split documents
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        splits = text_splitter.split_documents(docs)
        
        # Add metadata to track which file these chunks came from
        if file_id:
            for doc in splits:
                doc.metadata['file_id'] = file_id
                doc.metadata['source_file'] = os.path.basename(filepath)
        
        # Get or create vector store
        if not self.vector_store:
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        
        # Add documents
        self.vector_store.add_documents(documents=splits)
        print(f"Ingested {len(splits)} chunks from {os.path.basename(filepath)} into ChromaDB.")
        return len(splits)

    def delete_file(self, file_id: str):
        """Delete all embeddings for a specific file from the vector store."""
        if not self.client:
            raise ValueError("ChromaDB client not initialized. Is the Docker container running?")
        
        # Get or create vector store
        if not self.vector_store:
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        
        # Get the underlying collection
        collection = self.vector_store._collection
        
        # Query for documents with this file_id
        try:
            # Get all documents with matching file_id metadata
            results = collection.get(
                where={"file_id": file_id}
            )
            
            if results and results['ids']:
                # Delete the documents by their IDs
                collection.delete(ids=results['ids'])
                deleted_count = len(results['ids'])
                print(f"Deleted {deleted_count} chunks for file_id {file_id} from ChromaDB.")
                return deleted_count
            else:
                print(f"No chunks found for file_id {file_id} in ChromaDB.")
                return 0
        except Exception as e:
            print(f"Error deleting file from vector store: {e}")
            raise

    def get_retriever(self):
        """Returns a retriever for the vector store."""
        if not self.client:
             raise ValueError("ChromaDB client is not available. Please start the Docker services.")

        if not self.vector_store:
            self.vector_store = Chroma(
                client=self.client,
                collection_name=self.collection_name,
                embedding_function=self.embeddings,
            )
        return self.vector_store.as_retriever(search_kwargs={"k": 3})
