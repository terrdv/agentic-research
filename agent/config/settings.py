import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"

    # Ollama (local)
    ollama_model: str = "llama3.2"

    # LangSmith (optional tracing)
    langsmith_api_key: str = ""
    langchain_project: str = "agentic-research"
    langchain_tracing_v2: bool = False

    # Unpaywall (open-access PDF discovery for full-text fetching).
    # Requires a real email for the API; leave blank to disable OA lookup.
    unpaywall_email: str = ""

    def configure_tracing(self) -> None:
        """Export LangSmith config to the process env so LangChain picks it up.

        LangChain/LangGraph reads tracing settings from environment variables at
        runtime, not from this object, so we mirror them into os.environ.
        """
        if not (self.langchain_tracing_v2 and self.langsmith_api_key):
            return
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = self.langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = self.langchain_project
        os.environ.setdefault("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")


settings = Settings()
settings.configure_tracing()
