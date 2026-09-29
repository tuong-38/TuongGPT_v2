import os
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, MessagesState
from langgraph.prebuilt import ToolNode, tools_condition
from tools import tools

# Mặc định sử dụng gemini-3.7-flash
DEFAULT_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")

ALLOWED_MODELS = {
    "gemini-3.5-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
}

SYSTEM_PROMPT = """
You are a helpful Agentic AI assistant named TuongGPT, similar to ChatGPT.

Language & Tone Guidelines:
- Always detect and respond in the same language used by the user.
- Primarily prioritize and excel in Vietnamese and English.
- If the user asks in Vietnamese, reply in natural, fluent Vietnamese.
- If the user asks in English, reply in natural, clear English.

Formatting & Mathematical Guidelines:
- Format all mathematical and scientific formulas strictly in standard LaTeX:
  * Use $inline$ for formulas within text (e.g., $a$, $E = mc^2$).
  * Use $$display$$ for standalone formulas and complex equations.
- Never omit the dollar signs ($) or use bracket notations like \( \) or \[ \].
- Provide clear, thorough, and step-by-step explanations for complex problems. Avoid cutting off explanations prematurely.

You can:
1. Answer normal questions in depth.
2. Use tools when needed.
3. Search uploaded documents using the RAG tool.
4. Search the web for latest/current information using Tavily Search.
5. Remember important user information using the memory tool.
6. Recall memory when useful.
7. Use calculator for math.

Rules:
- If the user asks about latest news, current events, recent updates, today's information, current price, use web_search.
- If the user asks about an uploaded document, use search_uploaded_documents.
- If the user asks you to remember something, use remember_this.
- If the user asks about previous preferences or saved facts, use recall_memory.
- Use calculator for math questions.
- When using web search, summarize clearly and mention that the answer is based on web search results.
"""

def normalize_model_name(model_name: str | None) -> str:
    if not model_name:
        return DEFAULT_MODEL
    model_name = model_name.strip()
    if model_name not in ALLOWED_MODELS:
        return DEFAULT_MODEL
    return model_name


def build_agent(model_name: str):
    selected_model = normalize_model_name(model_name)

    llm = ChatGoogleGenerativeAI(
        model=selected_model,
        google_api_key=os.getenv("GOOGLE_API_KEY"),
        temperature=0.3,
        max_output_tokens=4096,
        streaming=True
    )

    llm_with_tools = llm.bind_tools(tools)

    def chatbot_node(state: MessagesState):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    tool_node = ToolNode(tools)

    workflow = StateGraph(MessagesState)
    workflow.add_node("chatbot", chatbot_node)
    workflow.add_node("tools", tool_node)

    workflow.add_edge(START, "chatbot")
    workflow.add_conditional_edges("chatbot", tools_condition)
    workflow.add_edge("tools", "chatbot")

    # Biên dịch đồ thị Agent (Trạng thái và lịch sử tin nhắn đã được lưu bền vững qua Supabase PostgreSQL)
    return workflow.compile()


_AGENT_CACHE = {}

def get_agent(model_name: str | None = None):
    selected_model = normalize_model_name(model_name)
    if selected_model not in _AGENT_CACHE:
        _AGENT_CACHE[selected_model] = build_agent(selected_model)
    return _AGENT_CACHE[selected_model]