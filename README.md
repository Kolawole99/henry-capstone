# Nexus-Mind: Multi-Agent Corporate Knowledge System

**A production-ready multi-agent RAG system for enterprise knowledge management with intelligent routing, specialized agents, and comprehensive observability.**

Nexus-Mind transforms static corporate documents into an active, intelligent knowledge assistant. Using a hierarchical multi-agent architecture, it routes queries to specialized agents, retrieves relevant information through RAG (Retrieval Augmented Generation), and validates responses through an independent auditor—all while maintaining full traceability via Langfuse.

---

## 🎯 Problem Statement

In rapidly scaling organizations, institutional memory is fragmented across individuals, Slack threads, PDF manuals, and cloud drives. This leads to:

- **Onboarding Friction**: New hires spend 20-30% of their first three months searching for basic information
- **Information Attrition**: When senior employees leave, their localized knowledge vanishes
- **Siloed Inefficiency**: Cross-departmental queries cause context-switching fatigue

**Nexus-Mind solves this** by providing instant, accurate access to departmental knowledge through AI-powered agents with specialized expertise.

---

## 🏗️ Architecture Overview

### Multi-Agent Workflow

```
User Query
    ↓
[Coordinator] ← Orchestrates entire workflow
    ↓
[Dispatcher] ← Routes to best agent (AI-powered selection)
    ↓
[Specialist] ← Performs RAG retrieval from agent-specific knowledge base
    ↓
[Auditor] ← Validates safety, tone, and quality with scoring
    ↓
Final Response (with sources, scores, and metadata)
```

### Agent Roles

1. **Coordinator Agent**
   - Orchestrates the entire query processing pipeline
   - Manages agent-to-agent communication
   - Tracks performance metrics (routing time, specialist time, audit time)
   - Implements error handling and fallback logic

2. **Dispatcher Agent**
   - Analyzes user queries using GPT-4o-mini
   - Dynamically fetches available agents from database
   - Routes to best agent based on AI-generated descriptions
   - Returns routing decision with confidence score and reasoning
   - **Prompt**: `src/server/prompts/dispatcher.md`

3. **Specialist Agent**
   - Performs RAG retrieval from agent-specific ChromaDB collection
   - Uses GPT-4o for response generation
   - Loads custom system prompts per agent (AI-generated)
   - Returns answer with source chunks (file names + content snippets)
   - **Prompt**: Dynamically loaded from database (generated via `agent_prompt_generator.py`)

4. **Auditor Agent**
   - Reviews specialist responses for safety and quality
   - Scores responses on three dimensions:
     - **Politeness** (0.0-1.0): Professional tone and courtesy
     - **Correctness** (0.0-1.0): Accuracy and completeness
     - **Confidence** (0.0-1.0): Clarity and definitiveness
   - Can revise responses to improve quality
   - **Prompt**: `src/server/prompts/auditor.md`

---

## 🛠️ Technology Stack

### Core Technologies

| Technology | Purpose | Why Chosen |
|------------|---------|------------|
| **LangChain** | Agent orchestration, RAG chains, structured outputs | Industry-standard framework for LLM applications with LCEL (LangChain Expression Language) |
| **ChromaDB** | Vector database for embeddings | Persistent storage, agent-specific collections, efficient similarity search |
| **OpenAI GPT-4o** | LLM for generation | State-of-the-art reasoning and generation capabilities |
| **Pydantic** | Data validation and type safety | Structured outputs, field validation, type hints throughout |
| **Langfuse** | Observability and tracing | Full visibility into agent decisions, performance metrics, debugging |
| **FastAPI** | REST API backend | High-performance async framework with auto-generated OpenAPI docs |
| **PostgreSQL** | Persistent storage | Reliable database for agents, files, chat sessions |
| **React + TypeScript** | Frontend UI | Modern, type-safe user interface |

### Supporting Libraries

- **python-json-logger**: Structured JSON logging for production
- **pypdf**: PDF document processing
- **tiktoken**: Token counting for embeddings
- **SQLAlchemy**: ORM for database operations
- **uvicorn**: ASGI server for FastAPI

---

## 📊 Data Models & Type Safety

### Pydantic Schemas (`src/server/models/schemas.py`)

