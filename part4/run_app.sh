#!/bin/bash

# Run E-commerce RAG Chatbot

echo "Starting E-commerce RAG Chatbot..."
echo "=================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run: python3 -m venv venv && venv/bin/pip install -r requirements-app.txt"
    exit 1
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found"
    echo "Please create .env with required configuration"
    exit 1
fi

# Check if data directory exists
if [ ! -d "data" ]; then
    echo "Error: data directory not found"
    echo "Please run Notebook 01 to generate knowledge base chunks"
    exit 1
fi

echo "Configuration validated"
echo "Starting Streamlit app..."
echo ""
echo "The app will open in your browser at: http://localhost:8501"
echo "Press Ctrl+C to stop the server"
echo ""

# Run Streamlit
venv/bin/streamlit run app.py
