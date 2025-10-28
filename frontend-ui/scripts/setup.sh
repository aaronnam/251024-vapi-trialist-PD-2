#!/bin/bash

# PandaDoc Voice Agent Frontend Setup Script
# This script automates the initial setup of the voice agent frontend

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1"
}

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# Check prerequisites
print_header "Checking Prerequisites"

# Check Node.js version
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 18 ]; then
    print_error "Node.js version 18+ is required. Current version: $(node -v)"
    exit 1
fi
print_status "Node.js $(node -v) found"

# Check npm/pnpm
if command -v pnpm &> /dev/null; then
    PKG_MANAGER="pnpm"
    print_status "Using pnpm"
elif command -v npm &> /dev/null; then
    PKG_MANAGER="npm"
    print_status "Using npm"
else
    print_error "No package manager found. Please install npm or pnpm."
    exit 1
fi

# Check git
if ! command -v git &> /dev/null; then
    print_error "Git is not installed. Please install git first."
    exit 1
fi
print_status "Git found"

# Check LiveKit CLI (optional but recommended)
if command -v lk &> /dev/null; then
    print_status "LiveKit CLI found"
    HAS_LK_CLI=true
else
    print_warning "LiveKit CLI not found. You'll need to manually configure credentials."
    HAS_LK_CLI=false
fi

# Clone the starter template
print_header "Setting Up Project"

if [ -d "pandadoc-voice-ui" ]; then
    print_warning "Directory 'pandadoc-voice-ui' already exists."
    read -p "Do you want to remove it and start fresh? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf pandadoc-voice-ui
        print_status "Removed existing directory"
    else
        print_error "Setup cancelled. Please remove or rename the existing directory."
        exit 1
    fi
fi

print_status "Cloning agent-starter-react template..."
git clone https://github.com/livekit-examples/agent-starter-react.git pandadoc-voice-ui
cd pandadoc-voice-ui

# Install dependencies
print_header "Installing Dependencies"
print_status "Installing packages with $PKG_MANAGER..."
$PKG_MANAGER install

# Copy configuration templates
print_header "Setting Up Configuration"

# Copy app config
if [ -f "../config/app-config.template.ts" ]; then
    cp ../config/app-config.template.ts app-config.ts
    print_status "Copied app configuration template"
else
    print_warning "app-config.template.ts not found. Using default configuration."
fi

# Setup environment variables
if [ -f "../config/.env.template" ]; then
    cp ../config/.env.template .env.local
    print_status "Created .env.local from template"
else
    print_warning ".env.template not found. Creating basic .env.local"
    cat > .env.local << EOF
LIVEKIT_URL=
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
AGENT_NAME=pd-voice-trialist-2-agent
EOF
fi

# Get LiveKit credentials if CLI is available
if [ "$HAS_LK_CLI" = true ]; then
    print_header "LiveKit Configuration"
    read -p "Do you want to configure LiveKit credentials now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Authenticating with LiveKit Cloud..."
        lk cloud auth

        print_status "Getting environment variables..."
        lk app env -w -d .env.local

        print_status "LiveKit credentials configured"
    else
        print_warning "Skipping LiveKit configuration. Remember to add credentials to .env.local"
    fi
else
    print_warning "Please add your LiveKit credentials to .env.local manually:"
    echo "  LIVEKIT_URL=your-livekit-url"
    echo "  LIVEKIT_API_KEY=your-api-key"
    echo "  LIVEKIT_API_SECRET=your-api-secret"
fi

# Add PandaDoc branding assets
print_header "Setting Up Branding"

mkdir -p public/logos
print_status "Created public/logos directory"

# Copy PandaDoc logos from frontend-ui/logos
if [ -d "../logos" ]; then
    cp ../logos/Emerald_black_pd_brandmark.png public/logos/
    cp ../logos/Emerald_white_pd_symbol_brandmark.png public/logos/
    cp ../logos/panda-logo-2.png public/logos/
    print_status "Copied PandaDoc logo assets"
else
    print_warning "Logo files not found in ../logos/ - you'll need to add them manually"
fi

# Create additional helper scripts
print_header "Creating Helper Scripts"

# Create run script
cat > run.sh << 'EOF'
#!/bin/bash
# Quick run script for development
echo "Starting PandaDoc Voice UI in development mode..."
npm run dev
EOF
chmod +x run.sh
print_status "Created run.sh script"

# Create build script
cat > build.sh << 'EOF'
#!/bin/bash
# Build for production
echo "Building PandaDoc Voice UI for production..."
npm run build
echo "Build complete! Run 'npm run start' to test production build."
EOF
chmod +x build.sh
print_status "Created build.sh script"

# Create deploy script
cat > deploy.sh << 'EOF'
#!/bin/bash
# Deploy to Vercel
echo "Deploying PandaDoc Voice UI to Vercel..."
if ! command -v vercel &> /dev/null; then
    echo "Installing Vercel CLI..."
    npm i -g vercel
fi
vercel --prod
EOF
chmod +x deploy.sh
print_status "Created deploy.sh script"

# Final instructions
print_header "Setup Complete!"

echo "Your PandaDoc Voice UI is ready for development!"
echo ""
echo "Next steps:"
echo "1. Navigate to the project: cd pandadoc-voice-ui"
echo "2. Configure your LiveKit credentials in .env.local"
echo "3. Update app-config.ts with your agent details"
echo "4. Replace the placeholder logo with your actual logo"
echo "5. Start development server: ./run.sh or npm run dev"
echo ""
echo "Quick commands:"
echo "  ./run.sh     - Start development server"
echo "  ./build.sh   - Build for production"
echo "  ./deploy.sh  - Deploy to Vercel"
echo ""
print_status "Setup completed successfully!"

# Optionally start the dev server
read -p "Do you want to start the development server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    print_status "Starting development server..."
    npm run dev
fi