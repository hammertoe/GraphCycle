# GraphCycle

GraphCycle is an experimental autonomous agent built using the Google Agent Development Kit (ADK). It demonstrates how agents can extract and organize knowledge from unstructured data.

## Features

* Autonomous execution using ADK
* Simple weather and time agent
* Easily extensible for more advanced multi-agent coordination

## Prerequisites

* Python 3.10+
* Git
* Google ADK installed via pip

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/hammertoe/GraphCycle.git
cd GraphCycle
```

### 2. Set up a virtual environment

**macOS / Linux**
```bash
python3 -m venv venv
source venv/bin/activate
```

**Windows**
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install the Google ADK CLI (if not already installed)

```bash
pip install google-adk
```

### 5. Set up Google Gemini API Key

1. Generate an API key for Google Gemini at [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Set the API key as an environment variable:

**macOS / Linux**
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

**Windows**
```bash
set GOOGLE_API_KEY=your_api_key_here
```

Alternatively, you can add it to your `.bashrc`, `.zshrc`, or create a `.env` file in the project root.

## Running the Agent

To run the default agent:

```bash
adk run graphcycle
```

This will launch the weather_time_agent defined in `graphcycle/agent.py`.

## Project Structure

```
GraphCycle/
├── graphcycle/
│   └── agent.py          # Agent logic
├── requirements.txt      # Python dependencies
└── README.md
```

