#!/bin/bash
# Quick start script for Yalom with Groq

echo "🚀 Yalom with Groq - Quick Start"
echo "================================"
echo ""

# Check if API key is set
if [ -z "$GROQ_YALOM_API_KEY" ]; then
    echo "❌ GROQ_YALOM_API_KEY environment variable not set!"
    echo ""
    echo "📝 Steps to set it up:"
    echo ""
    echo "1. Get your API key from: https://console.groq.com"
    echo "2. Set the environment variable:"
    echo ""
    echo "   export GROQ_YALOM_API_KEY=gsk_your_key_here"
    echo ""
    echo "3. To make it permanent, add to ~/.zshrc:"
    echo ""
    echo "   echo 'export GROQ_YALOM_API_KEY=gsk_your_key_here' >> ~/.zshrc"
    echo "   source ~/.zshrc"
    echo ""
    exit 1
fi

echo "✅ API key found: ${GROQ_YALOM_API_KEY:0:10}...${GROQ_YALOM_API_KEY: -4}"
echo ""

# Install dependencies
echo "📦 Installing dependencies..."
poetry install --quiet 2>&1 | grep -v "does not contain any element" || true
echo "✅ Dependencies installed"
echo ""

# Ask what to do
echo "What would you like to do?"
echo ""
echo "1) Test Groq integration"
echo "2) Run Streamlit web app"
echo "3) Both"
echo ""
read -p "Choose (1-3): " choice

case $choice in
    1)
        echo ""
        echo "🧪 Testing Groq integration..."
        echo ""
        poetry run python test_groq_integration.py
        ;;
    2)
        echo ""
        echo "🌐 Starting Streamlit app..."
        echo ""
        poetry run streamlit run app/streamlit_app.py
        ;;
    3)
        echo ""
        echo "🧪 Testing Groq integration first..."
        echo ""
        poetry run python test_groq_integration.py

        if [ $? -eq 0 ]; then
            echo ""
            read -p "✅ Test passed! Press Enter to launch Streamlit app..."
            echo ""
            echo "🌐 Starting Streamlit app..."
            echo ""
            poetry run streamlit run app/streamlit_app.py
        else
            echo ""
            echo "❌ Test failed. Please fix errors before running the app."
            exit 1
        fi
        ;;
    *)
        echo "Invalid choice. Exiting."
        exit 1
        ;;
esac
