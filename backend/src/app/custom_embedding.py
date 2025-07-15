from typing import Any, List

from llama_index.embeddings.azure_openai import AzureOpenAIEmbedding
from llama_index.llms.azure_openai import AzureOpenAI
from openai import OpenAI
from pydantic import Field


SUMMARY_PROMPT = "Summarize the following code snippet in one or two concise sentences:"


class CustomAzureOpenAICodeEmbedding(AzureOpenAIEmbedding):
    llm: AzureOpenAI = Field(..., description="AzureOpenAI LLM instance")

    @classmethod
    def class_name(cls) -> str:
        return "CustomAzureOpenAICodeEmbedding"

    def _summarize_code(self, code: str, max_length: int = 200) -> str:
        """
        Generate a short natural language summary of a given code snippet using AzureOpenAI LLM.

        Args:
            code (str): The code snippet to be summarized.
            max_length (int, optional): The maximum characters (approximate) of the summary in characters. Defaults to 200.

        Returns:
            str: A concise natural language summary of the provided code."""
        prompt = f"{SUMMARY_PROMPT}\n\n{code}"
        response = self.llm.complete(
            prompt=prompt,
            max_tokens=max_length // 4,  # rough estimate: 4 chars per token
            temperature=1,
        )
        summary = response.text.strip()
        return summary

    def _get_embedding(
        self, client: OpenAI, text: str, engine: str, **kwargs: Any
    ) -> List[float]:
        """Get embedding from a description + code chunk."""
        text = text.replace("\n", " ")

        description = self._summarize_code(text, max_length=200)

        # Concatenate description and code chunk
        combined = f"{description}\n{text}"
        return (
            client.embeddings.create(input=[combined], model=engine, **kwargs)
            .data[0]
            .embedding
        )

    def _get_embeddings(
        self, client: OpenAI, list_of_text: List[str], engine: str, **kwargs: Any
    ) -> List[List[float]]:
        """Get embeddings from a list of descriptions + code chunks."""
        assert len(list_of_text) <= 2048, (
            "The batch size should not be larger than 2048."
        )

        list_of_text = [text.replace("\n", " ") for text in list_of_text]

        processed_texts = []
        for text in list_of_text:
            description = self._summarize_code(text, max_length=200)
            combined = f"{description}\n{text}"
            processed_texts.append(combined)

        response = client.embeddings.create(
            input=processed_texts, model=engine, **kwargs
        )
        return [item.embedding for item in response.data]

    async def _asummarize_code(self, code: str, max_length: int = 200) -> str:
        """
        Asynchronously generate a short natural language summary of a given code snippet using AzureOpenAI LLM.

        Args:
            code (str): The code snippet to be summarized.
            max_length (int, optional): The maximum characters (approximate) of the summary in characters. Defaults to 200.

        Returns:
            str: A concise natural language summary of the provided code.
        """
        prompt = f"{SUMMARY_PROMPT}\n\n{code}"
        response = await self.llm.acomplete(
            prompt=prompt,
            max_tokens=max_length // 4,  # rough estimate: 4 chars per token
            temperature=1,
        )
        summary = response.text.strip()
        return summary

    async def _aget_embedding(
        self, aclient: OpenAI, text: str, engine: str, **kwargs: Any
    ) -> List[float]:
        """Asynchronously get embedding from a description + code chunk."""
        text = text.replace("\n", " ")

        description = await self._asummarize_code(text, max_length=200)

        # Concatenate description and code chunk
        combined = f"{description}\n{text}"
        response = await aclient.embeddings.create(
            input=[combined], model=engine, **kwargs
        )
        return response.data[0].embedding

    async def _aget_embeddings(
        self, aclient: OpenAI, list_of_text: List[str], engine: str, **kwargs: Any
    ) -> List[List[float]]:
        """Get embeddings from a list of descriptions + code chunks."""
        assert len(list_of_text) <= 2048, (
            "The batch size should not be larger than 2048."
        )

        list_of_text = [text.replace("\n", " ") for text in list_of_text]

        processed_texts = []
        for text in list_of_text:
            description = await self._asummarize_code(text, max_length=200)
            combined = f"{description}\n{text}"
            processed_texts.append(combined)

        response = aclient.embeddings.create(
            input=processed_texts, model=engine, **kwargs
        )
        return [item.embedding for item in response.data]

    def _get_text_embedding(self, text: str) -> List[float]:
        """Get text embedding."""
        client = self._get_client()
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        def _retryable_get_embedding():
            return self._get_embedding(
                client,
                text,
                engine=self._text_engine,
                **self.additional_kwargs,
            )

        return _retryable_get_embedding()

    async def _aget_text_embedding(self, text: str) -> List[float]:
        """Asynchronously get text embedding."""
        aclient = self._get_aclient()
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        async def _retryable_aget_embedding():
            return await self._aget_embedding(
                aclient,
                text,
                engine=self._text_engine,
                **self.additional_kwargs,
            )

        return await _retryable_aget_embedding()

    def _get_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get text embeddings.

        By default, this is a wrapper around _get_text_embedding.
        Can be overridden for batch queries.

        """
        client = self._get_client()
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        def _retryable_get_embeddings():
            return self._get_embeddings(
                client,
                texts,
                engine=self._text_engine,
                **self.additional_kwargs,
            )

        return _retryable_get_embeddings()

    async def _aget_text_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Asynchronously get text embeddings."""
        aclient = self._get_aclient()
        retry_decorator = self._create_retry_decorator()

        @retry_decorator
        async def _retryable_aget_embeddings():
            return await self._aget_embeddings(
                aclient,
                texts,
                engine=self._text_engine,
                **self.additional_kwargs,
            )

        return await _retryable_aget_embeddings()
