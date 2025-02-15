# Ollama Service Manager

A convenient GUI and command-line tool for managing the Ollama AI service on Linux systems. This utility provides an easy way to start, stop, enable, disable, and monitor your Ollama service through a user-friendly desktop application.

Built with **Python** and **Zenipy** for modern, reliable service management with excellent error handling and user experience.

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Linux-green.svg)
![Language](https://img.shields.io/badge/language-python-blue.svg)
![Python](https://img.shields.io/badge/python-3.6+-brightgreen.svg)

## 🚀 Features

- **Modern Python Implementation**: Clean, well-documented Python code with type hints
- **Intuitive GUI Interface**: Dialog-based interface using Zenipy (Python Zenity binding)
- **Multiple Operations**: Start, stop, restart, enable, disable Ollama service
- **Smart Context**: Shows relevant options based on current service state
- **Desktop Integration**: Desktop icon and applications menu entry
- **Status Monitoring**: View detailed service status and logs with loop-back to menu
- **Desktop Notifications**: Desktop notifications for operation feedback
- **Fallback Support**: Terminal interface when GUI tools aren't available
- **Secure Permission Handling**: Intelligent sudo/pkexec integration for service management
- **Enhanced Error Handling**: Comprehensive error handling with user-friendly messages

## 📋 Prerequisites

### Required

- **Linux** system with systemd
- **Ollama** service installed and configured
- **sudo** privileges for service management
- **Python 3.6+**

### Optional (for GUI features)

- **zenipy** - Python library for Zenity dialogs (`pip install zenipy`)
- **notify-send** (libnotify) - For desktop notifications

### Installing Dependencies

**Ubuntu/Debian:**

```bash
sudo apt install libnotify-bin python3-pip
pip3 install zenipy
```

**Fedora/RHEL/CentOS:**

```bash
sudo dnf install libnotify python3-pip
pip3 install zenipy
```

**Arch Linux:**

```bash
sudo pacman -S libnotify python-pip
pip install zenipy
```

## 🛠️ Installation

### Automated Installation

1. **Clone or download** the repository:

```bash
git clone <repository-url> ollama_toggle
cd ollama_toggle
```

2. **Run the installation script**:

```bash
chmod +x install.sh
./install.sh
```

The installer will:

- Detect your system and install required dependencies
- Install the Python service manager
- Set up desktop integration
- Configure the service manager

### Manual Installation

1. **Install Python dependencies**:

```bash
pip3 install zenipy
```

2. **Copy the Python script**:

```bash
cp ollama-toggle.py /home/$USER/Scripts/
chmod +x /home/$USER/Scripts/ollama-toggle.py
```

3. **Install desktop entry**:

```bash
# Install desktop entry
cp ollama-manager.desktop /home/$USER/.local/share/applications/
update-desktop-database /home/$USER/.local/share/applications/

# Optionally copy to desktop
cp ollama-manager.desktop /home/$USER/Desktop/
chmod +x /home/$USER/Desktop/ollama-manager.desktop
```

4. **Verify Ollama service exists**:

```bash
systemctl status ollama
```

## 📱 Usage

### GUI Method (Recommended)

1. **Desktop Icon**: Double-click the "Ollama Service Manager" icon on your desktop
2. **Applications Menu**: Search for "Ollama Service Manager" in your applications launcher
3. **Command Line**: Run the script directly:

   ```bash
   /home/$USER/Scripts/ollama-toggle.py
   ```

### Available Actions

The interface will show different options based on the current service state:

**When Ollama is Running:**

- 🛑 **Stop Service** - Stop the Ollama service
- 🔄 **Restart Service** - Restart the Ollama service
- ❌ **Disable Service** - Stop and disable autostart
- 📊 **View Status** - Show detailed service information

**When Ollama is Stopped:**

- ▶️ **Start Service** - Start the Ollama service
- ✅ **Enable Service** - Start and enable autostart
- 📊 **View Status** - Show detailed service information

### Terminal Method

If GUI tools aren't available, the script automatically falls back to a terminal interface:

```bash
/home/$USER/Scripts/ollama-toggle.py
```

## 📁 File Structure

```text
ollama_toggle/
├── README.md                    # This documentation
├── ollama-toggle.py            # Main Python service manager
├── ollama-manager.desktop      # Desktop entry file
├── install.sh                  # Enhanced installation script
├── LICENSE                     # GPL-3.0 license
└── screenshots/                # Usage screenshots
    ├── README.md               # Screenshots documentation
    ├── gui-running.png
    ├── gui-stopped.png
    └── status-view.png
```

## 🔧 Configuration

### Custom Installation Paths

If you want to install the script in a different location, modify these variables in the desktop entry file:

```ini
[Desktop Entry]
# Update path as needed
Exec=/path/to/your/ollama-toggle.py
```

### Service Customization

The script automatically detects your Ollama service. If you have a custom service name, modify the SERVICE_NAME variable:

```python
SERVICE_NAME: Final[str] = "your-custom-service"
```

## 🐛 Troubleshooting

### Common Issues

**1. "Permission denied" errors:**

```bash
# Ensure the script is executable
chmod +x /home/$USER/Scripts/ollama-toggle.py
```

**2. Desktop icon doesn't appear:**

```bash
# Update desktop database
update-desktop-database /home/$USER/.local/share/applications/
# Or refresh desktop
killall nautilus  # For GNOME
```

**3. Zenipy not found:**

```bash
# Install zenipy for GUI features
pip3 install zenipy
```

**4. Ollama service not found:**

```bash
# Check if Ollama is installed as a service
systemctl status ollama
sudo systemctl status ollama

# If not found, ensure Ollama is properly installed
curl -fsSL https://ollama.ai/install.sh | sh
```

**5. Sudo password prompts:**

- The script requires sudo privileges for service management
- You'll be prompted for your password when performing service operations
- The script prefers pkexec (GUI password prompt) when available
- This is normal and required for security

### Debug Mode

Run the script with debug output:

```bash
python3 -u /home/$USER/Scripts/ollama-toggle.py
```

## 🔒 Security Notes

- The script uses `sudo` or `pkexec` for service management operations
- Prefers `pkexec` in GUI sessions for better user experience
- Password prompts are handled by the system's authentication mechanism
- No passwords are stored or logged by the script
- Service operations are performed using standard systemctl commands

## 🧪 Testing

### Test the Installation

1. **Check script execution**:

```bash
/home/$USER/Scripts/ollama-toggle.py
```

2. **Verify desktop integration**:

```bash
desktop-file-validate /home/$USER/.local/share/applications/ollama-manager.desktop
```

3. **Test service operations**:

```bash
# Check current status
systemctl is-active ollama
systemctl is-enabled ollama
```

## 📝 Changelog

### Version 2.0.0

- **Complete Rewrite in Python**: Migrated from Bash to Python with zenipy for modern, maintainable code
- **Enhanced Installation**: Updated install.sh with automatic dependency detection
- **Improved Desktop Integration**: Updated desktop file for Python implementation
- **Loop-back Interface**: Returns to menu after viewing status for better UX
- **Advanced Error Handling**: Enhanced error handling with user-friendly messages
- **Type Safety**: Added comprehensive type hints and documentation
- **Removed Bash Version**: Fully migrated to Python-only implementation

### Version 1.0.0

- Initial release with Bash implementation
- GUI interface with Zenity
- Desktop integration
- Service start/stop/restart functionality
- Enable/disable autostart
- Status monitoring
- Desktop notifications
- Terminal fallback

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

### Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd ollama_toggle

# Make script executable
chmod +x ollama-toggle.py

# Install Python dependencies for development
pip3 install zenipy

# Test locally
./ollama-toggle.py
```

## 📄 License

This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama Team** - For creating the Ollama AI platform
- **Zenity Developers** - For the dialog interface toolkit
- **Zenipy Developers** - For the Python Zenity binding
- **Linux Community** - For systemd and desktop integration standards

## 📞 Support

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Verify your system meets the [Prerequisites](#-prerequisites)
3. Run in debug mode for detailed output
4. Check Ollama service logs: `sudo journalctl -u ollama -f`
5. Ensure zenipy is properly installed: `pip3 show zenipy`

---

**Made with ❤️ for the Ollama community**
