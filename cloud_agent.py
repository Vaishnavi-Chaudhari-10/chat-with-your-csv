import os
import streamlit as st
from groq import Groq
from typing import TypedDict, Optional
from langgraph.graph import StateGraph, START, END

from database import get_schema_text, execute_query
from sql_validator import validate_sql


MODEL = "openai/gpt-oss-20b"


class AgentState(TypedDict):
    question: str
    schema: Optional[str]
    sql: Optional[str]
    result: Optional[dict]
    error: Optional[str]


def generate_sql(schema, question):

    api_key = st.secrets.get(
        "GROQ_API_KEY",
        os.getenv("GROQ_API_KEY")
    )

    if not api_key:
        raise ValueError("Groq API key is not configured.")

    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an expert SQLite assistant. "
                    "Generate exactly one correct SELECT query using "
                    "only the tables and columns in the supplied schema. "
                    "Understand the requested operation carefully. "
                    "Do not add conditions that the user did not request. "
                    "Return only SQL without explanations or Markdown."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Database Schema:\n{schema}\n\n"
                    f"Question:\n{question}"
                )
            }
        ],
        temperature=0
    )

    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()

    return sql


def build_agent(connection):

    def inspect_node(state):
        return {"schema": get_schema_text(connection)}

    def generate_node(state):
        sql = generate_sql(
            state["schema"],
            state["question"]
        )
        return {"sql": sql}

    def validate_node(state):
        validated_sql = validate_sql(state["sql"])
        return {"sql": validated_sql}

    def execute_node(state):
        df = execute_query(connection, state["sql"])

        return {
            "result": {
                "columns": list(df.columns),
                "rows": df.to_dict(orient="records")
            }
        }

    workflow = StateGraph(AgentState)

    workflow.add_node("inspect_schema", inspect_node)
    workflow.add_node("generate_sql", generate_node)
    workflow.add_node("validate_sql", validate_node)
    workflow.add_node("execute_sql", execute_node)

    workflow.add_edge(START, "inspect_schema")
    workflow.add_edge("inspect_schema", "generate_sql")
    workflow.add_edge("generate_sql", "validate_sql")
    workflow.add_edge("validate_sql", "execute_sql")
    workflow.add_edge("execute_sql", END)

    return workflow.compile()


def run_agent(agent, question):

    initial_state = {
        "question": question,
        "schema": None,
        "sql": None,
        "result": None,
        "error": None
    }

    try:
        return agent.invoke(initial_state)

    except Exception as e:
        return {
            **initial_state,
            "error": str(e)
        }
