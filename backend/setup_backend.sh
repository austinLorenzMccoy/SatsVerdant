#!/bin/bash
# Setup SatsVerdant Backend with Poetry

set -e

echo "🚀 SatsVerdant Backend Setup"
echo "===================================="

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "📦 Poetry not found. Installing Poetry..."
    curl -sSL https://install.python-poetry.org | python3 -
    echo ""
    echo "⚠️  Please restart your terminal or run:"
    echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
    echo ""
    echo "Then run this script again."
    exit 1
fi

echo "✅ Poetry found: $(poetry --version)"
echo ""

# Configure Poetry to create venv in project directory
echo "⚙️  Configuring Poetry..."
poetry config virtualenvs.in-project true

# Install dependencies
echo "📦 Installing dependencies..."
poetry install

echo ""
echo "===================================="
echo "✅ Backend Setup Complete!"
echo "===================================="
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Activate virtual environment:"
echo "   poetry shell"
echo ""
echo "2. Copy environment file:"
echo "   cp .env.example .env"
echo "   # Edit .env with your configuration"
echo ""
echo "3. Initialize database:"
echo "   poetry run alembic upgrade head"
echo ""
echo "4. Run development server:"
echo "   poetry run uvicorn app.main:app --reload"
echo ""
echo "5. Run tests:"
echo "   poetry run pytest"
echo ""
echo "📚 Useful commands:"
echo "   poetry add <package>        # Add new dependency"
echo "   poetry add -D <package>     # Add dev dependency"
echo "   poetry update               # Update dependencies"
echo "   poetry show                 # List installed packages"
echo "   poetry export -f requirements.txt --output requirements.txt --without-hashes"
echo "                               # Export to requirements.txt"
echo ""
