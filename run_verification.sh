#!/bin/bash
# Wrapper script to run verification with virtual environment

echo "🔍 AI Document Processing Workflow Verification"
echo "================================================"
echo ""

# Activate virtual environment
if [ -d "venv" ]; then
    echo "✓ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please create one with: python3 -m venv venv"
    exit 1
fi

# Run verification script
echo "✓ Running verification tests..."
echo ""
python verify_ai_workflow.py

# Deactivate
deactivate
