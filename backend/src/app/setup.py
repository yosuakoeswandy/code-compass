import os
from dotenv import load_dotenv
from llama_index.core import Settings
from llama_index.llms.azure_openai import AzureOpenAI

from custom_embedding import CustomAzureOpenAICodeEmbedding


def setup_llama_index():
    load_dotenv()
    api_key = os.getenv("AZURE_OPEN_AI_KEY")
    azure_endpoint = os.getenv("AZURE_OPEN_AI_ENDPOINT")
    api_version = os.getenv("AZURE_OPEN_AI_API_VERSION")

    llm = AzureOpenAI(
        model="gpt-4o-mini",
        deployment_name="gpt-4o-mini",
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
    )

    embed_model = CustomAzureOpenAICodeEmbedding(
        llm=llm,
        model="text-embedding-3-small",
        deployment_name="text-embedding-3-small",
        dimensions=1536,
        api_key=api_key,
        azure_endpoint=azure_endpoint,
        api_version=api_version,
    )

    Settings.llm = llm
    Settings.embed_model = embed_model
