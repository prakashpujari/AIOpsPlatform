# AI Gateway Testing Guide

## Running the AI Gateway Locally (No Docker Required)

The AI Gateway can be started without Docker. For LLM calls, you can use Groq as a cloud provider.

### Setup

```bash
# From the ai-gateway directory
cd C:\pp\GitHub\AIOpsPlatform\apps\ai-gateway

# Set the Groq API key
echo "groq_api_key=YOUR_GROQ_API_KEY" > .env
```

### Start the Gateway

```bash
# Start in development mode
python -m uvicorn src.main:app --host 127.0.0.1 --port 8001 --reload

# Or use the startup script
python start_server.py
```

## Test Endpoints

### 1. Health Check
```bash
curl http://localhost:8001/health
```

### 2. Chat Completion (Non-streaming) - Using Groq
```bash
curl -X POST http://localhost:8001/v1/chat/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "strategy": "intent",
    "model": "llama-3.3-70b-groq",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### 3. Chat Completion (Streaming) - Using Groq
```bash
curl -X POST http://localhost:8001/v1/chat/stream \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{
    "messages": [{"role": "user", "content": "Write a Python function to add two numbers"}],
    "strategy": "code",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

### 4. Model Registry
```bash
curl http://localhost:8001/v1/health/models
```

### 5. Prometheus Metrics
```bash
curl http://localhost:8001/metrics
```

## Available Models

| Model ID | Priority | Provider | Notes |
|----------|----------|----------|-------|
| llama3.3-70b | 1 | VLLM | Local model |
| deepseek-r1 | 2 | VLLM | Local model |
| deepseek-coder | 3 | VLLM | Local model |
| qwen3-72b | 2 | VLLM | Local model |
| phi4-14b | 4 | OLLAMA | Local model |
| gemma2-9b | 5 | OLLAMA | Local model |
| **llama-3.3-70b-groq** | 10 | **GROQ** | **Cloud-hosted - works without Docker!** |

## Routing Strategies

- **intent**: Selects model based on message content intent (default)
- **cost**: Selects the cheapest model
- **latency**: Selects the fastest model (highest tokens/sec)
- **quality**: Selects highest priority model

## Running Tests

```bash
# All AI Gateway tests
python -m pytest tests/unit tests/integration -v

# Run Groq integration test
python test_groq_integration.py
```

## Test Cases

### Test Case 1: Intent-based Routing
```bash
# Route to code model for coding questions
curl -X POST http://localhost:8001/v1/chat/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{"messages": [{"role": "user", "content": "Write a Python function"}], "strategy": "intent"}'
# Expected: Selects deepseek-coder if healthy, or falls back
```

### Test Case 2: Cost-based Routing
```bash
curl -X POST http://localhost:8001/v1/chat/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "strategy": "cost"}'
# Expected: Selects gemma2-9b or llama-3.3-70b-groq (cheapest)
```

### Test Case 3: Cloud Provider (Groq)
```bash
curl -X POST http://localhost:8001/v1/chat/complete \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{"messages": [{"role": "user", "content": "Hello"}], "model": "llama-3.3-70b-groq"}'
# Expected: Uses Groq's Llama 3.3 70B model
```

## Browser Testing

Open in browser:
- **Health**: http://localhost:8001/health
- **API Docs**: http://localhost:8001/docs
- **Metrics**: http://localhost:8001/metrics
- **Model Status**: http://localhost:8001/v1/health/models

Use a tool like Postman or curl to POST to http://localhost:8001/v1/chat/complete with:
- Header: `X-API-Key: changeme`
- Body: `{"messages": [{"role": "user", "content": "Your question"}], "strategy": "intent", "model": "llama-3.3-70b-groq"}