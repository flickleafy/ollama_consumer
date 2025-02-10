# Ollama Consumer

A Python-based interactive chat interface for Ollama models with advanced model management, error handling, and automatic service recovery capabilities.

## Features

- 🤖 **Interactive Chat Interface**: Clean command-line chat experience with colored output
- 🔄 **Dynamic Model Switching**: Switch between models on-the-fly with the 's' command
- 🛠️ **Advanced Model Management**: Load, unload, and manage Ollama models efficiently
- 🚨 **Automatic Error Recovery**: Intelligent error handling with automatic service restart
- 🎨 **Formatted Responses**: Color-coded output with special handling for thinking tags
- ⚙️ **Configuration Management**: Persistent configuration using INI files
- 🔧 **Service Monitoring**: Automatic Ollama service health checks and recovery

## Requirements

- Python 3.6+
- Ollama installed and configured
- `requests` library for HTTP communication

## Installation

1. Clone the repository:

```bash
git clone https://github.com/flickleafy/ollama_consumer.git
cd ollama_consumer
```

2. Install required dependencies:

```bash
pip install requests
```

3. Configure your settings:

```bash
cp config.ini.example config.ini
# Edit config.ini with your preferred settings
```

## Usage

### Basic Usage

Run the main script to start the interactive chat:

```bash
python main.py
```

### Commands

- **Chat**: Type your message and press Enter
- **Switch Model**: Type `s` to select a different model
- **Exit**: Type `exit`, `quit`, or `q` to quit

### Model Management

The application provides comprehensive model management:

- **Automatic Loading**: Models are loaded on first use
- **Smart Unloading**: Previous models are unloaded when switching
- **Error Recovery**: Automatic recovery from model loading errors
- **Service Restart**: Automatic Ollama service restart if needed

### Configuration

The `config.ini` file stores:

- Currently loaded model information
- Service configuration settings
- User preferences

## Project Structure

```
ollama_consumer/
├── main.py              # Main application with chat interface
├── test_ollama.py       # Test utilities and functions
├── config.ini           # Configuration file (created from example)
├── config.ini.example   # Example configuration
├── LICENSE              # GPL v3 License
└── README.md           # This file
```

## Error Handling

The application includes robust error handling for common scenarios:

- **Connection Issues**: Automatic service restart attempts
- **Model Loading Errors**: Intelligent retry with recovery procedures
- **HTTP 500 Errors**: Automatic model unloading and service recovery
- **Service Down**: Multiple restart strategies with fallback options

## Testing

Run the test suite:

```bash
python test_ollama.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Development

### Key Components

- **ModelManager**: Handles model loading, unloading, and state management
- **Service Management**: Automatic Ollama service monitoring and restart
- **Error Recovery**: Comprehensive error handling and recovery procedures
- **UI Components**: Color-coded terminal output and user interaction

### Configuration Management

The application uses `configparser` for persistent configuration storage, tracking:

- Current loaded model state
- Service configuration
- User preferences

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

### License Summary

- ✅ **Commercial use** - You may use this software commercially
- ✅ **Modification** - You may modify the source code
- ✅ **Distribution** - You may distribute this software
- ✅ **Patent use** - You may use any patents that contributors grant
- ✅ **Private use** - You may use this software privately

**Requirements:**

- 📋 **License and copyright notice** - Include license and copyright notice with the software
- 📋 **State changes** - Document changes made to the software
- 📋 **Disclose source** - Source code must be made available when distributing the software
- 📋 **Same license** - Modifications must be released under the same license

**Limitations:**

- ❌ **Liability** - This software is provided without warranty
- ❌ **Warranty** - No warranty is provided

## Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/flickleafy/ollama_consumer/issues) page
2. Create a new issue with detailed information
3. Include logs and error messages when possible

## Changelog

### v1.0.0 (Current)

- Initial release with basic chat functionality
- Model management and switching capabilities
- Automatic error recovery and service restart
- Configuration management system
- Comprehensive error handling

## Acknowledgments

- Built for use with [Ollama](https://ollama.ai/)
- Uses the Ollama REST API for model interaction
- Inspired by the need for robust local LLM interaction tools