```python
class UserQuery(BaseModel):
    """User input with optional role context"""
    query_text: str
    user_role: Optional[str]

class RoutingDecision(BaseModel):
    """Dispatcher output - which agent to use"""
    agent_id: str  # UUID of selected agent
    agent_name: str  # Human-readable name
    reasoning: str  # Why this agent was chosen
    confidence: float  # 0.0-1.0 confidence score

class SourceChunk(BaseModel):
    """Individual source chunk with content"""
    file_name: str  # Source document name
    content: str  # Actual text content (truncated to 500 chars)

class AgentResponse(BaseModel):
    """Specialist output with sources"""
    answer: str
    sources: List[str]  # Unique file names
    source_chunks: List[SourceChunk]  # Detailed chunks with content
    agent_name: str

class AuditResult(BaseModel):
    """Auditor output with quality scores"""
    is_safe: bool
    feedback: str
    final_answer: str  # Potentially revised
    politeness_score: float  # 0.0-1.0
    correctness_score: float  # 0.0-1.0
    confidence_score: float  # 0.0-1.0
```

**Type Safety Benefits:**
- Compile-time validation of data flow between agents
- Auto-generated API documentation
- Prevents runtime errors from malformed data
- Enables structured LLM outputs via `with_structured_output()`

---

## 🔍 RAG Implementation Strategy

### Document Chunking

**Strategy**: Recursive Character Text Splitter
- **Chunk Size**: 1000 characters
- **Overlap**: 200 characters (20% overlap for context preservation)
- **Rationale**: Balances context retention with embedding efficiency

```python
# src/server/utils/vector_store.py
text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
```

### Embedding & Storage

- **Embeddings**: OpenAI `text-embedding-ada-002` (1536 dimensions)
- **Vector Store**: ChromaDB with persistent storage
- **Collections**: Agent-specific (e.g., `agent_<uuid>`)
- **Metadata Tracking**:
  - `file_id`: UUID for tracking and deletion
  - `source_file`: Original filename
  - `source`: Full file path

### Retrieval Strategy

- **Retriever Type**: Similarity search
- **Top-K**: 4 most relevant chunks
- **Search Method**: Cosine similarity on embeddings
- **Context Assembly**: LangChain's `create_stuff_documents_chain` combines chunks with prompt

```python
# Retrieval chain pattern
retriever = vector_store.get_retriever()
question_answer_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(retriever, question_answer_chain)
```

### File Management

- **Upload**: Files stored in `data/uploads/<file_id>_<filename>`
- **Ingestion**: Automatic chunking and embedding on upload
- **Deletion**: Removes both file and all associated embeddings from ChromaDB
- **Supported Formats**: PDF, TXT (via `pypdf` and LangChain loaders)

---

## 📝 Prompt Engineering

### Externalized Prompts

All prompts stored as markdown files in `src/server/prompts/`:
- `dispatcher.md`: Routing logic and decision criteria
- `auditor.md`: Safety guidelines and scoring rubrics
- `agent_generator.md`: Template for generating agent-specific prompts

**Benefits:**
- Easy iteration without code changes
- Version control for prompt evolution
- Non-technical stakeholders can review/edit
- Supports prompt templates with variables

### Dynamic Agent Prompts

Agents have AI-generated system prompts created via `agent_prompt_generator.py`:

```python
@observe(name="agent_prompt_generator", as_type="generation")
def generate_agent_prompt(agent_name: str, user_description: str):
    # Uses GPT-4o to generate specialized prompt
    # Based on examples in agent_generator.md
    # Returns: system_prompt + refined_description
```

**Example Generated Prompt** (for "HR Specialist"):
```
You are an expert HR representative for our company.

Your role:
- Provide accurate information about HR policies, benefits, and procedures
- Maintain a professional, empathetic, and supportive tone
- Always cite specific policy documents when providing guidance
- Escalate sensitive matters to human HR staff

When answering:
1. Start with a direct, clear answer
2. Provide relevant policy details from source documents
3. Include important deadlines, requirements, or next steps
4. Cite document sources
5. If applicable, provide contact information for follow-up
...
```

---

## 📊 Logging & Monitoring Strategy

### Structured Logging (`src/server/utils/logger.py`)

**Format**: JSON logs for production observability

```json
{
  "timestamp": "2025-12-18T16:10:40.123Z",
  "level": "INFO",
  "logger": "coordinator",
  "message": "Processing query",
  "extra_fields": {
    "query": "How do I report harassment?",
    "user_role": "employee",
    "agent_id": "uuid-here"
  }
}
```

