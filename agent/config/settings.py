from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Anthropic
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-sonnet-4-6"

    # Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # Ollama (local)
    ollama_model: str = "llama3.2"

    # UBC Library Summon API
    ubc_summon_id: str = ""
    ubc_summon_key: str = ""

    # API server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False

    # LangSmith (optional tracing)
    langsmith_api_key: str = ""
    langchain_project: str = "agentic-research"
    langchain_tracing_v2: bool = False


settings = Settings()
