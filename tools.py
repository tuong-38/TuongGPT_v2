import math
import os
from dotenv import load_dotenv

from langchain_core.tools import tool
from langchain_core.runnables import RunnableConfig
from langchain_tavily import TavilySearch

from database import save_memory, search_memory
from rag import retrieve_from_rag

load_dotenv()

web_search = TavilySearch(
    max_results=5,
    topic="general",
    search_depth="advanced"
)


@tool
def calculator(expression: str) -> str:
    """
    Useful for simple math calculations.
    Input should be a valid math expression.
    Example: 2 + 2, math.sqrt(16), 10 * 5
    """
    try:
        allowed = {
            "math": math,
            "abs": abs,
            "round": round,
            "min": min,
            "max": max,
            "sum": sum
        }
        result = eval(expression, {"__builtins__": {}}, allowed)
        return str(result)
    except Exception as e:
        return f"Calculation error: {str(e)}"


@tool
def search_uploaded_documents(query: str, config: RunnableConfig) -> str:
    """
    Search uploaded documents for relevant information.
    Use this when the user asks about uploaded PDFs, DOCX, TXT, notes, files, or docs.
    """
    # Lấy thông tin user_id và thread_id từ config do LangGraph inject vào
    user_id = config.get("configurable", {}).get("user_id", "default")
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    return retrieve_from_rag(
        query=query,
        user_id=user_id,
        thread_id=thread_id
    )


@tool
def remember_this(memory: str, config: RunnableConfig) -> str:
    """
    Save an important user preference or fact into long-term memory.
    Use this when the user asks you to remember something.
    """
    user_id = config.get("configurable", {}).get("user_id", "default")
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    return save_memory(
        user_id=user_id,
        thread_id=thread_id,
        memory=memory
    )


@tool
def recall_memory(query: str, config: RunnableConfig) -> str:
    """
    Recall saved long-term memories about the user or this conversation.
    """
    user_id = config.get("configurable", {}).get("user_id", "default")
    thread_id = config.get("configurable", {}).get("thread_id", "default")

    return search_memory(
        user_id=user_id,
        thread_id=thread_id,
        query=query
    )


tools = [
    calculator,
    search_uploaded_documents,
    remember_this,
    recall_memory,
    web_search
]