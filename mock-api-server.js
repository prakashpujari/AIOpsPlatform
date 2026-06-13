const express = require('express');
const cors = require('cors');

const app = express();
app.use(cors());
app.use(express.json());

// Mock data
const mockIncidents = [
  {
    id: "inc-001",
    title: "High CPU Usage on Payment Service",
    description: "CPU usage exceeded 90% threshold on payment-service pods",
    severity: "high",
    status: "investigating",
    source: "prometheus",
    created_at: "2026-06-12T10:30:00Z",
    updated_at: "2026-06-12T10:35:00Z",
    assignee: "john.doe@bank.internal",
    tags: ["performance", "payment-service", "kubernetes"],
    runbook_url: "https://runbooks.bank.internal/payment-service-high-cpu"
  },
  {
    id: "inc-002",
    title: "Database Connection Pool Exhaustion",
    description: "PostgreSQL connection pool exhausted on orders database",
    severity: "critical",
    status: "open",
    source: "datadog",
    created_at: "2026-06-12T09:15:00Z",
    updated_at: "2026-06-12T09:20:00Z",
    assignee: "jane.smith@bank.internal",
    tags: ["database", "postgresql", "connection-pool"],
    runbook_url: "https://runbooks.bank.internal/postgres-connection-pool"
  },
  {
    id: "inc-003",
    title: "Kafka Consumer Lag Alert",
    description: "Consumer lag exceeded 10000 messages on transaction-topic",
    severity: "medium",
    status: "resolved",
    source: "prometheus",
    created_at: "2026-06-11T14:20:00Z",
    updated_at: "2026-06-11T15:45:00Z",
    assignee: "bob.wilson@bank.internal",
    tags: ["kafka", "messaging", "lag"],
    runbook_url: "https://runbooks.bank.internal/kafka-consumer-lag"
  }
];

const mockMetrics = {
  cpu_usage: { current: 67, threshold: 80, unit: "%" },
  memory_usage: { current: 72, threshold: 85, unit: "%" },
  disk_usage: { current: 45, threshold: 90, unit: "%" },
  network_io: { current: 1250, threshold: 5000, unit: "Mbps" },
  request_latency_p99: { current: 245, threshold: 500, unit: "ms" },
  error_rate: { current: 0.12, threshold: 1.0, unit: "%" },
  active_incidents: 3,
  resolved_today: 12,
  mttr_minutes: 23
};

const mockChatMessages = [
  {
    id: "msg-1",
    role: "assistant",
    content: "Hello! I'm your AI Ops Copilot. How can I help you today?",
    timestamp: "2026-06-12T10:00:00Z"
  }
];

// Health endpoint
app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'mock-api', version: '1.0.0' });
});

// API v1 routes
app.get('/api/v1/health', (req, res) => {
  res.json({ status: 'ok', service: 'aiops-api', version: '1.0.0' });
});

// Incidents endpoints
app.get('/api/v1/incidents', (req, res) => {
  const page = parseInt(req.query.page) || 1;
  const pageSize = parseInt(req.query.page_size) || 20;
  const start = (page - 1) * pageSize;
  const end = start + pageSize;
  const items = mockIncidents.slice(start, end);
  res.json({
    items,
    total: mockIncidents.length,
    page,
    page_size: pageSize,
    total_pages: Math.ceil(mockIncidents.length / pageSize)
  });
});

app.get('/api/v1/incidents/:id', (req, res) => {
  const incident = mockIncidents.find(i => i.id === req.params.id);
  if (!incident) {
    return res.status(404).json({ detail: 'Incident not found' });
  }
  res.json(incident);
});

app.post('/api/v1/incidents', (req, res) => {
  const newIncident = {
    id: `inc-${Date.now()}`,
    ...req.body,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    status: 'open'
  };
  mockIncidents.unshift(newIncident);
  res.status(201).json(newIncident);
});

app.patch('/api/v1/incidents/:id', (req, res) => {
  const index = mockIncidents.findIndex(i => i.id === req.params.id);
  if (index === -1) {
    return res.status(404).json({ detail: 'Incident not found' });
  }
  mockIncidents[index] = { ...mockIncidents[index], ...req.body, updated_at: new Date().toISOString() };
  res.json(mockIncidents[index]);
});

// Metrics endpoints
app.get('/api/v1/metrics/summary', (req, res) => {
  res.json(mockMetrics);
});

app.get('/api/v1/metrics/timeseries', (req, res) => {
  const metric = req.query.metric || 'cpu_usage';
  const hours = parseInt(req.query.hours) || 24;
  const now = Date.now();
  const data = [];
  for (let i = hours; i >= 0; i--) {
    const timestamp = now - i * 3600 * 1000;
    data.push({
      timestamp: new Date(timestamp).toISOString(),
      value: mockMetrics[metric] ? mockMetrics[metric].current * (0.8 + Math.random() * 0.4) : Math.random() * 100
    });
  }
  res.json({ metric, data });
});

// Chat endpoints
app.get('/api/v1/chat/history', (req, res) => {
  res.json({ messages: mockChatMessages });
});

