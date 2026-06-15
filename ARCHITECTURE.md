# Odoo AI Assistant - Architecture Diagram

## Tổng quan hệ thống

```mermaid
graph TD
    subgraph "Frontend"
        UI[Next.js 14 UI + Streaming Chat]
        PDF[PDF Report + Email]
    end

    subgraph "Backend - FastAPI"
        API[API Routers]
        Auth[Authentication JWT]
    end

    subgraph "AI Core - LangGraph"
        Supervisor[Supervisor Agent]
        State[Agent State + Memory]
        ToolsNode[Tools Node]
        ConfirmNode[Confirm Node\n(Human-in-the-Loop)]
    end

    subgraph "Tools"
        CreateInvoice[Create Invoice Tool]
        SalesReport[Sales Report]
        LowStock[Low Stock]
        SearchKnowledge[Search Company Knowledge]
        GetOrder[Get Sale Order Detail]
        SearchProduct[Search Products]
    end

    subgraph "Odoo Layer"
        OdooRepo[OdooRepository]
        OdooDB[(Odoo 17)]
    end

    subgraph "RAG Pipeline"
        Ingestor[Data Ingestor]
        VectorStore[PGVector]
        AdvancedRAG[AdvancedRAG\nHyDE + Reranker]
    end

    UI --> API
    API --> Supervisor
    Supervisor --> ToolsNode
    ToolsNode --> Tools
    Tools --> OdooRepo
    Tools --> SearchKnowledge
    SearchKnowledge --> AdvancedRAG
    AdvancedRAG --> VectorStore
    Ingestor --> VectorStore
    Supervisor --> ConfirmNode
    OdooRepo --> OdooDB
    Tools --> Groq[Groq LLM]
    State --> Postgres[(PostgreSQL Checkpoint)]