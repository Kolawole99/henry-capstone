# Docker Setup Guide

This project uses Docker Compose to run the following services:

- **PostgreSQL** (Port 5432): Relational database
- **ChromaDB** (Port 8000): Vector database for embeddings
- **Langfuse** (Port 3000): LLM observability and analytics platform

## Quick Start

### 1. Configure Environment Variables

Copy the example environment file and customize it:

```bash
cp .env.example .env
```

**Important**: For production, generate secure secrets:

```bash
# Generate LANGFUSE_SECRET
openssl rand -base64 32

# Generate LANGFUSE_SALT
openssl rand -base64 32
```

Update the `.env` file with these generated values.

### 2. Start All Services

```bash
docker-compose up -d
```

### 3. Verify Services are Running

```bash
docker-compose ps
```

All services should show as "Up" and healthy.

### 4. Access the Services

- **ChromaDB API**: http://localhost:8000
- **Langfuse Dashboard**: http://localhost:3000
- **PostgreSQL**: localhost:5432

## Service Details

### PostgreSQL

- **Default Database**: `henry_capstone`
- **Langfuse Database**: `langfuse` (automatically created)
- **Connection String**: `postgresql://postgres:postgres@localhost:5432/henry_capstone`

### ChromaDB

- **API Endpoint**: http://localhost:8000
- **Health Check**: http://localhost:8000/api/v1/heartbeat
- **Data Persistence**: Stored in Docker volume `chroma_data`

### Langfuse

- **Dashboard**: http://localhost:3000
- **API**: http://localhost:3000/api/public
- **First-time Setup**: Create an admin account on first visit
- **Database**: Uses the PostgreSQL instance (separate database)

## Common Commands

### Start services
```bash
docker-compose up -d
```

### Stop services
```bash
docker-compose down
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f chromadb
docker-compose logs -f postgres
docker-compose logs -f langfuse-server
```

### Restart a service
```bash
docker-compose restart chromadb
```

### Remove all data (⚠️ Warning: This deletes all data!)
```bash
docker-compose down -v
```

## Connecting to Services

### Python Example - ChromaDB

```python
import chromadb

# Connect to ChromaDB
client = chromadb.HttpClient(host='localhost', port=8000)

# Create a collection
collection = client.create_collection(name="my_collection")

# Add documents
collection.add(
    documents=["This is a document", "This is another document"],
    metadatas=[{"source": "doc1"}, {"source": "doc2"}],
    ids=["id1", "id2"]
)

# Query
results = collection.query(
    query_texts=["search query"],
    n_results=2
)
```

### Python Example - PostgreSQL

```python
import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="henry_capstone",
    user="postgres",
    password="postgres"
)

cursor = conn.cursor()
cursor.execute("SELECT version();")
print(cursor.fetchone())
```

### Python Example - Langfuse

```python
from langfuse import Langfuse

# Initialize Langfuse client
langfuse = Langfuse(
    public_key="your-public-key",  # Get from Langfuse dashboard
    secret_key="your-secret-key",  # Get from Langfuse dashboard
    host="http://localhost:3000"
)

# Track an LLM call
trace = langfuse.trace(name="my-llm-call")
generation = trace.generation(
    name="gpt-call",
    model="gpt-4",
    input="What is AI?",
    output="AI is artificial intelligence..."
)
```

## Troubleshooting

### Port Conflicts

If you have port conflicts, modify the ports in your `.env` file:

```env
POSTGRES_PORT=5433
CHROMA_PORT=8001
LANGFUSE_PORT=3001
```

### Service Won't Start

Check logs for the specific service:

```bash
docker-compose logs langfuse-server
```

### Database Connection Issues

Ensure PostgreSQL is healthy before Langfuse starts:

```bash
docker-compose ps postgres
```

### Reset Everything

If you need to start fresh:

```bash
# Stop and remove containers, networks, and volumes
docker-compose down -v

# Start again
docker-compose up -d
```

## Health Checks

All services include health checks. You can verify them:

```bash
# Check all services
docker-compose ps

# Manual health checks
curl http://localhost:8000/api/v1/heartbeat  # ChromaDB
curl http://localhost:3000/api/public/health  # Langfuse
docker-compose exec postgres pg_isready -U postgres  # PostgreSQL
```
