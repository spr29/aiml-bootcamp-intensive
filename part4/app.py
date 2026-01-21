"""
E-commerce RAG Chatbot - Streamlit Application

A production-ready chatbot with multiple retrieval strategies,
conversation memory, and source attribution.
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ecommerce_rag import ConversationalRAG
from ecommerce_rag.config import Config

# Page configuration
st.set_page_config(
    page_title="E-commerce Support Chatbot",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .assistant-message {
        background-color: #f5f5f5;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    .source-box {
        background-color: #fff3cd;
        padding: 0.5rem;
        border-radius: 5px;
        margin: 0.25rem 0;
        font-size: 0.85rem;
    }
    .metric-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if 'chatbot' not in st.session_state:
    st.session_state.chatbot = None
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'config_valid' not in st.session_state:
    st.session_state.config_valid = Config.validate()


def initialize_chatbot(retrieval_method: str):
    """Initialize or reinitialize the chatbot."""
    st.session_state.chatbot = ConversationalRAG(retrieval_method=retrieval_method)
    st.session_state.messages = []


def display_message(role: str, content: str, sources: list = None):
    """Display a chat message with optional sources."""
    if role == "user":
        st.markdown(f'<div class="user-message"><strong>You:</strong><br>{content}</div>',
                   unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="assistant-message"><strong>Assistant:</strong><br>{content}</div>',
                   unsafe_allow_html=True)

        if sources:
            with st.expander("View Sources", expanded=False):
                for source in sources:
                    source_name = source['source'].split('/')[-1] if '/' in source['source'] else source['source']
                    st.markdown(
                        f'<div class="source-box">[{source["index"]}] {source_name} '
                        f'(Relevance: {source["score"]:.4f})</div>',
                        unsafe_allow_html=True
                    )


# Sidebar
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # Configuration status
    if st.session_state.config_valid:
        st.success("Configuration loaded successfully")
    else:
        st.error("Configuration incomplete. Check .env file.")
        st.stop()

    st.markdown("---")

    # Retrieval method selection
    st.markdown("### Retrieval Strategy")
    retrieval_method = st.selectbox(
        "Select method:",
        ["hybrid", "vector", "bm25"],
        help="Hybrid combines vector and keyword search for best results"
    )

    if st.button("Apply Settings"):
        initialize_chatbot(retrieval_method)
        st.success(f"Chatbot initialized with {retrieval_method} retrieval")

    st.markdown("---")

    # System info
    st.markdown("### System Info")
    config_summary = Config.get_summary()
    st.markdown(f"**Model:** {config_summary['llm_model']}")
    st.markdown(f"**Results:** {config_summary['num_results']}")
    st.markdown(f"**Region:** {config_summary['aws_region']}")

    st.markdown("---")

    # Conversation controls
    st.markdown("### Conversation")

    if st.session_state.chatbot:
        st.metric("Messages", len(st.session_state.messages))

        # Show user context if available
        if st.session_state.chatbot.user_context:
            st.markdown("**Remembered Info:**")
            for key, value in st.session_state.chatbot.user_context.items():
                st.markdown(f"- {key.replace('_', ' ').title()}: {value}")

        if st.button("Clear Conversation"):
            st.session_state.chatbot.clear_history()
            st.session_state.messages = []
            st.rerun()

        if st.button("Export Conversation"):
            if st.session_state.messages:
                conversation = st.session_state.chatbot.export_conversation()
                st.download_button(
                    label="Download JSON",
                    data=str(conversation),
                    file_name=f"conversation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )

    st.markdown("---")

    # About
    st.markdown("### About")
    st.markdown("""
    This chatbot uses:
    - **Retrieval**: Vector, BM25, or Hybrid search
    - **Generation**: LLM-powered responses
    - **Memory**: Conversation context tracking
    - **Sources**: Citation and attribution
    """)


# Main content
st.markdown('<div class="main-header">🛍️ E-commerce Support Chatbot</div>',
           unsafe_allow_html=True)

# Initialize chatbot if not already done
if st.session_state.chatbot is None:
    initialize_chatbot(retrieval_method)
    st.info(f"Chatbot initialized with **{retrieval_method}** retrieval strategy")

# Example questions
if not st.session_state.messages:
    st.markdown("### Try asking:")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("What is your return policy?"):
            st.session_state.example_query = "What is your return policy?"

    with col2:
        if st.button("How long does shipping take?"):
            st.session_state.example_query = "How long does shipping take?"

    with col3:
        if st.button("Do you offer free shipping?"):
            st.session_state.example_query = "Do you offer free shipping?"

# Chat interface
st.markdown("---")

# Display conversation history
for message in st.session_state.messages:
    display_message(
        message["role"],
        message["content"],
        message.get("sources")
    )

# Chat input
if prompt := st.chat_input("Ask me anything about our policies..."):
    process_query = prompt
elif hasattr(st.session_state, 'example_query'):
    process_query = st.session_state.example_query
    delattr(st.session_state, 'example_query')
else:
    process_query = None

if process_query:
    # Add user message to chat
    st.session_state.messages.append({
        "role": "user",
        "content": process_query
    })

    # Display user message
    display_message("user", process_query)

    # Generate response
    with st.spinner("Thinking..."):
        try:
            response = st.session_state.chatbot.chat(process_query)

            # Add assistant message to chat
            st.session_state.messages.append({
                "role": "assistant",
                "content": response["answer"],
                "sources": response["sources"]
            })

            # Display assistant message
            display_message(
                "assistant",
                response["answer"],
                response["sources"]
            )

        except Exception as e:
            st.error(f"Error generating response: {str(e)}")

# Footer
st.markdown("---")
st.markdown(
    '<div style="text-align: center; color: #666; font-size: 0.85rem;">'
    'Powered by RAG Technology | Built with Streamlit'
    '</div>',
    unsafe_allow_html=True
)
