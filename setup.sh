#!/bin/bash
# Quick setup script for MetaErase Bot

echo "🧹 MetaErase Bot — Setup"
echo "========================"

# Check Python version
python3 --version || { echo "❌ Python 3 not found. Install it first."; exit 1; }

# Create venv
echo "📦 Creating virtual environment..."
python3 -m venv venv || { echo "❌ Failed to create venv"; exit 1; }
source venv/bin/activate

# Install deps
echo "⬇️  Installing dependencies..."
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt || { echo "❌ Failed to install deps"; exit 1; }

# Setup .env
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo "⚠️  Edit .env and add your BOT_TOKEN!"
else
    echo "✅ .env already exists"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your BOT_TOKEN"
echo "  2. Run: source venv/bin/activate && python bot.py"
echo ""
