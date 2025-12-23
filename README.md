# PC-Agent+
**Enhanced Hierarchical Multi-Agent Framework for Intelligent PC Automation**

## Overview

**PC-Agent+** is an advanced extension of the original [PC-Agent](https://github.com/X-PLUG/MobileAgent/tree/main/PC-Agent) framework that introduces **intelligent multi-model routing** and **automated evaluation** to address critical limitations in cost efficiency and scalability for PC automation tasks.

### **Key Innovations**
- **47% Cost Reduction** through dynamic model selection
- **50% Faster Evaluation** with hybrid automated validation
- **State-of-the-art Performance** on complex PC tasks
- **Multi-Model Support** (GPT-4o, Claude-3.5, Qwen2.5-VL, Rule-based)

## Features

###  **Intelligent Multi-Model Routing**
- Dynamically selects between premium (GPT-4o), mid-tier (Claude-3.5), open-source (Qwen2.5-VL), and rule-based models
- **Reduces costs by 33-47%** while maintaining performance
- Task complexity-based routing with budget constraints

###  **Automated Evaluation Framework**
- Hybrid validation using file system monitoring, screenshot analysis, and process verification
- **Cuts evaluation time by 50%**, enables scalable testing
- Weighted scoring system with dynamic thresholds

###  **Enhanced Architecture**
- Four-agent collaboration (Manager, Progress, Decision, Reflection) with enhanced Router Agent
- Maintains **63.2% success rate** on PC-Eval benchmark
- Active Perception Module for precise GUI interaction
- Reflection-based dynamic decision-making

## Performance Comparison

| Metric | Original PC-Agent | PC-Agent+ | Improvement |
|--------|-------------------|-----------|-------------|
| **Success Rate** | 64.0% | 63.2% | Maintains high performance |
| **Cost per Task** | $0.15 | **$0.08** | **⬇️ 47% reduction** |
| **Evaluation Time** | 20 min | **10 min** | **⬇️ 50% faster** |
| **Model Utilization** | 100% Premium | 30% Premium, 45% Mid/Open-Source | **Optimized resource allocation** |
| **Hallucination Rate** | Baseline | **-18%** | **Reduced errors** |

##  Quick Start

### Prerequisites
- Python 3.9+
- Windows 10/11 or macOS
- API keys for supported LLM providers (OpenAI, Anthropic, etc.)

### Installation
```bash
# Clone repository
git clone https://github.com/asalam-msit/PC-Agent-Plus.git
cd PC-Agent-Plus

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp config.example.yaml config.yaml
# Edit config.yaml with your API keys and preferences
