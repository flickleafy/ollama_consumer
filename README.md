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
- 📊 **Comprehensive Benchmarking**: Advanced model performance evaluation with MoE support
- 🎮 **Interactive Benchmark Mode**: User-friendly guided benchmark configuration
- 📁 **Organized Results**: Category-based file output for better data management

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
├── main.py                # Main application with chat interface
├── test_ollama.py         # Test utilities and functions
├── benchmark.py           # Model benchmarking script
├── sample_questions.json  # Sample benchmark questions
├── config.ini             # Configuration file (created from example)
├── config.ini.example     # Example configuration
├── LICENSE                # GPL v3 License
└── README.md             # This file
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

## Benchmarking

The project includes a comprehensive benchmarking tool to evaluate model performance with advanced features for testing all types of models, including Mixture of Experts (MoE) models.

### Quick Benchmark

Run a benchmark with default questions on all available models:

```bash
python benchmark.py
```

### Interactive Mode

Launch the interactive benchmark configuration:

```bash
python benchmark.py --interactive
# or simply
python benchmark.py
```

The interactive mode provides a guided setup with options for:

- Model selection (all, by category, or manual selection)
- Custom questions from files
- Output and logging configuration
- Category filtering

### Advanced Benchmarking Options

```bash
# Quiet mode (less output)
python benchmark.py --quiet

# Custom base filename (creates multiple category files)
python benchmark.py --output my_benchmark

# Filter by model size category
python benchmark.py --category small
python benchmark.py --category medium
python benchmark.py --category large

# Use custom questions from a JSON file
python benchmark.py --custom-questions sample_questions.json

# Show available model categories
python benchmark.py --list-categories

# Combine options
python benchmark.py --output benchmark_2025_01_15 --category medium --quiet
```

### Benchmark Features

- **🤖 Advanced Model Support**: Full support for Mixture of Experts (MoE) models with accurate parameter estimation
- **📊 Model Categorization**: Automatic categorization by size (Small ≤16B, Medium 16B-100B, Large >100B)
- **🎯 Smart Parameter Detection**: API-driven parameter extraction with pattern-based fallback
- **📁 Organized Output**: Separate files for each category to avoid large monolithic files
- **⚡ Load Time Measurement**: Records how long each model takes to load
- **🕐 Inference Time Tracking**: Measures response time for each question
- **🧹 Response Cleaning**: Removes thinking tags to store only final answers
- **🛡️ Robust Error Handling**: Graceful handling of keyboard interrupts and model errors
- **📈 Comprehensive Analytics**: Detailed performance statistics and comparisons

### Model Categories

The benchmark automatically categorizes models:

- **Small Models**: ≤16B parameters (e.g., Llama 3.2 3B, Gemma 2 9B)
- **Medium Models**: 16B-100B parameters (e.g., Llama 3.1 70B)
- **Large Models**: >100B parameters (e.g., Llama 4 405B, MoE models like 128x17B)
- **Unknown**: Models with undetectable parameter counts

### MoE Model Support

The benchmark includes sophisticated support for Mixture of Experts models:

- **Conservative Parameter Estimation**: Uses realistic scaling factors instead of linear multiplication
- **Pattern Recognition**: Detects MoE patterns like.
- **API Integration**: Prioritizes official API parameter data when available

### Custom Questions

Create a JSON file with your own questions:

```json
[
  "What is artificial intelligence?",
  "Explain quantum computing simply.",
  "Write a haiku about programming.",
  "Solve this problem: What is 15 × 23?",
  "Name three advantages of renewable energy."
]
```

### Benchmark Output

Results are saved as separate JSON files for better organization:

```text
benchmark_2025-01-15-14.30.15_summary.json  # Overall results and statistics
benchmark_2025-01-15-14.30.15_small.json    # Small models detailed results
benchmark_2025-01-15-14.30.15_medium.json   # Medium models detailed results
benchmark_2025-01-15-14.30.15_large.json    # Large models detailed results
benchmark_2025-01-15-14.30.15_unknown.json  # Unknown size models results
```

#### File Structure

- **Summary File**: Contains overall benchmark info, category summaries, and performance statistics
- **Category Files**: Detailed results for each model size category with individual model performance data

#### Benefits of Separate Files

- ✅ **Manageable File Sizes**: Avoid large monolithic files
- ✅ **Category-Specific Analysis**: Easy to analyze specific model types
- ✅ **Faster Loading**: Load only the data you need
- ✅ **Better Organization**: Clear separation by model characteristics

The output includes detailed performance metrics, model comparisons, category statistics, and summary analytics to help you choose the best model for your use case.

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

### v1.1.0 (Current)

**Enhanced Benchmarking System:**

- 🧠 **MoE Model Support**: Full support for Mixture of Experts models with accurate parameter estimation
- 📊 **Model Categorization**: Automatic categorization by size (Small/Medium/Large/Unknown)
- 📁 **Organized Output**: Separate JSON files for each category to avoid large monolithic files
- 🎮 **Interactive Mode**: Guided benchmark configuration with user-friendly options
- 🎯 **Category Filtering**: Benchmark specific model size categories
- 🛡️ **Enhanced Error Handling**: Graceful keyboard interrupt handling and robust error recovery
- 🚀 **Performance Improvements**: Optimized parameter detection and response processing

**Code Quality Improvements:**

- 📖 **Better Documentation**: Comprehensive help text and usage examples

### v1.0.0

- Initial release with basic chat functionality
- Model management and switching capabilities
- Automatic error recovery and service restart
- Configuration management system
- Comprehensive error handling

## Acknowledgments

- Built for use with [Ollama](https://ollama.ai/)
- Uses the Ollama REST API for model interaction
- Inspired by the need for robust local LLM interaction tools