app.post('/api/v1/chat', (req, res) => {
  const userMessage = {
    id: `msg-${Date.now()}`,
    role: 'user',
    content: req.body.message,
    timestamp: new Date().toISOString()
  };
  mockChatMessages.push(userMessage);

  // Simulate AI response
  setTimeout(() => {
    const aiResponse = {
      id: `msg-${Date.now() + 1}`,
      role: 'assistant',
      content: `I understand you're asking about "${req.body.message}". Based on the current system status, I can see there are ${mockMetrics.active_incidents} active incidents. Would you like me to provide more details about any specific incident or help you with root cause analysis?`,
      timestamp: new Date().toISOString()
    };
    mockChatMessages.push(aiResponse);
  }, 1000);

  res.json({ message: userMessage });
});

// AI Gateway chat endpoint
app.post('/v1/chat', (req, res) => {
  const userMessage = req.body.messages?.[req.body.messages.length - 1]?.content || req.body.message || 'Hello';

  // Simulate streaming response
  if (req.body.stream) {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');

    const response = `I understand you're asking about "${userMessage}". Based on the current system status, I can see there are ${mockMetrics.active_incidents} active incidents. Would you like me to provide more details about any specific incident or help you with root cause analysis?`;

    const words = response.split(' ');
    let i = 0;
    const interval = setInterval(() => {
      if (i < words.length) {
        res.write(`data: ${JSON.stringify({ choices: [{ delta: { content: words[i] + ' ' } }] })}\n\n`);
        i++;
      } else {
        res.write(`data: [DONE]\n\n`);
        clearInterval(interval);
        res.end();
      }
    }, 50);
  } else {
    res.json({
      id: `chatcmpl-${Date.now()}`,
      object: 'chat.completion',
      created: Math.floor(Date.now() / 1000),
      model: 'llama3.3-70b',
      choices: [{
        index: 0,
        message: {
          role: 'assistant',
          content: `I understand you're asking about "${userMessage}". Based on the current system status, I can see there are ${mockMetrics.active_incidents} active incidents. Would you like me to provide more details about any specific incident or help you with root cause analysis?`
        },
        finish_reason: 'stop'
      }],
      usage: {
        prompt_tokens: 50,
        completion_tokens: 100,
        total_tokens: 150
      }
    });
  }
});

// Auth endpoints (mock)
app.post('/api/v1/auth/login', (req, res) => {
  res.json({
    access_token: 'mock-jwt-token-' + Date.now(),
    token_type: 'bearer',
    expires_in: 3600,
    user: {
      id: 'user-1',
      email: req.body.email || 'admin@bank.internal',
      name: 'Admin User',
      roles: ['admin', 'operator', 'analyst']
    }
  });
});

app.get('/api/v1/auth/me', (req, res) => {
  const authHeader = req.headers.authorization;
  if (!authHeader) {
    return res.status(401).json({ detail: 'Not authenticated' });
  }
  res.json({
    id: 'user-1',
    email: 'admin@bank.internal',
    name: 'Admin User',
    roles: ['admin', 'operator', 'analyst']
  });
});

// Dashboard stats
app.get('/api/v1/dashboard/stats', (req, res) => {
  res.json({
    total_incidents: mockIncidents.length,
    active_incidents: mockMetrics.active_incidents,
    resolved_today: mockMetrics.resolved_today,
    mttr_minutes: mockMetrics.mttr_minutes,
    system_health: 'degraded',
    critical_alerts: 1,
    warning_alerts: 2
  });
});

// Root cause analysis
app.get('/api/v1/rca/:incidentId', (req, res) => {
  res.json({
    incident_id: req.params.incidentId,
    root_cause: "Database connection pool exhaustion due to missing connection cleanup in payment-service v2.3.1",
    contributing_factors: [
      "Connection leak in PaymentService.processRefund() method",
      "Increased traffic during end-of-month processing",
      "Connection pool size not scaled with traffic"
    ],
    recommended_actions: [
      "Fix connection leak in PaymentService.processRefund()",
      "Increase connection pool size from 20 to 50",
      "Add connection leak detection monitoring",
      "Implement circuit breaker for database calls"
    ],
    confidence: 0.92,
    generated_at: new Date().toISOString()
  });
});

// Runbooks
app.get('/api/v1/runbooks', (req, res) => {
  res.json([
    { id: 'rb-1', title: 'High CPU Usage Mitigation', category: 'performance', url: 'https://runbooks.bank.internal/high-cpu' },
    { id: 'rb-2', title: 'Database Connection Pool Exhaustion', category: 'database', url: 'https://runbooks.bank.internal/postgres-pool' },
    { id: 'rb-3', title: 'Kafka Consumer Lag Recovery', category: 'messaging', url: 'https://runbooks.bank.internal/kafka-lag' },
    { id: 'rb-4', title: 'Memory Leak Investigation', category: 'performance', url: 'https://runbooks.bank.internal/memory-leak' }
  ]);
});

// Start server
const PORT = process.env.PORT || 8000;
app.listen(PORT, () => {
  console.log(`Mock API server running on http://localhost:${PORT}`);
  console.log(`Health check: http://localhost:${PORT}/health`);
  console.log(`API docs: http://localhost:${PORT}/api/v1/health`);
});