**Log Levels:**
- `INFO`: Normal operations (query processing, agent routing)
- `WARNING`: Non-critical issues (no agents available, file validation failed)
- `ERROR`: Failures requiring attention (API errors, database issues)

**Key Metrics Logged:**
- **Routing Duration**: Time to select agent (ms)
- **Specialist Duration**: Time for RAG retrieval + generation (ms)
- **Audit Duration**: Time for quality review (ms)
- **Total Duration**: End-to-end query processing (ms)
- **Source Counts**: Number of chunks retrieved
- **Audit Scores**: Politeness, correctness, confidence

### Request Logging Middleware

```python
# src/server/api/middleware.py
class LoggingMiddleware:
    # Logs every HTTP request with:
    # - Method, path, status code
    # - Duration
    # - Client IP
```

### Langfuse Tracing

**Integration**: `@observe` decorators on all agent methods

```python
@observe(name="coordinator_process_query", as_type="chain")
def process_query(self, query_text: str, ...):
    # Full trace captured automatically
```

**Trace Hierarchy:**
```
coordinator_process_query (chain)
├── dispatcher_route_query (generation)
├── specialist_generate_response (generation)
│   └── LLM calls, retrieval operations
└── auditor_audit_response (generation)
```

**Langfuse Dashboard Shows:**
- Complete execution tree
- LLM token usage and costs
- Latency breakdown by agent
- Input/output for each step
- Error traces with stack traces

---

## ✅ Input Validation & Security

### Validation Layer (`src/server/utils/validators.py`)

**Message Validation:**
- Max length: 5000 characters
- Min length: 1 character
- No SQL injection patterns
- XSS prevention (HTML tag stripping)

**File Validation:**
- Max size: 10MB
- Allowed extensions: `.pdf`, `.txt`, `.md`
- Filename sanitization (removes special characters)
- MIME type verification

**UUID Validation:**
- Proper UUID format for agent_id, file_id, session_id
- Prevents injection attacks

**Agent Name/Description Validation:**
- Name: 3-100 characters, alphanumeric + spaces
- Description: 10-1000 characters

### Pydantic Field Validators

```python
class ChatRequest(BaseModel):
    message: str
    
    @field_validator('message')
    @classmethod
    def validate_message_field(cls, v):
        return validate_message(v)  # Raises ValueError if invalid
```

---

## 🧪 Evaluation Strategy

### Test Queries (`data/test-queries.json`)

13 diverse test cases covering:
- HR policies (vacation, remote work, performance reviews)
- IT support (VPN, passwords, software)
- Finance (expenses, reimbursements)
- Legal (NDAs, contracts, data privacy)
- Complex multi-domain queries

### Evaluation Metrics

1. **Routing Accuracy**
   - Does dispatcher select the correct agent?
   - Measured via confidence scores and manual review

2. **RAG Faithfulness**
   - Does answer come from retrieved documents?
   - Measured via source chunk inspection

3. **Response Quality (Auditor Scores)**
   - **Politeness**: 0.7+ target (professional tone)
   - **Correctness**: 0.85+ target (accurate information)
   - **Confidence**: 0.8+ target (clear, definitive)

4. **Performance Benchmarks**
   - Routing: <500ms
   - Specialist (RAG): <3000ms
   - Audit: <1000ms
   - Total: <5000ms (5 seconds)

5. **Source Attribution**
   - 100% of responses must cite sources
   - Source chunks must be relevant to answer

### Manual Evaluation Checklist

- [ ] Correct agent selected for query type
- [ ] Answer addresses the user's question
- [ ] Sources are relevant and correctly cited
- [ ] Tone is professional and helpful
- [ ] No hallucinations (answer grounded in sources)
- [ ] Audit scores are reasonable (>0.7 across dimensions)

---

## 🚀 Setup & Installation

### Prerequisites

- Python 3.9+
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- PostgreSQL (via Docker)
- ChromaDB (via Docker)

### 1. Clone Repository

```bash
git clone <repo-url>
cd henry-capstone
```

### 2. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Key Dependencies (Pinned Versions):**
- `langchain==0.3.27`
- `chromadb==1.3.7`
- `pydantic==2.12.5`
- `langfuse==3.7.0`
- `fastapi==0.125.0`

### 3. Environment Configuration

```bash
cp .env.example .env
```

