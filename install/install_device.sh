#!/bin/bash
# Behavior Box Controller - Device Installation Script
# Supports: Raspberry Pi OS (Bullseye, Bookworm)
# License: CC BY-NC-SA 4.0
# NOTE: This script must be run with sudo

set -e

# Constants
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
MIN_PYTHON_VERSION="3.11"
APP_NAME="Behavior Box Device Controller"
VENV_PATH="$REPO_ROOT/venvs/device"
REQUIREMENTS="$REPO_ROOT/apps/device/requirements.txt"
SERVICE_FILE="/etc/systemd/system/bbox-device.service"

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

# Check for sudo
check_sudo() {
    log_step "Checking permissions"

    if [ "$EUID" -ne 0 ]; then
        log_error "This script must be run with sudo"
        log_info "Please run: sudo ./install_device.sh"
        exit 1
    fi

    log_success "Running with sudo privileges"
}

# Check for Raspberry Pi
check_raspberry_pi() {
    log_step "Checking hardware"

    if [ ! -f /proc/device-tree/model ]; then
        log_warn "Not running on Raspberry Pi"
        log_info "The device controller requires Raspberry Pi hardware for GPIO access"
        log_info "You can continue for testing in simulation mode"
        read -p "Continue anyway? [y/N]: " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        SIMULATION_MODE=1
    else
        MODEL=$(cat /proc/device-tree/model)
        log_info "Detected: $MODEL"
        log_success "Raspberry Pi hardware detected"
        SIMULATION_MODE=0
    fi
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
        log_error "Python 3.11 or later is required"
        log_info "Install with: sudo apt-get install python3.11 python3.11-venv"
        exit 1
    fi
}

# Install system packages
install_system_packages() {
    log_step "Installing system packages"

    log_info "Updating package lists..."
    apt-get update -qq || log_warn "apt-get update had some warnings"

    log_info "Installing required packages..."
    apt-get install -y \
        python3-venv \
        python3-dev \
        i2c-tools \
        python3-pip \
        git || error_exit "Failed to install system packages"

    log_success "System packages installed"
}

# Enable I2C
enable_i2c() {
    log_step "Configuring I2C"

    if [ $SIMULATION_MODE -eq 1 ]; then
        log_info "Skipping I2C configuration (not on Raspberry Pi)"
        return
    fi

    # Check if I2C is already enabled
    if grep -q "^dtparam=i2c_arm=on" /boot/config.txt 2>/dev/null || grep -q "^dtparam=i2c_arm=on" /boot/firmware/config.txt 2>/dev/null; then
        log_info "I2C already enabled in config"
    else
        log_info "Enabling I2C interface..."

        # Try both locations (older and newer Raspberry Pi OS)
        if [ -f /boot/config.txt ]; then
            echo "dtparam=i2c_arm=on" >> /boot/config.txt
            log_info "Added I2C config to /boot/config.txt"
        elif [ -f /boot/firmware/config.txt ]; then
            echo "dtparam=i2c_arm=on" >> /boot/firmware/config.txt
            log_info "Added I2C config to /boot/firmware/config.txt"
        else
            log_warn "Could not find config.txt to enable I2C"
        fi

        # Load module now (without reboot)
        modprobe i2c-dev 2>/dev/null || log_warn "Could not load i2c-dev module"

        log_warn "I2C enabled, but reboot recommended for full activation"
    fi

    # Check if I2C devices exist
    if [ -e /dev/i2c-1 ]; then
        log_success "I2C interface available at /dev/i2c-1"
    else
        log_warn "I2C device /dev/i2c-1 not found (reboot may be needed)"
    fi
}

# Configure GPIO permissions
configure_gpio() {
    log_step "Configuring GPIO permissions"

    if [ $SIMULATION_MODE -eq 1 ]; then
        log_info "Skipping GPIO configuration (not on Raspberry Pi)"
        return
    fi

    # Add pi user to gpio and i2c groups if they exist
    if id "pi" &>/dev/null; then
        if grep -q "^gpio:" /etc/group; then
            usermod -a -G gpio pi 2>/dev/null || true
            log_info "Added user 'pi' to gpio group"
        fi

        if grep -q "^i2c:" /etc/group; then
            usermod -a -G i2c pi 2>/dev/null || true
            log_info "Added user 'pi' to i2c group"
        fi

        log_success "User permissions configured"
    else
        log_warn "User 'pi' not found, skipping group assignment"
    fi
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

    # Fix ownership if created with sudo
    if [ -n "$SUDO_USER" ]; then
        chown -R $SUDO_USER:$SUDO_USER "$VENV_PATH"
        log_info "Set ownership to $SUDO_USER"
    fi

    log_success "Virtual environment created"
}

