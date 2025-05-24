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

## Running the Agent

To run the default agent:

```bash
adk run weather_time_agent
```

This will launch the weather_time_agent defined in `weather_time_agent/agent.py`.

## Project Structure

```
GraphCycle/
├── weather_time_agent/
│   └── agent.py          # Agent logic
├── requirements.txt       # Python dependencies
└── README.md
```

## License

MIT (or your preferred license)
