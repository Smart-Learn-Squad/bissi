# 🤖 BISSI Agent - Testing & Demonstration Guide

## 📌 Overview

Three ways to test and see BISSI agent capabilities in action:

### 1. **Unit Tests** (Quick validation - 26 tests)
Test isolated agent components without LLM

### 2. **Integration Tests** (See tools execute)
Watch the agent actually use tools to accomplish tasks

### 3. **Interactive REPL** (Real-time exploration)
Chat with the agent and see it use tools in real-time

---

## 🧪 Option 1: Unit Tests (Fastest)

**What it does**: Validates core agent mechanisms (26 tests, ~3.3s)

**Run**:
```bash
cd bissi
source .venv/bin/activate
bash tests/QUICK_START.sh
```

**Output**: ✅ 26/26 tests pass in ~3.3 seconds

**Good for**: Regression testing, CI/CD, quick validation

---

## 🔌 Option 2: Integration Tests (See Tools)

**What it does**: Agent executes real tools against test files

**Run**:
```bash
cd bissi
source .venv/bin/activate
python -m pytest tests/test_agentic_integration.py -v -s
```

**What you see**:
- ✅ File operations (read, write, edit, list)
- ✅ Python code execution
- ✅ Directory traversal
- ✅ Tool chaining workflows
- ✅ Error handling

**Example output**:
```
✅ Listed directory: {'items': [{'name': 'file1.txt', ...}]}
✅ Python execution result: {'output': 'Result: 30\n'}
✅ All 26 tools are callable
✅ Agent context components initialized
```

**Good for**: Seeing tools in action, validating tool integration

---

## 💬 Option 3: Interactive REPL (Best Experience)

**What it does**: Chat with the agent in real-time, see it use tools

### Pre-requisites

Before starting REPL, the LLM server must be running:

```bash
# In terminal 1: Start llama.cpp server
python -m llama_cpp.server \
    --model /path/to/gemma-4-E2B-it-Q4_K_M.gguf \
    --port 8001 \
    --n_ctx 8192
```

### Run Interactive REPL

```bash
cd bissi
source .venv/bin/activate
python agent_repl.py
```

**You'll see**:
```
================================================================================
🤖 BISSI AGENT - INTERACTIVE CAPABILITY DEMONSTRATION
================================================================================

📋 Available commands:
  - Type your prompt to see the agent use tools
  - Type 'tools' to see available tools
  - Type 'info' to see agent information
  - Type 'history' to see tool execution log
  - Type 'exit' or 'quit' to close

================================================================================

🤔 You: _
```

### Commands in REPL

```
Type your prompt:           "Crée un fichier test.txt"
List tools:                 "tools"
Agent info:                 "info"
Execution history:          "history"
Exit:                       "exit" or "quit"
```

### Example Prompts

```
French prompts (Agent responds in French):
  - "Crée un fichier hello.txt avec le contenu 'Hello World'"
  - "Lis le fichier hello.txt"
  - "Liste tous les fichiers .py dans le répertoire courant"
  - "Cherche des fichiers contenant 'TODO'"
  - "Calcule 2^10 en Python"
  - "Compte les lignes de code dans tous les .py"

See what happens:
  - Agent analyzes your request
  - Calls appropriate tools
  - Shows you tool execution
  - Provides results and explanations
```

**Good for**: Exploring capabilities, seeing real agent behavior

---

## 🎯 Demonstration Script

Automated demo with pre-written prompts:

```bash
cd bissi
source .venv/bin/activate
python test_agent_demo.py
```

**What it does**:
1. Creates test directory
2. Runs 8 pre-written tasks:
   - File creation
   - File reading
   - Directory listing
   - File search
   - File editing
   - Multiple file operations
   - Python code execution
   - Data analysis

**Output**: Shows how agent accomplishes each task step-by-step

---

## 📊 Comparison

| Feature | Unit Tests | Integration | REPL |
|---------|-----------|-------------|------|
| Speed | ⚡ ~3.3s | ⚡⚡ ~5-10s | 🐢 Depends on LLM |
| See tools? | ❌ No | ✅ Yes | ✅✅ Yes + Interactive |
| LLM needed? | ❌ No | ❌ No | ✅ Yes (llama.cpp) |
| Real execution? | ❌ Mocked | ✅ Yes | ✅✅ Yes |
| Interactive? | ❌ No | ❌ No | ✅ Yes |
| CI/CD ready? | ✅ Yes | ✅ Yes | ❌ No |

---

## 🛠️ Agent Capabilities Tested

### File Operations ✅
- Read text files
- Write text files
- Edit files (find/replace)
- Delete files
- Get file info

### Search & Browse ✅
- Search by pattern (*.py)
- Search by content
- List directories
- Get directory tree

### Data Processing ✅
- Read Excel files
- Write Excel files
- Execute Python code

### Documents ✅
- Read Word documents
- Write Word documents
- Read PDF
- Read PowerPoint
- Write PowerPoint

### Vision (if available) ✅
- Describe images
- Extract text from images
- Analyze charts
- Analyze screenshots

### System ✅
- Get clipboard
- Set clipboard
- Move files
- Get recent files

---

## 🚀 Quick Start (Recommended Flow)

1. **First time? Run unit tests** (quick validation):
   ```bash
   bash tests/QUICK_START.sh
   ```

2. **See tools in action** (integration tests):
   ```bash
   python -m pytest tests/test_agentic_integration.py -v -s
   ```

3. **Play with agent** (interactive REPL):
   ```bash
   # Make sure llama.cpp is running first!
   python agent_repl.py
   ```

---

## 🎓 Understanding Tool Calls

When you see this in REPL:
```
🔧 Calling tool: read_text_file
   Args: {'file_path': '/tmp/test.txt'}
     ✅ Result: Content of file...
```

The agent:
1. Analyzed your request
2. Decided which tool to use
3. Called the tool with appropriate parameters
4. Got the result
5. Processed it to give you an answer

---

## ⚙️ Configuration

### Agent Settings
Located in `core/config.py`:
- Model path
- LLM server URL/port
- Timeout settings
- Temperature
- Context token limit

### LLM Server
Configure in `bissi-master.sh`:
- Model file path
- Port (default: 8001)
- Context size (default: 8192)
- Threads/GPU usage

---

## 🐛 Troubleshooting

**"llama.cpp server not available"**
- Start the server: `python -m llama_cpp.server --model <model_path> --port 8001`

**"Test timeout"**
- Increase timeout in `core/config.py`
- Or increase `initial_wait` in pytest

**"ModuleNotFoundError"**
- Activate venv: `source .venv/bin/activate`
- Install requirements: `pip install -r requirements.txt`

**"Tool not found"**
- Check spelling in prompt
- Use French for better results (agent optimized for French)

---

## 📝 Files

| File | Purpose |
|------|---------|
| `agent_repl.py` | Interactive REPL for live agent testing |
| `test_agent_demo.py` | Automated demonstration with pre-written prompts |
| `tests/test_agentic_capabilities.py` | 26 unit tests validating agent components |
| `tests/test_agentic_integration.py` | Integration tests showing tool execution |
| `tests/QUICK_START.sh` | Script to quickly run unit tests |
| `tests/README.md` | Detailed test guide |

---

## ✨ Key Takeaways

✅ **26 tools available** - Comprehensive capability set  
✅ **Tool-calling robust** - Reliable tool invocation  
✅ **Error handling** - Graceful failure recovery  
✅ **Real execution** - Not simulated, actually runs  
✅ **Chainable** - Can use multiple tools in sequence  
✅ **Production-ready** - Validated and tested  

---

*Last updated: 2026-05-07*
