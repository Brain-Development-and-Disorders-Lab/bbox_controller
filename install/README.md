# Behavior Box Controller - Installation Guide

This guide covers installation of the Behavior Box Controller software on all supported platforms.

## Overview

Run the installer to configure the Python environment and install dependencies. The installer creates a launcher script at the repository root.

## Table of Contents

- [Dashboard Installation](#dashboard-installation)
  - [macOS](#macos)
  - [Windows](#windows)
  - [Linux](#linux)
- [Device Installation (Raspberry Pi)](#device-installation-raspberry-pi)
- [Troubleshooting](#troubleshooting)
- [For Developers](#for-developers)

## System Requirements

### Dashboard

- **Operating System**: macOS 10.15+, Windows 10/11, or Linux (Ubuntu 20.04+, Debian 11+)
- **Python**: 3.11 or later
- **RAM**: 4GB minimum
- **Disk Space**: ~500MB for installation

### Device Controller

- **Hardware**: Raspberry Pi 3, 4, or 5
- **Operating System**: Raspberry Pi OS (Bullseye or Bookworm)
- **Python**: 3.11 or later
- **RAM**: 1GB minimum
- **Disk Space**: ~2GB for installation
- **Peripherals**: GPIO-connected hardware, I2C displays (optional)

## Dashboard Installation

The dashboard is the desktop application used to monitor and control experiments.

### macOS

1. **Install Python 3.11+** (if not already installed)

   ```bash
   # Download from https://www.python.org/downloads/
   # Or use Homebrew:
   brew install python@3.11
   ```

2. **Clone or download the repository**

   ```bash
   git clone <repository-url>
   cd bbox_controller
   ```

3. **Run the installer**

   ```bash
   ./install/install_dashboard.sh
   ```

4. **Launch the dashboard**

   ```bash
   ./apps/dashboard/start.sh
   ```

   Or double-click the desktop shortcut if you created one during installation.

**Troubleshooting macOS:**

- If you get a "Permission denied" error, make sure the script is executable: `chmod +x install/install_dashboard.sh`
- If macOS Gatekeeper blocks the script, right-click the script and select "Open" or run via Terminal
- For Qt plugin issues, the installer automatically configures the plugin path

### Windows

1. **Install Python 3.11+** (if not already installed)
   - Download from [python.org/downloads](https://www.python.org/downloads/)
   - **Important**: Check "Add Python to PATH" during installation

2. **Download and extract the repository**
   - Download the ZIP from GitHub or clone with Git
   - Extract to a location like `C:\BehaviorBox\`

3. **Run the installer**
   - Double-click `install\install_dashboard.bat`
   - Or from Command Prompt:

     ```cmd
     cd C:\path\to\bbox_controller
     install\install_dashboard.bat
     ```

4. **Launch the dashboard**
   - Double-click `launch_dashboard.bat`
   - Or use the desktop shortcut if you created one

**Troubleshooting Windows:**

- If Python is not found, verify installation with: `py --version`
- If you see "Scripts are disabled", you may need to enable script execution or use the .bat file instead of .ps1
- Windows Defender may scan the installer - this is normal and safe

### Linux

1. **Install Python 3.11+** (if not already installed)

   ```bash
   # Ubuntu/Debian
   sudo apt-get update
   sudo apt-get install python3.11 python3.11-venv python3-pip

   # Fedora
   sudo dnf install python3.11
   ```

2. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd bbox_controller
   ```

3. **Run the installer**

   ```bash
   ./install/install_dashboard.sh
   ```

4. **Launch the dashboard**

   ```bash
   ./apps/dashboard/start.sh
   ```

**Troubleshooting Linux:**

- If you get Qt platform plugin errors, install: `sudo apt-get install libxcb-xinerama0`
- For display issues, ensure X11 or Wayland is properly configured

## Device Installation (Raspberry Pi)

The device controller runs on a Raspberry Pi and manages the behavior box hardware.

### Prerequisites

- Raspberry Pi 3, 4, or 5 with Raspberry Pi OS installed
- SD card with at least 8GB (16GB recommended)
- Internet connection (for initial setup)
- SSH access or keyboard/monitor connected

### Installation Steps

1. **Update system packages**

   ```bash
   sudo apt-get update
   sudo apt-get upgrade
   ```

2. **Install Git** (if not already installed)

   ```bash
   sudo apt-get install git
   ```

3. **Clone the repository**

   ```bash
   cd ~
   git clone <repository-url>
   cd bbox_controller
   ```

4. **Run the device installer** (requires sudo)

   ```bash
   sudo ./install/install_device.sh
   ```

   The installer will:
   - Check for Python 3.11+
   - Install system dependencies (I2C tools, etc.)
   - Enable the I2C interface
   - Configure GPIO permissions
   - Create a virtual environment
   - Install Python packages (may take 10-20 minutes)
   - Verify hardware connections
   - Optionally set up auto-start on boot

5. **Reboot the Raspberry Pi** (if I2C was newly enabled)

   ```bash
   sudo reboot
   ```

6. **Launch the device controller**

   ```bash
   sudo ./launch_device.sh
   ```

### Auto-Start Configuration

If you enabled auto-start during installation, the device controller will start automatically on boot. Manage it with:

```bash
# Start the service
sudo systemctl start bbox-device

# Stop the service
sudo systemctl stop bbox-device

# Check status
sudo systemctl status bbox-device

# View logs
sudo journalctl -u bbox-device -f

# Disable auto-start
sudo systemctl disable bbox-device
```

### Hardware Verification

After installation, verify your hardware connections:

```bash
# Check I2C devices
sudo i2cdetect -y 1

# Should show displays at addresses 0x3C and 0x3D
```

## Troubleshooting

### Common Issues

#### "Python 3.11 or later is required"

**Solution**: Install Python 3.11+ from python.org or your package manager.

```bash
# macOS with Homebrew
brew install python@3.11

# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-venv

# Windows
# Download installer from python.org
```

#### "Virtual environment not found"

**Solution**: Run the installer first:

```bash
# Dashboard
./install/install_dashboard.sh

# Device
sudo ./install/install_device.sh
```

#### Qt Plugin Errors (macOS)

**Solution**: The start script configures this automatically. If issues persist, verify your PyQt6 installation:

```bash
source venvs/dashboard/bin/activate
python -c "import PyQt6.QtCore; print('PyQt6 OK')"
```

#### I2C Not Detected (Raspberry Pi)

**Solution**:

1. Verify I2C is enabled: Check `/boot/config.txt` for `dtparam=i2c_arm=on`
2. Reboot after enabling I2C
3. Check connections: `sudo i2cdetect -y 1`
4. Verify hardware connections

#### Permission Denied (Raspberry Pi GPIO)

**Solution**: The device controller requires sudo for GPIO access:

```bash
sudo ./launch_device.sh
```

If using systemd service, it runs as root automatically.

#### "Failed to install dependencies"

**Possible causes**:

- No internet connection
- Firewall blocking PyPI
- Disk space full

**Solution**:

1. Check internet connection
2. Free up disk space: `df -h`
3. Retry installation
4. For offline installation, see [Developer Documentation](#for-developers)

### Getting Help

If you encounter issues not covered here:

1. Check the log files:
   - Dashboard: `apps/dashboard/logs/dashboard.log`
   - Device: `apps/device/logs/device.log`

2. Verify your Python version:

   ```bash
   python3 --version  # Should be 3.11 or later
   ```

3. Check virtual environment activation:

   ```bash
   source venvs/dashboard/bin/activate  # macOS/Linux
   venvs\dashboard\Scripts\activate.bat  # Windows
   python -c "import sys; print(sys.prefix)"
   ```

## For Developers

### Manual Installation

If you prefer to set up the environment manually:

```bash
# Create virtual environment
python3.11 -m venv venvs/dashboard  # or venvs/device

# Activate it
source venvs/dashboard/bin/activate  # macOS/Linux
venvs\dashboard\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r apps/dashboard/requirements.txt  # or apps/device/requirements.txt
```

### Development Mode

For development, you can run directly:

```bash
# Dashboard
source venvs/dashboard/bin/activate
cd packages
PYTHONPATH=$(pwd) python dashboard/main.py

# Device (on Raspberry Pi)
source venvs/device/bin/activate
cd packages
sudo PYTHONPATH=$(pwd) python device/main.py --port 8765
```

### Using Existing Virtual Environments

If you have virtual environments at different locations, modify `apps/dashboard/start.sh` or `apps/device/start.sh` to point to your venv path.

### Offline Installation

To install without internet access:

1. Download all wheel files on a machine with internet:

   ```bash
   pip download -r apps/dashboard/requirements.txt -d wheels/
   ```

2. Transfer the `wheels/` directory to the target machine

3. Install from local wheels:

   ```bash
   pip install --no-index --find-links wheels/ -r apps/dashboard/requirements.txt
   ```

### Updating the Software

To update to a new version:

```bash
# Pull latest changes
git pull

# Re-run the installer to update dependencies
./install/install_dashboard.sh  # or install_device.sh
```

## Platform-Specific Notes

### macOS Platforms

- The dashboard works on macOS 10.15 (Catalina) and later
- Apple Silicon (M1/M2/M3) is fully supported
- Qt plugins are automatically configured by the installer

### Windows Platforms

- Works on Windows 10 and Windows 11
- Git Bash or WSL can be used for bash scripts
- The batch (.bat) scripts work in Command Prompt and PowerShell

### Raspberry Pi

- Tested on Raspberry Pi 5
- Raspberry Pi Zero/Zero 2 W may work but performance will be limited
- Raspberry Pi OS Lite (no desktop) is recommended for device controllers
- SSH access is recommended for headless setup

## Next Steps

After installation:

1. **Start the dashboard**: Run `./apps/dashboard/start.sh` or use the desktop shortcut
2. **Start the device**: Run `sudo ./launch_device.sh` on the Raspberry Pi
3. **Connect**: Use the dashboard to connect to your device
4. **Run experiments**: Create and monitor experiments through the dashboard

For additional documentation, see the main [README.md](../README.md).
