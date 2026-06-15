# backend/app/tools/documents/__init__.py

from .search_document import search_document_tool
from .summarize_document import summarize_document_tool
from .extract_table import extract_table_tool
from .compare_documents import compare_documents_tool
from .ask_document import ask_document_tool

# Danh sách tools của Document Agent
documents_tools_list = [
    search_document_tool,
    summarize_document_tool,
    extract_table_tool,
    compare_documents_tool,
    ask_document_tool,
]

__all__ = [
    "search_document_tool",
    "summarize_document_tool",
    "extract_table_tool",
    "compare_documents_tool",
    "ask_document_tool",
    "documents_tools_list",
]