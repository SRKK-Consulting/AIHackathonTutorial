import chainlit as cl
from langchain_openai import AzureChatOpenAI
from typing import Annotated, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# Azure OpenAI configuration
AZURE_OPENAI_API_KEY = "1K0e89sz1shcTcFl9fsZXPv5OM1pxCVOGBccLfCCHOtLffA2tv02JQQJ99BGACi0881XJ3w3AAAAACOGwzRS"
AZURE_OPENAI_ENDPOINT = "https://foundry1234.cognitiveservices.azure.com/"
AZURE_OPENAI_DEPLOYMENT = "o4-mini"
AZURE_OPENAI_API_VERSION = "2024-12-01-preview"

# Initialize AzureChatOpenAI
llm = AzureChatOpenAI(
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_key=AZURE_OPENAI_API_KEY,
    azure_deployment=AZURE_OPENAI_DEPLOYMENT,
    api_version=AZURE_OPENAI_API_VERSION,
)

class MessageClassifier(BaseModel):
    message_type: Literal["emotional", "logical"] = Field(
        ...,
        description="Classify if the message requires an emotional (therapist) or logical response."
    )

class State(TypedDict):
    messages: Annotated[list, add_messages]
    message_type: str | None

def classify_message(state: State):
    last_message = state["messages"][-1]
    classifier_llm = llm.with_structured_output(MessageClassifier)

    result = classifier_llm.invoke([
        {
            "role": "system",
            "content": """Classify the user message as either:
            - 'emotional': if it asks for emotional support, therapy, deals with feelings, or personal problems
            - 'logical': if it asks for facts, information, logical analysis, or practical solutions
            """
        },
        {"role": "user", "content": last_message.content}
    ])
    return {"message_type": result.message_type}

def router(state: State):
    message_type = state.get("message_type", "logical")
    if message_type == "emotional":
        return {"next": "therapist"}
    return {"next": "logical"}

def therapist_agent(state: State):
    last_message = state["messages"][-1]

    messages = [
        {"role": "system",
         "content": """You are a compassionate therapist. Focus on the emotional aspects of the user's message.
                        Show empathy, validate their feelings, and help them process their emotions.
                        Ask thoughtful questions to help them explore their feelings more deeply.
                        Avoid giving logical solutions unless explicitly asked."""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}

def logical_agent(state: State):
    last_message = state["messages"][-1]

    messages = [
        {"role": "system",
         "content": """You are a purely logical assistant. Focus only on facts and information.
            Provide clear, concise answers based on logic and evidence.
            Do not address emotions or provide emotional support.
            Be direct and straightforward in your responses."""
         },
        {
            "role": "user",
            "content": last_message.content
        }
    ]
    reply = llm.invoke(messages)
    return {"messages": [{"role": "assistant", "content": reply.content}]}

# Build the graph
graph_builder = StateGraph(State)
graph_builder.add_node("classifier", classify_message)
graph_builder.add_node("router", router)
graph_builder.add_node("therapist", therapist_agent)
graph_builder.add_node("logical", logical_agent)
graph_builder.add_edge(START, "classifier")
graph_builder.add_edge("classifier", "router")
graph_builder.add_conditional_edges(
    "router",
    lambda state: state.get("next"),
    {"therapist": "therapist", "logical": "logical"}
)
graph_builder.add_edge("therapist", END)
graph_builder.add_edge("logical", END)
graph = graph_builder.compile()

@cl.on_chat_start
async def on_chat_start():
    cl.user_session.set("state", {
        "messages": [],
        "message_type": None
    })
    await cl.Message(content="Welcome! How can I assist you today?").send()

@cl.on_message
async def on_message(message: cl.Message):
    state = cl.user_session.get("state")
    state["messages"] = state.get("messages", []) + [
        {"role": "user", "content": message.content}
    ]

    state = graph.invoke(state)
    cl.user_session.set("state", state)

    if state.get("messages") and len(state["messages"]) > 0:
        last_message = state["messages"][-1]
        await cl.Message(content=last_message.content).send()

# if __name__ == "__main__":
# 	# Chainlit will automatically run the application
# 	pass