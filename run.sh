#!/bin/bash
# ╔══════════════════════════════════════════════════════╗
# ║       InterviewAI - Setup & Run Script               ║
# ╚══════════════════════════════════════════════════════╝

echo ""
echo "🚀 InterviewAI Setup"
echo "═══════════════════"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.10+"
    exit 1
fi

echo "✓ Python $(python3 --version)"

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "→ Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
source venv/bin/activate

# Install dependencies
echo "→ Installing dependencies..."
pip install -r requirements.txt -q

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo "→ Creating .env template..."
    echo "GROQ_API_KEY=your-groq-api-key-here" > .env
    echo "SECRET_KEY=your-flask-secret-key-change-this"  >> .env
    echo ""
    echo "📝 Please edit .env and add your GROQ_API_KEY"
    echo "   Get your key at: https://console.groq.com"
    echo ""
fi

# Load env vars
export $(cat .env | xargs) 2>/dev/null

# Create uploads dir
mkdir -p uploads

echo ""
echo "✅ Setup complete!"
echo ""
echo "🌐 Starting server at http://localhost:5000"
echo "   Press Ctrl+C to stop"
echo ""

python3 app.py
