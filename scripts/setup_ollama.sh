#!/bin/bash
# Ollama installation and model download script
# Supports macOS and Linux systems

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

echo_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Detect operating system
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Check if Ollama is installed
check_ollama() {
    if command -v ollama &> /dev/null; then
        echo_info "Ollama is already installed"
        ollama --version
        return 0
    else
        echo_warn "Ollama is not installed"
        return 1
    fi
}

# Install Ollama
install_ollama() {
    local os=$(detect_os)

    echo_info "Detected operating system: $os"

    if [[ "$os" == "macos" ]]; then
        echo_info "Installing Ollama on macOS..."
        echo_info "Downloading installer..."
        curl -fsSL https://ollama.com/install.sh | sh
    elif [[ "$os" == "linux" ]]; then
        echo_info "Installing Ollama on Linux..."
        curl -fsSL https://ollama.com/install.sh | sh
    else
        echo_error "Unsupported operating system: $OSTYPE"
        echo_info "Please visit https://ollama.com/download to manually download and install"
        exit 1
    fi

    echo_info "Ollama installation complete"
}

# Start Ollama service
start_ollama_service() {
    echo_info "Checking Ollama service status..."

    # Try to connect to Ollama API
    if curl -s http://localhost:11434/api/tags &> /dev/null; then
        echo_info "Ollama service is already running"
        return 0
    fi

    echo_info "Starting Ollama service..."
    local os=$(detect_os)

    if [[ "$os" == "macos" ]]; then
        # On macOS, Ollama usually runs as an application
        open -a Ollama 2>/dev/null || {
            echo_warn "Unable to start Ollama app, please start it manually"
            echo_info "Or run in terminal: ollama serve"
        }
    else
        # On Linux, use systemd or manual start
        if systemctl is-active --quiet ollama; then
            echo_info "Ollama systemd service is already running"
        else
            echo_info "Attempting to start Ollama service..."
            ollama serve &>/dev/null &
            sleep 3
        fi
    fi

    # Wait for service to start
    echo_info "Waiting for Ollama service to be ready..."
    for i in {1..10}; do
        if curl -s http://localhost:11434/api/tags &> /dev/null; then
            echo_info "Ollama service is ready"
            return 0
        fi
        sleep 1
    done

    echo_error "Ollama service failed to start, please check"
    return 1
}

# Download recommended vision models
download_models() {
    echo_info "========================================="
    echo_info "Recommended vision models list:"
    echo_info "========================================="
    echo_info "1. qwen3-vl:4b     - Qwen2-VL 4B (recommended, balanced performance)"
    echo_info "2. llava-v1.6:7b   - LLaVA 1.6 7B (high quality)"
    echo_info "3. llava-v1.6:13b  - LLaVA 1.6 13B (highest quality, requires more resources)"
    echo_info "4. minicpm-v:8b    - MiniCPM-V 8B (Chinese optimized)"
    echo_info "========================================="

    echo ""
    read -p "Please select model to download (1-4, or 'all' to download all, 'skip' to skip): " choice

    case $choice in
        1)
            download_single_model "qwen3-vl:4b"
            ;;
        2)
            download_single_model "llava-v1.6:7b"
            ;;
        3)
            download_single_model "llava-v1.6:13b"
            ;;
        4)
            download_single_model "minicpm-v:8b"
            ;;
        all)
            download_single_model "qwen3-vl:4b"
            download_single_model "llava-v1.6:7b"
            download_single_model "minicpm-v:8b"
            ;;
        skip)
            echo_info "Skipping model download"
            ;;
        *)
            echo_error "Invalid selection"
            ;;
    esac
}

# Download a single model
download_single_model() {
    local model=$1
    echo_info "========================================="
    echo_info "Downloading model: $model"
    echo_info "========================================="

    if ollama list | grep -q "^${model%:*}"; then
        echo_warn "Model $model already exists, skipping download"
        return 0
    fi

    echo_info "Starting download, this may take several minutes..."
    if ollama pull "$model"; then
        echo_info "Model $model downloaded successfully"
    else
        echo_error "Model $model download failed"
        return 1
    fi
}

# Test models
test_model() {
    echo_info "========================================="
    echo_info "Testing installed models"
    echo_info "========================================="

    echo_info "List of installed models:"
    ollama list

    echo ""
    echo_info "Testing complete! You can now run image tagging with the following command:"
    echo_info "  python src/main.py --image-path /path/to/images --model qwen3-vl:4b"
}

# Main function
main() {
    echo_info "========================================="
    echo_info "Ollama Installation and Configuration Script"
    echo_info "========================================="

    # Check if already installed
    if ! check_ollama; then
        read -p "Do you want to install Ollama? (y/n): " install_choice
        if [[ "$install_choice" == "y" || "$install_choice" == "Y" ]]; then
            install_ollama
        else
            echo_info "Skipping Ollama installation"
            exit 0
        fi
    fi

    # Start service
    start_ollama_service || {
        echo_error "Ollama service failed to start, please start it manually and try again"
        exit 1
    }

    # Download models
    download_models

    # Test
    test_model

    echo_info "========================================="
    echo_info "Setup complete!"
    echo_info "========================================="
}

# Run main function
main
