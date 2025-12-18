# Nexus-Mind: Multi-Agent Corporate Knowledge System

Nexus-Mind is a proof-of-concept multi-agent system designed to act as an intelligent "Corporate Brain." It autonomously routes user queries to specialized agents (HR, Technical Support), retrieves relevant policy or documentation, and validates responses through an independent auditor agent.

## 🚀 Key Features

*   **Intelligent Routing:** A Dispatcher Agent analyzes user intent to route queries to the correct department (HR vs. Engineering).
*   **Specialized RAG:** Domain-specific agents equipped with Retrieval Augmented Generation (RAG) to fetch accurate information from internal documents.
*   **Audit & Safety:** A dedicated Auditor Agent reviews every response for tone, safety, and compliance before it reaches the user.
*   **Traceability:** Full observability integrated via Langfuse.

## 🏗 Architecture

The system follows a **Hierarchical Delegation** pattern:

1.  **User Input** -> **Dispatcher Agent** (Brain)
2.  **Dispatcher** -> **Specialist Agent** (HR or Tech)
3.  **Specialist** -> **Vector Store** (ChromaDB) -> **Draft Response**
4.  **Draft Response** -> **Auditor Agent** (Reviewer) -> **Final Output**

### Tech Stack

*   **LangChain:** Orchestration framework.
*   **ChromaDB:** Local vector store for document embeddings.
*   **OpenAI GPT-4o:** LLM backbone.
*   **Pydantic:** Data validation and structured output.
*   **Langfuse:** Observability and tracing.

## 🛠 Setup & Installation

1.  **Clone the Repository**
    ```bash
    git clone <repo-url>
    cd henry-capstone
    ```

2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Environment Variables**
    Copy `.env.example` to `.env` and fill in your keys:
    ```bash
    cp .env.example .env
    ```
    Required keys:
    *   `OPENAI_API_KEY`
    *   `LANGFUSE_PUBLIC_KEY` (Optional)
    *   `LANGFUSE_SECRET_KEY` (Optional)

4.  **Start Docker Services**
    Ensure you have Docker and Docker Compose installed.
    ```bash
    docker-compose up -d
    ```
    This will start ChromaDB (port 8000) and Langfuse.

5.  **Prepare Data**
    Place your `.txt` or `.pdf` policy documents in the `data/` directory. (Sample data is provided).

## 🏃 Usage

Run the CLI application:

```bash
python3 src/main.py
```

### Example Interaction

**User:** "How do I report harassment?"
**System:**
> *Dispatcher identifies 'HR' intent.*
> *HR Specialist retrieves 'Harassment Policy'.*
> *Auditor confirms professional tone.*
> **Nexus Response:** "Per our Zero Tolerance Policy, all harassment incidents should be reported immediately to hr@nexus.com or via the anonymous portal. Substantiated claims result in termination."

**User:** "How do I rotate API keys?"
**System:**
> *Dispatcher identifies 'TECH' intent.*
> *Tech Specialist retrieves 'Key Rotation Guide'.*
> **Nexus Response:** "Run `npm run rotate-keys --service=<service_name>` in the ops-cli repository. Keys must be rotated every 90 days."

## 🧠 Design Decisions

*   **Why Multi-Agent?** Single-prompt systems often confuse context (e.g., applying HR tone to code snippets). Separating concerns allows us to optimize prompts for each domain.
*   **Auditor Pattern:** We specifically added an Auditor to prevent "hallucinations" and ensure corporate compliance, mimicking real-world managerial review steps.
*   **Pydantic:** Used to enforce strict contracts between agents, preventing "chatty" failures where agents output unstructured text instead of actionable data.

## 📂 Project Structure

*   `src/server/agents/`: Individual agent implementations.
*   `src/server/models/`: Pydantic schemas.
*   `src/server/utils/`: Vector store and helper logic.
*   `data/`: Knowledge base documents.
*   `docs/`: Detailed proposal and architecture docs.