# helper methods for creating connections to LLM backends.

import langchain
from langchain_google_vertexai import ChatVertexAI
from langchain_openai import ChatOpenAI

def getGemini(project, model=None):
    """returns a langchain callable for gemini-1.5-flash or specified model."""
    if not model:
        model = "gemini-1.5-flash"
    v = ChatVertexAI(
        model=model,
        project=project
    )
    return v

def getCloudRun(endpoint):
    """return a langchain runnable for our Cloud Run-deployed model"""
    v = ChatOpenAI(
        base_url=endpoint,
        api_key="not-actually-used", # type: ignore
    )
    return v
