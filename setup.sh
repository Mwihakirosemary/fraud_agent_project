#!/bin/bash
# Fraud Detection Agent - Quick Setup Script

echo "🔍 Fraud Detection Agent - Setup"
echo "================================"
echo ""

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create directories if they don't exist
echo ""
echo "📁 Creating project structure..."
mkdir -p agent
mkdir -p dashboard
mkdir -p data/structured
mkdir -p data/unstructured
mkdir -p outputs/cleaned
mkdir -p outputs/embeddings
mkdir -p outputs/investigations
mkdir -p vector_db/chroma

# Create __init__.py files
touch agent/__init__.py
touch dashboard/__init__.py

echo "✓ Directories created"

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
echo "This may take a few minutes..."

pip install -q google-generativeai python-dotenv \
    pandas numpy sentence-transformers chromadb \
    streamlit plotly scikit-learn tqdm pyarrow

echo "✓ Dependencies installed"

# Check for API key
echo ""
echo "🔑 Checking API key..."

if [ -f ".env" ]; then
    echo "✓ .env file found"
    if grep -q "GOOGLE_API_KEY" .env; then
        echo "✓ GOOGLE_API_KEY configured in .env"
    else
        echo "⚠️  GOOGLE_API_KEY not found in .env"
        echo ""
        echo "Please add your Google API key to .env:"
        echo "  echo 'GOOGLE_API_KEY=your-key-here' >> .env"
        echo ""
        echo "Get your free key at: https://aistudio.google.com/app/apikey"
    fi
else
    echo "⚠️  .env file not found"
    echo ""
    echo "Creating .env file..."
    echo "# Fraud Detection Agent Configuration" > .env
    echo "GOOGLE_API_KEY=your-api-key-here" >> .env
    echo ""
    echo "✓ .env file created"
    echo "📝 Please edit .env and add your Google API key"
    echo "   Get your free key at: https://aistudio.google.com/app/apikey"
fi

# Validate data files
echo ""
echo "📊 Checking data files..."

data_files=(
    "outputs/cleaned/creditcard_cleaned.parquet"
    "outputs/cleaned/siem_logs_cleaned.parquet"
    "outputs/cleaned/kyc_profiles_cleaned.parquet"
)

missing_files=0
for file in "${data_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "⚠️  Missing: $file"
        missing_files=$((missing_files + 1))
    fi
done

if [ $missing_files -gt 0 ]; then
    echo ""
    echo "⚠️  $missing_files data file(s) missing"
    echo "Please run Jupyter notebooks 1-3 to generate data:"
    echo "  1. 01_Data_Collection.ipynb"
    echo "  2. 02_Data_Cleaning_Preprocessing.ipynb"
    echo "  3. 03_Embedding_Generation_VectorDB.ipynb"
fi

# Check ChromaDB
echo ""
echo "🗄️  Checking ChromaDB..."

if [ -d "vector_db/chroma" ] && [ "$(ls -A vector_db/chroma 2>/dev/null)" ]; then
    echo "✓ ChromaDB database found"
else
    echo "⚠️  ChromaDB database not found"
    echo "Please run notebook 03_Embedding_Generation_VectorDB.ipynb"
fi

# Summary
echo ""
echo "================================"
echo "📋 Setup Summary"
echo "================================"
echo ""

if [ $missing_files -eq 0 ] && [ -f ".env" ] && grep -q "GOOGLE_API_KEY" .env && [ "$(ls -A vector_db/chroma 2>/dev/null)" ]; then
    echo "✅ Setup complete! You're ready to go."
    echo ""
    echo "🚀 Next steps:"
    echo "  1. Test agent tools:"
    echo "     python -c 'from agent.agent_tools import FraudAgentTools; t = FraudAgentTools()'"
    echo ""
    echo "  2. Run a test investigation:"
    echo "     python agent/investigation_workflow.py"
    echo ""
    echo "  3. Launch dashboard:"
    echo "     streamlit run dashboard/dashboard.py"
    echo ""
else
    echo "⚠️  Setup incomplete. Please address the warnings above."
    echo ""
    echo "Required steps:"
    if [ $missing_files -gt 0 ]; then
        echo "  • Run Jupyter notebooks to generate data"
    fi
    if [ ! -f ".env" ] || ! grep -q "GOOGLE_API_KEY" .env; then
        echo "  • Add GOOGLE_API_KEY to .env file"
    fi
    if [ ! -d "vector_db/chroma" ] || [ ! "$(ls -A vector_db/chroma 2>/dev/null)" ]; then
        echo "  • Run notebook 3 to create ChromaDB"
    fi
    echo ""
    echo "After completing these steps, run this script again."
fi

echo ""
echo "📖 For detailed instructions, see README.md"
echo ""