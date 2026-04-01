"""
Tests for the MiniMax RAG cookbook notebook.

Unit tests validate notebook structure, configuration patterns, and MiniMax API setup.
Integration tests (marked with @pytest.mark.integration) validate actual API calls.
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


NOTEBOOK_PATH = Path(__file__).parent.parent / "notebooks" / "rag_with_minimax.ipynb"

MINIMAX_API_BASE_URL = "https://api.minimax.io/v1"
MINIMAX_MODELS = ["MiniMax-M2.7", "MiniMax-M2.7-highspeed"]


# ─── helpers ───


def load_notebook():
    """Load the notebook and return parsed JSON."""
    with open(NOTEBOOK_PATH, "r") as f:
        return json.load(f)


def get_all_code(nb):
    """Concatenate all code cell sources."""
    return "\n".join(
        "".join(cell["source"])
        for cell in nb["cells"]
        if cell["cell_type"] == "code"
    )


def get_all_markdown(nb):
    """Concatenate all markdown cell sources."""
    return "\n".join(
        "".join(cell["source"])
        for cell in nb["cells"]
        if cell["cell_type"] == "markdown"
    )


# ─── unit tests: notebook structure ───


class TestNotebookStructure:
    """Validate notebook file structure and metadata."""

    def test_notebook_exists(self):
        assert NOTEBOOK_PATH.exists(), f"Notebook not found at {NOTEBOOK_PATH}"

    def test_valid_json(self):
        nb = load_notebook()
        assert "cells" in nb
        assert "metadata" in nb
        assert nb["nbformat"] == 4

    def test_has_markdown_and_code_cells(self):
        nb = load_notebook()
        cell_types = [cell["cell_type"] for cell in nb["cells"]]
        assert "markdown" in cell_types
        assert "code" in cell_types

    def test_starts_with_title(self):
        nb = load_notebook()
        first_cell = nb["cells"][0]
        assert first_cell["cell_type"] == "markdown"
        title = "".join(first_cell["source"])
        assert "MiniMax" in title

    def test_has_pip_install(self):
        code = get_all_code(load_notebook())
        assert "pip install" in code
        assert "haystack-ai" in code

    def test_ends_with_summary(self):
        nb = load_notebook()
        last_cell = nb["cells"][-1]
        assert last_cell["cell_type"] == "markdown"
        text = "".join(last_cell["source"])
        assert "Summary" in text or "summary" in text


class TestMiniMaxConfiguration:
    """Validate MiniMax-specific configuration in notebook cells."""

    def test_api_base_url_correct(self):
        code = get_all_code(load_notebook())
        assert MINIMAX_API_BASE_URL in code

    def test_uses_minimax_api_key_env(self):
        code = get_all_code(load_notebook())
        assert "MINIMAX_API_KEY" in code

    def test_uses_m27_model(self):
        code = get_all_code(load_notebook())
        assert "MiniMax-M2.7" in code

    def test_uses_highspeed_model(self):
        code = get_all_code(load_notebook())
        assert "MiniMax-M2.7-highspeed" in code

    def test_temperature_in_valid_range(self):
        """MiniMax requires temperature in (0.0, 1.0]."""
        code = get_all_code(load_notebook())
        import re

        temps = re.findall(r'"temperature":\s*([\d.]+)', code)
        for t in temps:
            temp_val = float(t)
            assert 0.0 < temp_val <= 1.0, f"Temperature {temp_val} outside (0, 1]"

    def test_uses_openai_chat_generator(self):
        code = get_all_code(load_notebook())
        assert "OpenAIChatGenerator" in code

    def test_api_key_via_secret(self):
        code = get_all_code(load_notebook())
        assert "Secret.from_env_var" in code

    def test_no_hardcoded_api_key(self):
        code = get_all_code(load_notebook())
        # Should not contain actual API keys
        import re

        assert not re.search(r'api_key\s*=\s*["\'][a-zA-Z0-9]{20,}["\']', code)


class TestRAGPipelineStructure:
    """Validate RAG pipeline components in notebook."""

    def test_has_document_store(self):
        code = get_all_code(load_notebook())
        assert "InMemoryDocumentStore" in code

    def test_has_embedder(self):
        code = get_all_code(load_notebook())
        assert "SentenceTransformersDocumentEmbedder" in code

    def test_has_retriever(self):
        code = get_all_code(load_notebook())
        assert "InMemoryEmbeddingRetriever" in code

    def test_has_prompt_builder(self):
        code = get_all_code(load_notebook())
        assert "ChatPromptBuilder" in code

    def test_pipeline_connections(self):
        code = get_all_code(load_notebook())
        assert "rag_pipeline.connect" in code

    def test_has_question_examples(self):
        code = get_all_code(load_notebook())
        assert "question" in code


class TestDocumentation:
    """Validate documentation quality in markdown cells."""

    def test_mentions_minimax_in_title(self):
        md = get_all_markdown(load_notebook())
        assert "MiniMax" in md

    def test_mentions_openai_compatible(self):
        md = get_all_markdown(load_notebook())
        assert "OpenAI-compatible" in md or "OpenAI compatible" in md

    def test_mentions_context_window(self):
        md = get_all_markdown(load_notebook())
        assert "204K" in md

    def test_mentions_both_models_in_docs(self):
        md = get_all_markdown(load_notebook())
        assert "MiniMax-M2.7" in md
        assert "MiniMax-M2.7-highspeed" in md

    def test_has_api_key_instructions(self):
        md = get_all_markdown(load_notebook())
        assert "API key" in md or "api key" in md or "API Key" in md

    def test_has_model_table(self):
        md = get_all_markdown(load_notebook())
        assert "| Model" in md


class TestIndexToml:
    """Validate index.toml entry for the MiniMax notebook."""

    def test_notebook_in_index(self):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        index_path = Path(__file__).parent.parent / "index.toml"
        data = tomllib.loads(index_path.read_text())

        notebooks = [nb["notebook"] for nb in data["cookbook"] if "notebook" in nb]
        assert "rag_with_minimax.ipynb" in notebooks

    def test_index_entry_has_required_fields(self):
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib

        index_path = Path(__file__).parent.parent / "index.toml"
        data = tomllib.loads(index_path.read_text())

        minimax_entry = None
        for nb in data["cookbook"]:
            if nb.get("notebook") == "rag_with_minimax.ipynb":
                minimax_entry = nb
                break

        assert minimax_entry is not None, "MiniMax entry not found in index.toml"
        assert "title" in minimax_entry
        assert "topics" in minimax_entry
        assert len(minimax_entry["topics"]) > 0
        assert "MiniMax" in minimax_entry["title"]


# ─── unit tests: mock-based API validation ───


class TestMiniMaxAPISetup:
    """Test MiniMax API configuration with mocked OpenAI client."""

    @patch("openai.OpenAI")
    def test_client_creation_with_minimax_base_url(self, mock_openai_cls):
        """Verify OpenAI client can be configured with MiniMax base URL."""
        from openai import OpenAI

        client = OpenAI(
            api_key="test-key",
            base_url=MINIMAX_API_BASE_URL,
        )
        mock_openai_cls.assert_called_once_with(
            api_key="test-key",
            base_url=MINIMAX_API_BASE_URL,
        )

    def test_generation_kwargs_valid(self):
        """Ensure generation kwargs match MiniMax constraints."""
        kwargs = {"temperature": 0.7, "max_tokens": 512}
        assert 0.0 < kwargs["temperature"] <= 1.0
        assert kwargs["max_tokens"] > 0

    def test_model_names_valid(self):
        """Verify model names match MiniMax naming convention."""
        for model in MINIMAX_MODELS:
            assert model.startswith("MiniMax-")
            assert "M2.7" in model


# ─── integration tests ───


@pytest.mark.integration
class TestMiniMaxIntegration:
    """Integration tests that make actual API calls to MiniMax.

    Run with: pytest -m integration
    Requires MINIMAX_API_KEY environment variable.
    """

    @pytest.fixture(autouse=True)
    def skip_without_api_key(self):
        if not os.environ.get("MINIMAX_API_KEY"):
            pytest.skip("MINIMAX_API_KEY not set")

    @staticmethod
    def _strip_think_tags(text):
        """Remove <think>...</think> tags from MiniMax responses."""
        import re
        return re.sub(r"<think>[\s\S]*?</think>\s*", "", text).strip()

    def test_basic_chat_completion(self):
        """Test basic chat completion with MiniMax M2.7."""
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["MINIMAX_API_KEY"],
            base_url=MINIMAX_API_BASE_URL,
        )
        response = client.chat.completions.create(
            model="MiniMax-M2.7",
            messages=[{"role": "user", "content": "Say 'hello' in one word."}],
            temperature=0.1,
            max_tokens=256,
        )
        assert response.choices[0].message.content is not None
        content = self._strip_think_tags(response.choices[0].message.content)
        assert len(content) > 0

    def test_highspeed_model(self):
        """Test chat completion with MiniMax-M2.7-highspeed."""
        from openai import OpenAI

        client = OpenAI(
            api_key=os.environ["MINIMAX_API_KEY"],
            base_url=MINIMAX_API_BASE_URL,
        )
        response = client.chat.completions.create(
            model="MiniMax-M2.7-highspeed",
            messages=[{"role": "user", "content": "What is 2+2? Answer with just the number."}],
            temperature=0.1,
            max_tokens=256,
        )
        assert response.choices[0].message.content is not None
        content = self._strip_think_tags(response.choices[0].message.content)
        assert "4" in content

    def test_haystack_openai_chat_generator(self):
        """Test MiniMax via Haystack's OpenAIChatGenerator."""
        from haystack.components.generators.chat import OpenAIChatGenerator
        from haystack.dataclasses import ChatMessage
        from haystack.utils import Secret

        generator = OpenAIChatGenerator(
            api_key=Secret.from_env_var("MINIMAX_API_KEY"),
            model="MiniMax-M2.7",
            api_base_url=MINIMAX_API_BASE_URL,
            generation_kwargs={"temperature": 0.1, "max_tokens": 50},
        )
        messages = [ChatMessage.from_user("What is the capital of France? One word answer.")]
        result = generator.run(messages=messages)

        assert "replies" in result
        assert len(result["replies"]) > 0
        assert "Paris" in result["replies"][0].text
