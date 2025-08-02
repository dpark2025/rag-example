import streamlit as st
import json
import os
from rag_backend import rag_system, LocalLLMClient

st.set_page_config(
    page_title="Local RAG System",
    page_icon="🤖",
    layout="wide"
)

def check_system_health():
    """Check if all components are working"""
    health_status = {
        "embeddings": True,  # SentenceTransformers always works locally
        "vector_db": True,   # ChromaDB always works locally
        "llm": rag_system.llm_client.health_check()
    }
    return health_status

def main():
    st.title("🤖 Fully Local RAG System")
    st.write("Complete offline knowledge base - your data never leaves your machine!")
    
    # Sidebar
    with st.sidebar:
        st.header("📊 System Status")
        
        health = check_system_health()
        
        st.metric("Embedding Model", "✅ Online" if health["embeddings"] else "❌ Offline")
        st.metric("Vector Database", "✅ Online" if health["vector_db"] else "❌ Offline")
        st.metric("Local LLM", "✅ Online" if health["llm"] else "❌ Offline")
        
        if not health["llm"]:
            st.error("⚠️ Ollama not responding. Check if container is running.")
        
        st.divider()
        
        # Document Management
        st.header("📚 Document Management")
        
        # Current document count
        doc_count = rag_system.collection.count()
        st.metric("Documents in KB", doc_count)
        
        # Upload documents
        with st.expander("Add Documents"):
            title = st.text_input("Document Title")
            content = st.text_area("Document Content", height=150)
            source = st.text_input("Source (optional)", value="manual_upload")
            
            if st.button("Add Document", type="primary"):
                if title and content:
                    result = rag_system.add_documents([{
                        "title": title,
                        "content": content,
                        "source": source
                    }])
                    st.success(result)
                    st.rerun()
                else:
                    st.error("Please provide both title and content")
        
        # Bulk upload
        with st.expander("Bulk Upload"):
            uploaded_file = st.file_uploader("Upload text files", type=['txt'], accept_multiple_files=True)
            
            if uploaded_file and st.button("Process Files"):
                documents = []
                for file in uploaded_file:
                    content = file.read().decode('utf-8')
                    documents.append({
                        "title": file.name,
                        "content": content,
                        "source": "file_upload"
                    })
                
                if documents:
                    result = rag_system.add_documents(documents)
                    st.success(f"Processed {len(documents)} files: {result}")
                    st.rerun()
        
        # Efficiency metrics in sidebar
        with st.expander("⚡ Efficiency Settings"):
            current_threshold = st.slider(
                "Similarity Threshold", 
                min_value=0.5, 
                max_value=0.9, 
                value=rag_system.similarity_threshold,
                step=0.05,
                help="Higher = more selective retrieval"
            )
            
            max_context = st.slider(
                "Max Context Tokens",
                min_value=500,
                max_value=4000,
                value=rag_system.max_context_tokens,
                step=250,
                help="Adjust based on your LLM's capabilities"
            )
            
            if st.button("Update Settings"):
                rag_system.similarity_threshold = current_threshold
                rag_system.max_context_tokens = max_context
                st.success("Settings updated!")
        
        # Show efficiency metrics
        if 'last_query_metrics' in st.session_state:
            metrics = st.session_state.last_query_metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Chunks Used", metrics.get('context_used', 0))
            with col2:
                st.metric("Context Tokens", metrics.get('context_tokens', 0))
            with col3:
                st.metric("Efficiency", f"{metrics.get('efficiency_ratio', 0):.3f}")
        
        # Sample documents
        if st.button("Add Sample Documents"):
            sample_docs = [
                {
                    "title": "Docker Basics",
                    "content": "Docker is a containerization platform that allows you to package applications and their dependencies into lightweight, portable containers. Containers ensure consistency across different environments.",
                    "source": "sample"
                },
                {
                    "title": "Local RAG Systems",
                    "content": "Retrieval-Augmented Generation (RAG) systems combine document retrieval with language generation. Local RAG systems run entirely on your machine, ensuring data privacy and eliminating API costs.",
                    "source": "sample"
                },
                {
                    "title": "Ollama Overview", 
                    "content": "Ollama is a tool for running large language models locally. It supports models like Llama, Mistral, and Codellama. Models can be pulled and run with simple commands like 'ollama pull llama3.2'.",
                    "source": "sample"
                }
            ]
            
            result = rag_system.add_documents(sample_docs)
            st.success(result)
            st.rerun()
    
    # Main chat interface
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant" and "sources" in message:
                st.write(message["content"])
                if message["sources"]:
                    with st.expander("📚 Sources"):
                        for source in message["sources"]:
                            st.write(f"• {source['title']} (Score: {source['score']})")
            else:
                st.write(message["content"])
    
    # Chat input
    if prompt := st.chat_input("Ask me anything about your documents..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.write(prompt)
        
        # Generate response
        with st.chat_message("assistant"):
            if not health["llm"]:
                response = "❌ Sorry, the local language model is not available. Please check if Ollama is running."
                sources = []
            else:
                with st.spinner("Searching knowledge base..."):
                    result = rag_system.rag_query(prompt)
                    response = result["answer"]
                    sources = result["sources"]
                    
                    # Store metrics for efficiency display
                    st.session_state.last_query_metrics = {
                        'context_used': result.get('context_used', 0),
                        'context_tokens': result.get('context_tokens', 0),
                        'efficiency_ratio': result.get('efficiency_ratio', 0)
                    }
                
                st.write(response)
                
                if sources:
                    with st.expander("📚 Sources"):
                        for source in sources:
                            st.write(f"• {source['title']} (Score: {source['score']})")
                    
                    # Show efficiency info
                    if 'context_tokens' in result:
                        st.caption(f"💡 Used {result['context_tokens']} context tokens from {result['context_used']} chunks")
        
        # Add assistant response
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "sources": sources
        })

if __name__ == "__main__":
    main()