# 🦙 Ollama Setup Guide for Multimodal RAG

This guide will help you set up Ollama to run local LLM models with the Multimodal RAG system.

## 🚀 Quick Start

### 1. Install Ollama

**Linux/Mac:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

**Windows:**
Download and install from [ollama.ai](https://ollama.ai/download)

### 2. Start Ollama Server
```bash
ollama serve
```
The server will run on `http://localhost:11434` by default.

### 3. Pull a Model
```bash
# Recommended general purpose model (3.8GB)
ollama pull llama2

# Or for a smaller, faster model (1.1GB)
ollama pull phi

# For coding tasks (3.8GB)
ollama pull codellama
```

### 4. Configure the RAG System
Edit your `.env` file:
```bash
# Use Ollama as the LLM provider
LLM_PROVIDER=ollama

# Specify the model (default: llama2)
OLLAMA_MODEL=llama2

# Ollama server URL (default: http://localhost:11434)
OLLAMA_BASE_URL=http://localhost:11434
```

### 5. Run the RAG System
```bash
python main.py web
```

## 📋 Recommended Models

| Model | Size | Use Case | Command |
|-------|------|----------|---------|
| **llama2** | 3.8GB | General purpose, good quality | `ollama pull llama2` |
| **phi** | 1.1GB | Fast, lightweight | `ollama pull phi` |
| **codellama** | 3.8GB | Code generation/explanation | `ollama pull codellama` |
| **tinyllama** | 637MB | Very fast, basic tasks | `ollama pull tinyllama` |
| **llama2:13b** | 7.3GB | Higher quality (needs more RAM) | `ollama pull llama2:13b` |

## ⚙️ Configuration Options

### Environment Variables

```bash
# .env file settings
LLM_PROVIDER=ollama          # Use Ollama
LLM_PROVIDER=openai          # Use OpenAI
LLM_PROVIDER=auto            # Auto-detect (Ollama first, then OpenAI)

OLLAMA_MODEL=llama2          # Which Ollama model to use
OLLAMA_BASE_URL=http://localhost:11434  # Ollama server URL
```

### Model Selection

You can change models at runtime by setting the `OLLAMA_MODEL` environment variable:

```bash
# Use a different model
export OLLAMA_MODEL=phi
python main.py web
```

## 🔧 Advanced Configuration

### Custom Ollama Server

If running Ollama on a different machine:

```bash
# .env
OLLAMA_BASE_URL=http://192.168.1.100:11434
```

### Model Parameters

The system uses these default parameters for Ollama:
- **Temperature**: 0.7 (creativity level)
- **Max Tokens**: 1000 (response length)
- **Stream**: False (wait for complete response)

## 🚨 Troubleshooting

### Ollama Not Connected
```
🔴 Ollama: Not connected
```
**Solutions:**
1. Make sure Ollama is running: `ollama serve`
2. Check if the port is correct (default: 11434)
3. Verify firewall settings

### Model Not Available
```
❌ Ollama model llama2 not available
```
**Solutions:**
1. Pull the model: `ollama pull llama2`
2. Check available models: `ollama list`
3. Update `OLLAMA_MODEL` in `.env`

### Slow Responses
**Solutions:**
1. Use a smaller model like `phi` or `tinyllama`
2. Increase system RAM
3. Use GPU acceleration if available

### Out of Memory
**Solutions:**
1. Use a smaller model (`tinyllama`, `phi`)
2. Close other applications
3. Restart Ollama: `ollama serve`

## 💡 Performance Tips

### Model Size vs Quality
- **Small models** (phi, tinyllama): Fast but less accurate
- **Medium models** (llama2): Good balance
- **Large models** (llama2:13b): Best quality but slower

### System Requirements
- **Minimum**: 4GB RAM, small models only
- **Recommended**: 8GB RAM for llama2
- **Optimal**: 16GB+ RAM for large models

### Speed Optimization
1. **Use SSD storage** for faster model loading
2. **Close unnecessary applications** to free RAM
3. **Use appropriate model size** for your hardware

## 🔄 Switching Between Providers

### Use Ollama Only
```bash
# .env
LLM_PROVIDER=ollama
OLLAMA_MODEL=llama2
```

### Use OpenAI Only
```bash
# .env
LLM_PROVIDER=openai
OPENAI_API_KEY=your_api_key_here
```

### Auto Mode (Recommended)
```bash
# .env
LLM_PROVIDER=auto
OLLAMA_MODEL=llama2
OPENAI_API_KEY=your_api_key_here
```
Auto mode tries Ollama first, falls back to OpenAI if Ollama is unavailable.

## 🧪 Testing Your Setup

### Command Line Test
```bash
# Test Ollama directly
ollama run llama2 "Hello, how are you?"

# Test the RAG system
python main.py cli
```

### Web Interface Test
1. Run: `python main.py web`
2. Check the sidebar for "🤖 LLM Provider"
3. Should show: "🟢 Ollama: Connected"

## 🌟 Benefits of Using Ollama

✅ **Privacy**: All processing happens locally
✅ **Cost**: No API fees after initial setup
✅ **Speed**: No network latency for inference
✅ **Offline**: Works without internet connection
✅ **Control**: Full control over model and parameters
✅ **Customization**: Can fine-tune models for specific use cases

## 📚 Popular Model Combinations

### For User Manuals (Recommended)
```bash
ollama pull llama2        # Good balance of quality and speed
```

### For Quick Prototyping
```bash
ollama pull phi           # Fast responses, good for testing
```

### For Code Documentation
```bash
ollama pull codellama     # Specialized for code understanding
```

### For Production (High Quality)
```bash
ollama pull llama2:13b    # Best quality, needs more resources
```

## 🔗 Useful Commands

```bash
# List installed models
ollama list

# Remove a model
ollama rm llama2

# Show model information
ollama show llama2

# Update a model
ollama pull llama2

# Stop Ollama server
pkill ollama
```

---

**Need help?** Check the [Ollama documentation](https://github.com/jmorganca/ollama) or create an issue in this repository.