**Required Environment Variables:**
```bash
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional: for custom endpoints

# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5439/henry_capstone

# ChromaDB
CHROMA_HOST=localhost
CHROMA_PORT=8000

# Langfuse (Optional - for tracing)
LANGFUSE_HOST=https://cloud.langfuse.com
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR
```

### 4. Start Docker Services

```bash
docker-compose up -d
```

**Services Started:**
- PostgreSQL (port 5439)
- ChromaDB (port 8000)

### 5. Start Backend API

```bash
./start_api.sh
```

API available at: `http://localhost:8001`
API docs: `http://localhost:8001/docs`

### 6. Start Frontend (Optional)

```bash
cd src/client
npm install
npm run dev
```

Frontend available at: `http://localhost:5173`

---

## 📖 Usage Guide

### Creating an Agent

**Via API:**
```bash
curl -X POST http://localhost:8001/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "HR Specialist",
    "description": "Handles employee questions about policies, benefits, leave, and workplace conduct"
  }'
```

**What Happens:**
1. `agent_prompt_generator.py` uses GPT-4o to create specialized system prompt
2. Agent stored in PostgreSQL with generated prompt
3. Dedicated ChromaDB collection created (`agent_<uuid>`)

**Via UI:**
1. Navigate to Settings page
2. Click "Create Agent"
3. Enter name and description
4. View generated system prompt
5. Agent ready for use

### Uploading Knowledge Base Files

```bash
curl -X POST http://localhost:8001/agents/{agent_id}/files \
  -F "file=@path/to/policy.pdf"
```

**What Happens:**
1. File validated (size, type, name)
2. Saved to `data/uploads/`
3. Chunked (1000 chars, 200 overlap)
4. Embedded via OpenAI
5. Stored in agent-specific ChromaDB collection
6. Metadata tracked in PostgreSQL

### Querying the System

**Via API:**
```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "How many vacation days do I get?",
    "session_id": "uuid-here"
  }'
```

**Response:**
```json
{
  "response": "As a new employee, you receive 15 vacation days per year...",
  "session_id": "uuid-here",
  "department": "HR Specialist",
  "sources": ["employee_handbook.pdf", "pto_policy.pdf"]
}
```

**Via UI:**
1. Navigate to Chat page
2. Type your question
3. AI automatically routes to best agent
4. Response shown with sources
5. Session persisted for context

---

## 🏗️ Project Structure

```
henry-capstone/
├── src/
│   ├── server/
│   │   ├── agents/              # Multi-agent system
│   │   │   ├── coordinator.py   # Orchestration
│   │   │   ├── dispatcher.py    # Routing logic
│   │   │   ├── specialist.py    # RAG execution
│   │   │   └── auditor.py       # Quality validation
│   │   ├── api/
│   │   │   ├── main.py          # FastAPI app
│   │   │   ├── database.py      # SQLAlchemy models
│   │   │   ├── middleware.py    # Logging middleware
│   │   │   └── routes/          # API endpoints
│   │   │       ├── chat.py      # Chat endpoint
│   │   │       ├── agents.py    # Agent CRUD
│   │   │       └── files.py     # File upload/delete
│   │   ├── models/
│   │   │   └── schemas.py       # Pydantic models
│   │   ├── prompts/             # Externalized prompts
│   │   │   ├── dispatcher.md
│   │   │   ├── auditor.md
│   │   │   └── agent_generator.md
│   │   └── utils/
│   │       ├── agent_prompt_generator.py  # AI prompt generation
│   │       ├── vector_store.py            # ChromaDB manager
│   │       ├── prompt_loader.py           # Load .md prompts
│   │       ├── logger.py                  # Structured logging
│   │       └── validators.py              # Input validation
│   └── client/                  # React frontend
│       ├── src/
│       │   ├── pages/           # ChatPage, SettingsPage
│       │   ├── components/      # UI components
│       │   ├── api/             # API client
│       │   └── utils/           # Frontend validators
│       └── package.json
├── data/
│   ├── uploads/                 # Uploaded files
│   └── test-queries.json        # Evaluation test cases
├── docs/
│   └── proposal.md              # Detailed technical proposal
├── docker-compose.yml           # PostgreSQL + ChromaDB
├── requirements.txt             # Python dependencies (pinned)
├── .env.example                 # Environment template
├── .gitignore                   # Excludes .env, uploads, etc.
└── README.md                    # This file
```