# Install dependencies
install_dependencies() {
    log_step "Installing Python dependencies"

    # Activate virtual environment
    source "$VENV_PATH/bin/activate" || error_exit "Failed to activate virtual environment"

    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip --quiet || error_exit "Failed to upgrade pip"

    # Install requirements (this includes platform-specific Linux packages)
    log_info "Installing Python packages (this may take 10-20 minutes on Raspberry Pi)..."
    log_info "Packages include: pygame, websockets, numpy, Pillow, and GPIO libraries"
    pip install -r "$REQUIREMENTS" || error_exit "Failed to install dependencies"

    log_success "All dependencies installed"
}

# Verify installation
verify_installation() {
    log_step "Verifying installation"

    source "$VENV_PATH/bin/activate"

    # Test imports
    python -c "import pygame" || error_exit "pygame import failed"
    python -c "import websockets" || error_exit "websockets import failed"
    python -c "import numpy" || error_exit "numpy import failed"
    python -c "import PIL" || error_exit "Pillow import failed"

    # Test GPIO imports (may fail on non-Pi)
    if [ $SIMULATION_MODE -eq 0 ]; then
        python -c "import gpiozero" 2>/dev/null || log_warn "gpiozero import failed (hardware may not be connected)"
    fi

    log_success "Core packages verified"
}

# Verify hardware
verify_hardware() {
    log_step "Verifying hardware"

    if [ $SIMULATION_MODE -eq 1 ]; then
        log_info "Skipping hardware verification (simulation mode)"
        return
    fi

    if [ ! -e /dev/i2c-1 ]; then
        log_warn "I2C device /dev/i2c-1 not found"
        log_info "You may need to reboot for I2C to be fully enabled"
        return
    fi

    log_info "Scanning I2C bus..."
    i2cdetect -y 1 | tee /tmp/i2c_scan.txt

    # Check for common display addresses
    if grep -q "3c" /tmp/i2c_scan.txt || grep -q "3d" /tmp/i2c_scan.txt; then
        log_success "I2C displays detected"
    else
        log_warn "Expected display devices not detected at 0x3C or 0x3D"
        log_info "This is OK if displays are not connected yet"
    fi
}

# Create launcher
create_launcher() {
    log_step "Creating launcher script"

    LAUNCHER="$REPO_ROOT/launch_device.sh"

    cat > "$LAUNCHER" << 'EOF'
#!/bin/bash
# Auto-generated launcher for Behavior Box Device Controller

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venvs/device"

# Check for sudo
if [ "$EUID" -ne 0 ]; then
    echo "Error: Must run with sudo for GPIO access"
    echo "Usage: sudo ./launch_device.sh [--port PORT]"
    exit 1
fi

# Check virtual environment
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please run: sudo install/install_device.sh"
    exit 1
fi

source "$VENV_PATH/bin/activate"
cd "$SCRIPT_DIR/apps/device"
./start.sh "$@"
EOF

    chmod +x "$LAUNCHER"

    # Fix ownership if created with sudo
    if [ -n "$SUDO_USER" ]; then
        chown $SUDO_USER:$SUDO_USER "$LAUNCHER"
    fi

    log_success "Launcher created at $LAUNCHER"
}

# Configure auto-start
configure_autostart() {
    log_step "Auto-start configuration"

    read -p "Start device controller on boot? [y/N]: " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Skipping auto-start configuration"
        return
    fi

    log_info "Creating systemd service..."

    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=Behavior Box Device Controller
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$REPO_ROOT
ExecStart=$VENV_PATH/bin/python $REPO_ROOT/packages/device/main.py
Restart=always
RestartSec=10
StandardOutput=append:$REPO_ROOT/apps/device/logs/device.log
StandardError=append:$REPO_ROOT/apps/device/logs/device.log

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable bbox-device.service

    log_success "Auto-start configured"
    echo
    log_info "Service management commands:"
    log_info "  Start:   sudo systemctl start bbox-device"
    log_info "  Stop:    sudo systemctl stop bbox-device"
    log_info "  Status:  sudo systemctl status bbox-device"
    log_info "  Logs:    sudo journalctl -u bbox-device -f"
}

# Display success message
show_success() {
    log_step "Installation complete!"
    echo
    log_success "Behavior Box Device Controller has been installed successfully"
    echo

    if [ $SIMULATION_MODE -eq 1 ]; then
        log_warn "Running in SIMULATION MODE (no Raspberry Pi hardware detected)"
        echo
    fi

    echo "To start the device controller:"
    echo "  sudo ./launch_device.sh"
    echo

    if grep -q "I2C enabled, but reboot recommended" <(log_warn "test" 2>&1) 2>/dev/null; then
        log_warn "REBOOT RECOMMENDED for I2C changes to take effect"
        echo "  After reboot, run: sudo ./launch_device.sh"
        echo
    fi

    echo "For help, see: $REPO_ROOT/install/README.md"
    echo
}

# Main installation flow
main() {
    echo
    echo "======================================"
    echo "  Behavior Box Device Installer"
    echo "======================================"
    echo

    check_sudo
    check_raspberry_pi
    check_python
    install_system_packages
    enable_i2c
    configure_gpio
    create_venv
    install_dependencies
    verify_installation
    verify_hardware
    create_launcher
    configure_autostart
    show_success
}

# Run main function
main "$@"
