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
- 🚫 **Model Blacklisting**: Exclude problematic models from benchmarking via configuration
- 🎮 **Interactive Benchmark Mode**: User-friendly guided benchmark configuration
- 📁 **Organized Results**: Category-based file output for better data management
- 🎯 **GPU Optimization**: Multi-GPU configuration tools for optimal performance

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
- **System prompt**: Optional instruction that defines how the model should behave
- **Model blacklist**: Models to exclude from benchmarking

#### Setting a System Prompt

To set a system prompt that will be applied to all conversations, edit your `config.ini` file:

```ini
[ollama]
current_loaded_model = llama3.2:latest
system_prompt = You are a helpful AI assistant. Please provide clear, accurate, and concise responses.
```

#### Blacklisting Models

To exclude problematic models from benchmarking, add them to the blacklist section in your `config.ini` file:

```ini
[blacklist]
# Models to exclude from benchmarking (JSON array format)
models = ["model1:latest", "problematic_model:tag"]

# Alternative formats also supported:
# models = model1:latest, model2:tag, model3:latest
# models = single_model:latest
```

Blacklisted models will be automatically filtered out from:

- All benchmark operations
- Interactive model selection
- Category-based filtering

This is useful for excluding models that:

- Are known to fail during benchmarking
- Cause system instability
- Take excessively long to load or respond

The system prompt will be automatically applied to all conversations with any model. Examples of useful system prompts:

- `You are a helpful coding assistant. Provide clean, well-commented code examples.`
- `You are a creative writing assistant. Help with storytelling and creative ideas.`
- `Respond in a professional and technical manner. Focus on accuracy and detail.`
- `Keep responses brief and to the point. Use bullet points when appropriate.`

To remove the system prompt, simply delete the `system_prompt` line or leave it empty.

## Project Structure

```text
ollama_consumer/
├── main.py                # Main application with chat interface
├── test_ollama.py         # Test utilities and functions
├── benchmark.py           # Model benchmarking script
├── check_gpu_config.py    # GPU configuration checker and optimizer
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

## GPU Optimization

For users with multiple GPUs, this project includes tools and guidance to optimize Ollama's GPU usage for maximum performance.

### GPU Configuration Tool

Use the included GPU configuration checker to analyze your setup and get optimization recommendations:

```bash
python check_gpu_config.py
```

This tool will:

- **Detect all NVIDIA GPUs** and their capabilities
- **Show current GPU utilization** and memory usage
- **Recommend optimal environment variables** for your setup
- **Display GPU priority order** for best performance

### Multi-GPU Optimization Strategy

The goal is to **prioritize the most capable GPU** while using weaker GPUs only when necessary for model splitting:

#### **Automatic GPU Detection and Recommendations**

The `check_gpu_config.py` script analyzes your GPUs by:

- Memory capacity (primary factor)
- Current utilization
- Temperature and power consumption
- Available memory

#### **Environment Variables for Optimal Performance**

Based on your GPU configuration, set these environment variables:

```bash
# Example for dual GPU config (primary 16Gb) + (secondary 8Gb)
# Force Ollama to prioritize GPU 0 first
export CUDA_VISIBLE_DEVICES=0,1

# Use 90% of GPU memory (reserve 10% for system)
export OLLAMA_GPU_MEMORY_FRACTION=0.9

# Limit to one model at a time for optimal GPU usage
export OLLAMA_MAX_LOADED_MODELS=1

# Optional: Force all layers to GPU when possible
export OLLAMA_GPU_LAYERS=-1
```

#### **Configuration Behavior**

With proper configuration:

- ✅ **Single-GPU Models**: Always load on the most capable GPU
- ✅ **Large Models**: Automatically split across GPUs when needed
- ✅ **Memory Optimization**: Reserve 10% GPU memory for system operations
- ✅ **Performance Priority**: Weaker GPUs used only when primary GPU can't handle the entire model

### Manual GPU Configuration

If you prefer manual configuration:

#### **Step 1: Identify Your GPUs**

```bash
nvidia-smi --query-gpu=index,name,memory.total --format=csv
```

#### **Step 2: Set GPU Priority**

Order GPUs by capability in `CUDA_VISIBLE_DEVICES`:

```bash
# Most capable GPU first, weaker GPUs after
export CUDA_VISIBLE_DEVICES=0,1,2  # Adjust indices based on your setup
```

#### **Step 3: Configure Memory Usage**

```bash
# Reserve memory for system operations
export OLLAMA_GPU_MEMORY_FRACTION=0.9

# Limit concurrent models for optimal performance
export OLLAMA_MAX_LOADED_MODELS=1
```

#### **Step 4: Apply Configuration**

Add to your shell profile (`.bashrc` or `.zshrc`):

```bash
echo 'export CUDA_VISIBLE_DEVICES=0,1
export OLLAMA_GPU_MEMORY_FRACTION=0.9
export OLLAMA_MAX_LOADED_MODELS=1
export OLLAMA_GPU_LAYERS=-1' >> ~/.zshrc

source ~/.zshrc
```

#### **Step 5: Restart Ollama**

```bash
# Restart Ollama service
sudo systemctl restart ollama

# Or if using a different service manager:
# sudo service ollama restart
```

### GPU Optimization Benefits

Proper GPU configuration provides:

- 🚀 **Faster Model Loading**: Models load on the most capable GPU first
- 💾 **Efficient Memory Usage**: Optimal memory allocation across GPUs
- ⚡ **Better Performance**: Reduced inference times for most workloads
- 🔄 **Smart Fallback**: Automatic model splitting only when necessary
- 🎯 **Resource Optimization**: Weaker GPUs reserved for overflow scenarios

### Troubleshooting GPU Issues

**Model Loading Slowly:**

- Check if the model is being split unnecessarily
- Verify `CUDA_VISIBLE_DEVICES` order prioritizes your best GPU

**GPU Memory Errors:**

- Reduce `OLLAMA_GPU_MEMORY_FRACTION` to 0.8 or 0.7
- Ensure no other GPU-intensive processes are running

**Models Loading on Wrong GPU:**

- Verify environment variables are set correctly
- Restart Ollama service after configuration changes
- Check GPU memory availability with `nvidia-smi`

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
- � **Model Blacklisting**: Exclude problematic models from benchmarking via configuration
- �🛡️ **Enhanced Error Handling**: Graceful keyboard interrupt handling and robust error recovery
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
