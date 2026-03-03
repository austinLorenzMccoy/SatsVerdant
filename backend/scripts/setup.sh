#!/bin/bash

# SatsVerdant Backend Setup Script
# This script sets up the Supabase backend for SatsVerdant

set -e

echo "🌱 Setting up SatsVerdant Backend..."

# Check if Supabase CLI is installed
if ! command -v supabase &> /dev/null; then
    echo "❌ Supabase CLI not found. Please install it first:"
    echo "   macOS: brew install supabase/tap/supabase"
    echo "   Linux: curl -L https://github.com/supabase/cli/releases/latest/download/supabase_linux_amd64.tar.gz | tar xz"
    echo "   Windows: scoop install supabase"
    exit 1
fi

# Check if user is logged in to Supabase
if ! supabase projects list &> /dev/null; then
    echo "🔐 Please login to Supabase first:"
    echo "   supabase login"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f "supabase/functions/.env.local" ]; then
    echo "📝 Creating environment file..."
    cp supabase/functions/.env.example supabase/functions/.env.local
    echo "⚠️  Please edit supabase/functions/.env.local with your actual API keys"
fi

# Initialize Supabase project if not already done
if [ ! -f "supabase/config.toml" ]; then
    echo "🚀 Initializing Supabase project..."
    supabase init
fi

# Start local Supabase
echo "🔄 Starting local Supabase..."
supabase start

# Wait for Supabase to be ready
echo "⏳ Waiting for Supabase to be ready..."
sleep 10

# Run database migrations
echo "🗄️ Running database migrations..."
supabase db reset

# Seed the database
echo "🌱 Seeding database with sample data..."
supabase db seed

# Deploy Edge Functions locally
echo "⚡ Deploying Edge Functions locally..."
supabase functions serve --env-file supabase/functions/.env.local

echo "✅ Backend setup complete!"
echo ""
echo "🌐 Local Supabase URLs:"
echo "   Studio: $(supabase status | grep 'API URL' | awk '{print $3}')"
echo "   DB URL: $(supabase status | grep 'DB URL' | awk '{print $3}')"
echo "   Edge Functions: http://localhost:54321/functions/v1/"
echo ""
echo "📚 Next steps:"
echo "   1. Edit supabase/functions/.env.local with your API keys"
echo "   2. Test the classify function: curl -X POST http://localhost:54321/functions/v1/classify"
echo "   3. Visit the Studio to explore the database"
echo ""
echo "🔧 Useful commands:"
echo "   supabase status     - Check local status"
echo "   supabase db reset   - Reset database"
echo "   supabase logs       - View logs"
echo "   supabase stop       - Stop local services"
