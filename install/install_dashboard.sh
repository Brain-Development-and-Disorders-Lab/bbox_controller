#!/bin/bash
# Behavior Box Controller - Dashboard Installation Script
# Supports: macOS (10.15+), Linux (Ubuntu 20.04+, Debian 11+)
# License: CC BY-NC-SA 4.0

set -e

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
MIN_PYTHON_VERSION="3.11"
APP_NAME="Behavior Box Dashboard"
VENV_PATH="$REPO_ROOT/venvs/dashboard"
REQUIREMENTS="$REPO_ROOT/apps/dashboard/requirements.txt"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Logging functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "\n${BOLD}==> $1${NC}"; }

# Error handler
error_exit() {
    log_error "$1"
    log_info "Installation failed. Check the errors above."
    exit 1
}

# Check Python version
check_python() {
    log_step "Checking Python installation"

    # Try python3 first, then python
    PYTHON_CMD=""
    for cmd in python3 python; do
        if command -v $cmd &> /dev/null; then
            version=$($cmd --version 2>&1 | awk '{print $2}')
            major=$(echo $version | cut -d. -f1)
            minor=$(echo $version | cut -d. -f2)

            if [ "$major" -eq 3 ] && [ "$minor" -ge 11 ]; then
                PYTHON_CMD=$cmd
                log_success "Found Python $version at $(which $cmd)"
                break
            fi
        fi
    done

    if [ -z "$PYTHON_CMD" ]; then
        error_exit "Python 3.11 or later is required. Please install from https://www.python.org/downloads/"
    fi
}

# Detect platform
detect_platform() {
    log_step "Detecting platform"

    OS_TYPE="$(uname -s)"
    case "${OS_TYPE}" in
        Darwin*)
            PLATFORM="macos"
            log_info "Platform: macOS"
            ;;
        Linux*)
            PLATFORM="linux"
            log_info "Platform: Linux"
            ;;
        *)
            error_exit "Unsupported platform: ${OS_TYPE}"
            ;;
    esac
}

# Create virtual environment
create_venv() {
    log_step "Creating virtual environment"

    if [ -d "$VENV_PATH" ]; then
        log_warn "Virtual environment already exists at $VENV_PATH"
        read -p "Remove and recreate? [y/N]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -rf "$VENV_PATH"
        else
            log_info "Using existing virtual environment"
            return
        fi
    fi

    log_info "Creating virtual environment at $VENV_PATH"
    $PYTHON_CMD -m venv "$VENV_PATH" || error_exit "Failed to create virtual environment"
    log_success "Virtual environment created"
}

# Install dependencies
install_dependencies() {
    log_step "Installing dependencies"

    # Activate virtual environment
    source "$VENV_PATH/bin/activate" || error_exit "Failed to activate virtual environment"

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip --quiet || error_exit "Failed to upgrade pip"

    # Install requirements
    log_info "Installing Python packages (this may take a few minutes)..."
    pip install -r "$REQUIREMENTS" || error_exit "Failed to install dependencies"

    log_success "All dependencies installed"
}

# Verify installation
verify_installation() {
    log_step "Verifying installation"

    source "$VENV_PATH/bin/activate"

    # Test imports
    python -c "import PyQt6" || error_exit "PyQt6 import failed"
    python -c "import websocket" || error_exit "websocket-client import failed"
    python -c "import PIL" || error_exit "Pillow import failed"

    log_success "All packages verified"
}

# Configure Qt for macOS
configure_qt_macos() {
    if [ "$PLATFORM" == "macos" ]; then
        log_step "Configuring Qt for macOS"

        # Find the actual Python version directory
        QT_PLUGINS=$(find "$VENV_PATH/lib" -type d -name "PyQt6" 2>/dev/null | head -1)
        if [ -n "$QT_PLUGINS" ]; then
            QT_PLUGINS="$QT_PLUGINS/Qt6/plugins"
            if [ -d "$QT_PLUGINS" ]; then
                log_info "Qt plugins found at $QT_PLUGINS"
                log_success "Qt configured"
            else
                log_warn "Qt plugins directory not found at expected location"
            fi
        else
            log_warn "PyQt6 installation not found, may cause issues"
        fi
    fi
}

# Create desktop shortcut (optional)
create_desktop_shortcut() {
    log_step "Desktop integration"

    read -p "Create desktop shortcut? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return
    fi

    if [ "$PLATFORM" == "macos" ]; then
        # macOS: Create .command file that directly calls start.sh
        LAUNCHER="$HOME/Desktop/Behavior Box Dashboard.command"
        cat > "$LAUNCHER" << EOF
#!/bin/bash
exec "$REPO_ROOT/apps/dashboard/start.sh"
EOF
        chmod +x "$LAUNCHER"
        log_success "Desktop launcher created"
    elif [ "$PLATFORM" == "linux" ]; then
        # Linux: Create .desktop file that directly calls start.sh
        DESKTOP_FILE="$HOME/.local/share/applications/behavior-box-dashboard.desktop"
        mkdir -p "$(dirname "$DESKTOP_FILE")"
        cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Type=Application
Name=Behavior Box Dashboard
Exec=$REPO_ROOT/apps/dashboard/start.sh
Icon=$REPO_ROOT/apps/dashboard/assets/icon.png
Terminal=false
Categories=Science;Education;
EOF
        chmod +x "$DESKTOP_FILE"

        # Also create desktop shortcut if ~/Desktop exists
        if [ -d "$HOME/Desktop" ]; then
            cp "$DESKTOP_FILE" "$HOME/Desktop/behavior-box-dashboard.desktop"
            chmod +x "$HOME/Desktop/behavior-box-dashboard.desktop"
            log_success "Desktop shortcut created with icon"
        else
            log_success "Application menu entry created with icon"
        fi
    fi
}

# Display success message
show_success() {
    log_step "Installation complete!"
    echo
    log_success "Behavior Box Dashboard has been installed successfully"
    echo
    echo "To start the dashboard:"
    echo "  1. Run: ./apps/dashboard/start.sh"
    echo "  2. Or double-click the desktop shortcut (if created)"
    echo
    echo "For help, see: $REPO_ROOT/install/README.md"
    echo
}

# Main installation flow
main() {
    echo
    echo "======================================"
    echo "  Behavior Box Dashboard Installer  "
    echo "======================================"
    echo

    check_python
    detect_platform
    create_venv
    install_dependencies
    verify_installation
    configure_qt_macos
    create_desktop_shortcut
    show_success
}

# Run main function
main "$@"
