#!/bin/bash

# VexaAI RAG Chat PDF - Setup Script
# Developed by: John Evans Okyere
# This script automates the installation and setup process

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${PURPLE}================================${NC}"
    echo -e "${PURPLE}$1${NC}"
    echo -e "${PURPLE}================================${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python_version() {
    if command_exists python3; then
        python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
        python_major=$(echo $python_version | cut -d'.' -f1)
        python_minor=$(echo $python_version | cut -d'.' -f2)
        
        if [ "$python_major" -eq 3 ] && [ "$python_minor" -ge 8 ]; then
            print_success "Python $python_version detected"
            return 0
        else
            print_error "Python 3.8+ required, found $python_version"
            return 1
        fi
    else
        print_error "Python 3 not found"
        return 1
    fi
}

# Function to create virtual environment
create_virtual_env() {
    print_status "Creating virtual environment..."
    
    if [ -d "venv" ]; then
        print_warning "Virtual environment already exists"
        read -p "Do you want to recreate it? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf venv
        else
            return 0
        fi
    fi
    
    python3 -m venv venv
    print_success "Virtual environment created"
}

# Function to activate virtual environment
activate_virtual_env() {
    print_status "Activating virtual environment..."
    
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_success "Virtual environment activated"
    else
        print_error "Could not find virtual environment activation script"
        return 1
    fi
}

# Function to install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    if [ -f "requirements.txt" ]; then
        pip install --upgrade pip
        pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        return 1
    fi
}

# Function to check Ollama installation
check_ollama() {
    print_status "Checking Ollama installation..."
    
    if command_exists ollama; then
        print_success "Ollama is installed"
        return 0
    else
        print_warning "Ollama not found"
        return 1
    fi
}

# Function to install Ollama
install_ollama() {
    print_status "Installing Ollama..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command_exists brew; then
            brew install ollama
        else
            print_status "Downloading Ollama installer for macOS..."
            curl -fsSL https://ollama.ai/install.sh | sh
        fi
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_status "Downloading Ollama installer for Linux..."
        curl -fsSL https://ollama.ai/install.sh | sh
    else
        print_warning "Please install Ollama manually from https://ollama.ai"
        return 1
    fi
    
    print_success "Ollama installed"
}

# Function to start Ollama service
start_ollama() {
    print_status "Starting Ollama service..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS - Ollama runs as a service
        ollama serve &
        sleep 2
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux - may need to start as service
        if command_exists systemctl; then
            sudo systemctl start ollama || ollama serve &
        else
            ollama serve &
        fi
        sleep 2
    fi
}

# Function to pull required models
pull_models() {
    print_status "Pulling required AI models..."
    
    # Check if Ollama is running
    if ! curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_warning "Ollama service not running, attempting to start..."
        start_ollama
        sleep 5
    fi
    
    # Pull the main model
    print_status "Pulling DeepSeek-R1 model (this may take a while)..."
    ollama pull deepseek-r1:14b
    
    print_success "Models pulled successfully"
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    directories=("data/pdfs" "logs" "cache" "exports" "temp" "backups")
    
    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
        # Create .gitkeep files for empty directories
        if [ ! -f "$dir/.gitkeep" ] && [ "$dir" != "temp" ]; then
            touch "$dir/.gitkeep"
        fi
    done
    
    print_success "Directories created"
}

# Function to setup environment file
setup_environment() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Environment file created from template"
            print_warning "Please review and customize .env file as needed"
        else
            print_warning "No .env.example found, creating basic .env file"
            cat > .env << EOF
# VexaAI RAG Chat PDF Configuration
MODEL_NAME=deepseek-r1:14b
EMBEDDING_MODEL=deepseek-r1:14b
OLLAMA_BASE_URL=http://localhost:11434
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
SIMILARITY_SEARCH_K=5
MAX_FILE_SIZE_MB=50
TEMPERATURE=0.1
LOG_LEVEL=INFO
EOF
            print_success "Basic .env file created"
        fi
    else
        print_warning ".env file already exists, skipping"
    fi
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test Python imports
    python3 -c "
import streamlit as st
import langchain
import langchain_ollama
print('✓ Python dependencies OK')
"
    
    # Test Ollama connection
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        print_success "✓ Ollama service OK"
    else
        print_warning "✗ Ollama service not accessible"
    fi
    
    # Test model availability
    if ollama list | grep -q "deepseek-r1:14b"; then
        print_success "✓ Required model available"
    else
        print_warning "✗ Required model not found"
    fi
}

# Function to display final instructions
show_final_instructions() {
    print_header "INSTALLATION COMPLETE"
    
    echo -e "${GREEN}VexaAI RAG Chat PDF has been successfully set up!${NC}"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Activate virtual environment:"
    echo "   source venv/bin/activate    # Linux/macOS"
    echo "   # or"
    echo "   venv\\Scripts\\activate       # Windows"
    echo
    echo "2. Start the application:"
    echo "   streamlit run main.py"
    echo
    echo "3. Open your browser to:"
    echo "   http://localhost:8501"
    echo
    echo -e "${YELLOW}Configuration:${NC}"
    echo "- Edit .env file to customize settings"
    echo "- Check logs/ directory for application logs"
    echo "- Upload PDFs to data/pdfs/ if needed"
    echo
    echo -e "${YELLOW}Troubleshooting:${NC}"
    echo "- Ensure Ollama service is running: ollama serve"
    echo "- Check model availability: ollama list"
    echo "- Review logs for any errors"
    echo
    echo -e "${GREEN}Happy chatting with your PDFs! 🤖📄${NC}"
}

# Main installation function
main() {
    print_header "VexaAI RAG Chat PDF Setup"
    echo -e "${BLUE}Developed by: John Evans Okyere${NC}"
    echo
    
    # Check system requirements
    print_header "CHECKING SYSTEM REQUIREMENTS"
    
    if ! check_python_version; then
        print_error "Please install Python 3.8 or higher"
        exit 1
    fi
    
    # Setup Python environment
    print_header "SETTING UP PYTHON ENVIRONMENT"
    
    create_virtual_env
    activate_virtual_env
    install_dependencies
    
    # Setup Ollama
    print_header "SETTING UP OLLAMA"
    
    if ! check_ollama; then
        print_warning "Ollama not found. Attempting to install..."
        if ! install_ollama; then
            print_error "Failed to install Ollama automatically"
            print_warning "Please install Ollama manually from https://ollama.ai"
            print_warning "Then run this script again or continue manually"
            exit 1
        fi
    fi
    
    start_ollama
    pull_models
    
    # Setup application
    print_header "SETTING UP APPLICATION"
    
    create_directories
    setup_environment
    
    # Test everything
    print_header "TESTING INSTALLATION"
    
    test_installation
    
    # Show final instructions
    show_final_instructions
}

# Check if running with bash
if [ -z "$BASH_VERSION" ]; then
    echo "This script requires bash. Please run with: bash setup.sh"
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "main.py" ]; then
    print_error "main.py not found. Please run this script from the VexaAI project directory"
    exit 1
fi

# Run main installation
main "$@"