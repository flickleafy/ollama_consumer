#!/bin/bash

# Ollama Service Manager Installation Script
# This script installs the Ollama Service Manager on your system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check if we're on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This script is designed for Linux systems only."
        exit 1
    fi
    
    # Check if systemd is available
    if ! command_exists systemctl; then
        print_error "systemd is required but not found."
        exit 1
    fi
    
    # Check if Ollama service exists
    if ! systemctl list-unit-files | grep -q "ollama.service"; then
        print_warning "Ollama service not found. Please ensure Ollama is installed."
        print_status "You can install Ollama with: curl -fsSL https://ollama.ai/install.sh | sh"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
    
    # Check for optional dependencies
    if ! command_exists zenity; then
        print_warning "zenity not found. GUI features will be limited."
        print_status "Install with: sudo apt install zenity (Ubuntu/Debian) or sudo dnf install zenity (Fedora)"
    fi
    
    if ! command_exists notify-send; then
        print_warning "notify-send not found. Desktop notifications will be disabled."
        print_status "Install with: sudo apt install libnotify-bin (Ubuntu/Debian)"
    fi
    
    if ! command_exists pkexec; then
        print_warning "pkexec not found. GUI privilege escalation may not work properly."
        print_status "Install with: sudo apt install policykit-1 (Ubuntu/Debian) or sudo dnf install polkit (Fedora)"
        print_status "Note: The script will fall back to sudo, but may require terminal access."
    fi
    
    print_success "Prerequisites check completed."
}

# Function to install files
install_files() {
    print_status "Installing Ollama Service Manager..."
    
    # Create Scripts directory
    SCRIPTS_DIR="$HOME/Scripts"
    mkdir -p "$SCRIPTS_DIR"
    print_status "Created directory: $SCRIPTS_DIR"
    
    # Copy and make executable the main script
    cp "ollama-toggle.py" "$SCRIPTS_DIR/"
    chmod +x "$SCRIPTS_DIR/ollama-toggle.py"
    print_success "Installed script to: $SCRIPTS_DIR/ollama-toggle.py"
    
    # Update desktop entry with correct user path
    sed "s|/home/xxx|$HOME|g" "ollama-manager.desktop" > "/tmp/ollama-manager.desktop"
    
    # Install desktop entry to desktop
    cp "/tmp/ollama-manager.desktop" "$HOME/Desktop/"
    chmod +x "$HOME/Desktop/ollama-manager.desktop"
    print_success "Installed desktop icon to: $HOME/Desktop/ollama-manager.desktop"
    
    # Install to applications menu
    mkdir -p "$HOME/.local/share/applications"
    cp "/tmp/ollama-manager.desktop" "$HOME/.local/share/applications/"
    print_success "Installed to applications menu: $HOME/.local/share/applications/"
    
    # Update desktop database
    if command_exists update-desktop-database; then
        update-desktop-database "$HOME/.local/share/applications/" 2>/dev/null || true
        print_success "Updated desktop database"
    fi
    
    # Clean up
    rm -f "/tmp/ollama-manager.desktop"
}

# Function to test installation
test_installation() {
    print_status "Testing installation..."
    
    # Test script execution
    if [[ -x "$HOME/Scripts/ollama-toggle.py" ]]; then
        print_success "Script is executable"
    else
        print_error "Script is not executable"
        return 1
    fi
    
    # Test desktop file
    if command_exists desktop-file-validate; then
        if desktop-file-validate "$HOME/.local/share/applications/ollama-manager.desktop" 2>/dev/null; then
            print_success "Desktop entry is valid"
        else
            print_warning "Desktop entry validation failed"
        fi
    fi
    
    print_success "Installation test completed"
}

# Main installation function
main() {
    echo "========================================"
    echo "  Ollama Service Manager Installation"
    echo "========================================"
    echo
    
    # Check if we're in the right directory
    if [[ ! -f "ollama-toggle.py" ]] || [[ ! -f "ollama-manager.desktop" ]]; then
        print_error "Required files not found. Please run this script from the ollama_toggle directory."
        exit 1
    fi
    
    check_prerequisites
    echo
    install_files
    echo
    test_installation
    echo
    
    print_success "Installation completed successfully!"
    echo
    print_status "You can now:"
    echo "  • Double-click the desktop icon 'Ollama Service Manager'"
    echo "  • Search for 'Ollama Service Manager' in your applications menu"
    echo "  • Run directly: $HOME/Scripts/ollama-toggle.py"
    echo
    print_status "If the desktop icon doesn't appear immediately, try:"
    echo "  • Refreshing your desktop (F5 or right-click → Refresh)"
    echo "  • Logging out and back in"
    echo "  • Running: killall nautilus (for GNOME)"
}

# Handle script interruption
trap 'print_error "Installation interrupted"; exit 1' INT TERM

# Run main function
main "$@"