---

## 🎯 Design Decisions & Tradeoffs

### Why Multi-Agent?

**Single Agent Limitations:**
- Confuses context (applies HR tone to code snippets)
- Cannot specialize prompts per domain
- Difficult to audit and improve specific capabilities
- No separation of concerns

**Multi-Agent Benefits:**
- **Specialization**: Each agent optimized for its domain
- **Auditability**: Independent auditor prevents hallucinations
- **Scalability**: Add new agents without affecting existing ones
- **Observability**: Trace each agent's contribution
- **Reliability**: Separation reduces cascading failures

### Why ChromaDB?

**Alternatives Considered:**
- **FAISS**: In-memory only, no persistence
- **Pinecone**: Cloud-only, vendor lock-in
- **Weaviate**: Heavier, more complex setup

**ChromaDB Chosen Because:**
- Persistent storage (survives restarts)
- Agent-specific collections (isolation)
- Simple Docker deployment
- Open-source, no vendor lock-in
- Efficient similarity search

### Why Pydantic?

**Benefits:**
- Type safety prevents runtime errors
- Auto-validation of LLM outputs
- Structured outputs via `with_structured_output()`
- Self-documenting code with Field descriptions
- FastAPI integration for API validation

### Why Langfuse?

**Alternatives:**
- **LangSmith**: Requires LangChain Cloud account
- **Custom logging**: Lacks visualization and trace hierarchy

**Langfuse Chosen Because:**
- Self-hosted or cloud options
- Beautiful trace visualization
- Token usage and cost tracking
- Integrates seamlessly with LangChain
- Production-ready observability

---

## 📈 Performance Benchmarks

**Typical Query Processing:**
- Routing (Dispatcher): ~300-500ms
- RAG Retrieval (Specialist): ~2000-3000ms
- Audit (Auditor): ~800-1200ms
- **Total**: ~3-5 seconds

**Optimization Opportunities:**
- Cache frequent queries
- Parallel agent execution where possible
- Batch embeddings for file uploads
- Use faster embedding models (e.g., `text-embedding-3-small`)

---

## 🔒 Security Considerations

1. **API Keys**: Never committed to git (`.env` in `.gitignore`)
2. **Input Validation**: All user inputs validated and sanitized
3. **File Uploads**: Size limits, type restrictions, filename sanitization
4. **SQL Injection**: Prevented via SQLAlchemy ORM
5. **XSS Prevention**: HTML tags stripped from inputs
6. **UUID Validation**: Prevents injection in database queries

---

## 🧪 Testing

### Run Test Queries

```bash
# Test dispatcher routing
python -c "from src.server.agents.coordinator import Coordinator; \
           c = Coordinator(); \
           print(c.process_query('How do I report harassment?'))"
```

### Evaluate Agent Performance

1. Load test queries from `data/test-queries.json`
2. Process each query through coordinator
3. Check Langfuse dashboard for traces
4. Verify audit scores meet thresholds (>0.7)
5. Manually review source attribution

---

## 🚧 Future Enhancements

### Phase 2: Enterprise Hardening

- [ ] **Authentication**: OAuth 2.0 for user management
- [ ] **Role-Based Access Control**: Restrict agent access by user role
- [ ] **Multi-tenancy**: Isolate agents per organization
- [ ] **Advanced RAG**: Hybrid search (keyword + semantic)
- [ ] **Caching Layer**: Redis for frequent queries
- [ ] **Rate Limiting**: Prevent API abuse
- [ ] **Webhooks**: Real-time notifications for file ingestion
- [ ] **Analytics Dashboard**: Query volume, agent performance, user satisfaction

### Phase 3: Integrations

- [ ] **Google Workspace**: Auto-sync documents
- [ ] **Microsoft OneDrive**: Live document updates
- [ ] **Slack Bot**: Query agents from Slack
- [ ] **CRM Integration**: Access customer data (with PII controls)
- [ ] **MCP Server**: Centralized model management

---

## 📚 Additional Resources

- **Langfuse Dashboard**: `https://cloud.langfuse.com` (or self-hosted)
- **API Documentation**: `http://localhost:8001/docs`
- **LangChain Docs**: https://python.langchain.com/
- **ChromaDB Docs**: https://docs.trychroma.com/
- **Pydantic Docs**: https://docs.pydantic.dev/

---

## 📄 License

MIT License - See LICENSE file for details
