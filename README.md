# ReAct Agent

## Requirements

- Python 3.11+
- Poetry

## Getting Started

### Clone the Repository

```bash
git clone https://github.com/murnat98/react-agent.git
cd react-agent
```

### Create a Virtual Environment and Install Dependencies

- Create a file named `.env` with these 2 keys:
```
SERP_API_KEY=your_serp_api_key
LLM_API_KEY=your_llm_api_key
```

```bash
python3 -m venv venv
source venv/bin/activate
poetry install
```

### Run the Agent

```bash
poetry run python -m react_agent "Your query"
```
