#!/bin/bash

# Setup script for LangFuse tracing configuration

echo "🔍 LangFuse Tracing Setup"
echo "========================"
echo ""
echo "This script will help you configure LangFuse tracing for your voice agent."
echo ""

# Check if already configured
if lk agent secrets | grep -q "LANGFUSE_PUBLIC_KEY"; then
    echo "✅ LangFuse is already configured!"
    echo ""
    read -p "Do you want to update the configuration? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 0
    fi
fi

echo "📝 Please provide your LangFuse credentials:"
echo "(Get these from https://cloud.langfuse.com → Settings → API Keys)"
echo ""

# Get public key
read -p "Enter your LANGFUSE_PUBLIC_KEY: " PUBLIC_KEY
if [ -z "$PUBLIC_KEY" ]; then
    echo "❌ Public key cannot be empty"
    exit 1
fi

# Get secret key
read -p "Enter your LANGFUSE_SECRET_KEY: " SECRET_KEY
if [ -z "$SECRET_KEY" ]; then
    echo "❌ Secret key cannot be empty"
    exit 1
fi

# Optional: Custom host (for self-hosted)
read -p "Enter LANGFUSE_HOST (press Enter for cloud.langfuse.com): " HOST
if [ -z "$HOST" ]; then
    HOST="https://cloud.langfuse.com"
fi

echo ""
echo "🔧 Configuring LiveKit Cloud secrets..."

# Update secrets in LiveKit Cloud
lk agent update-secrets \
  --secrets "LANGFUSE_PUBLIC_KEY=$PUBLIC_KEY" \
  --secrets "LANGFUSE_SECRET_KEY=$SECRET_KEY" \
  --secrets "LANGFUSE_HOST=$HOST"

if [ $? -eq 0 ]; then
    echo "✅ Secrets updated successfully!"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Deploy your agent: lk agent deploy"
    echo "2. Restart the agent: lk agent restart"
    echo "3. Test with a session: lk agent proxy console"
    echo "4. View traces at: $HOST"
    echo ""
    echo "📊 Your LangFuse dashboard URL:"
    # Extract project ID from public key (usually format: pk_xxx_yyy)
    PROJECT_ID=$(echo $PUBLIC_KEY | cut -d'_' -f2)
    echo "$HOST/project/$PROJECT_ID"
else
    echo "❌ Failed to update secrets. Please check your LiveKit CLI configuration."
    exit 1
fi