# generator.py

from dotenv import load_dotenv
load_dotenv() # Loaded first

import os # OpenRouter capability
from pathlib import Path
#from langchain_openai import ChatOpenAI # OpenRouter capability
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from src.models import FirmProfile

PROMPT_PATH = Path("prompts/generate_statement.md")

# OPEN ROUTER
# llm = ChatOpenAI(
#     model="anthropic/claude-sonnet-4-6",
#     openai_api_key=os.getenv("OPENROUTER_API_KEY"),
#     openai_api_base="https://openrouter.ai/api/v1",
#     max_tokens=2000
# )

llm = ChatAnthropic(model="claude-sonnet-4-6", max_tokens=2000)

def generate_markdown_capability_statement(firm: FirmProfile) -> str:
    system_prompt =  PROMPT_PATH.read_text(encoding="utf-8")
    user_content = firm.model_dump_json(indent=2)

    response = llm.invoke([
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_content)
            ])

    return response.content