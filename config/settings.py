"""Centralized Configuration System for KritiAI."""
from enum import Enum
from pathlib import Path
from typing import Optional
import json
import os
from pydantic import BaseModel, Field


class PowerMode(str, Enum):
    """The three primary KritiAI autonomy power modes."""
    SAFE = "safe"
    AUTONOMOUS = "autonomous"
    RISK = "risk"


class GranularPermissions(BaseModel):
    """Fine-grained permission controls evaluated by the Policy Engine."""
    allow_internet: bool = True
    allow_browser: bool = True
    allow_filesystem: bool = True
    allow_terminal: bool = True
    allow_powershell: bool = True
    allow_application_control: bool = True
    allow_keyboard_mouse: bool = False
    allow_git: bool = True
    allow_github: bool = True
    allow_software_installation: bool = False
    allow_public_publishing: bool = False
    allow_deployment: bool = False
    allow_external_apis: bool = True


class ModelSelection(BaseModel):
    """Configured model overrides and routing preferences."""
    general_model: str = "auto"
    coding_model: str = "auto"
    reasoning_model: str = "auto"
    vision_model: str = "auto"
    embedding_model: str = "auto"
    prefer_local: bool = True
    ollama_endpoint: str = "http://localhost:11434"
    openai_api_key: Optional[str] = None
    openai_base_url: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    
    # Priority weighting for automatic routing (0 - 100)
    priority_quality: int = 80
    priority_speed: int = 60
    priority_cost: int = 90
    priority_privacy: int = 100


class PrivacySettings(BaseModel):
    """Privacy guardrails for local-first execution."""
    prefer_local_models: bool = True
    never_send_local_files_to_cloud: bool = False
    ask_before_cloud_processing: bool = False


class AppConfig(BaseModel):
    """Top-level KritiAI configuration."""
    app_name: str = "KritiAI"
    version: str = "0.1.0"
    power_mode: PowerMode = PowerMode.AUTONOMOUS
    permissions: GranularPermissions = Field(default_factory=GranularPermissions)
    models: ModelSelection = Field(default_factory=ModelSelection)
    privacy: PrivacySettings = Field(default_factory=PrivacySettings)
    
    # Storage and paths
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".kritiai")
    workspace_dir: Path = Field(default_factory=lambda: Path.cwd())
    db_name: str = "kritiai.db"
    
    # Server configuration
    host: str = "127.0.0.1"
    port: int = 8765
    
    # Task execution defaults
    max_retries: int = 3
    default_tool_timeout: int = 60
    emergency_stop_active: bool = False

    @property
    def db_path(self) -> Path:
        return self.data_dir / self.db_name

    def ensure_directories(self) -> None:
        """Ensure critical application directories exist."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "logs").mkdir(parents=True, exist_ok=True)
        (self.data_dir / "backups").mkdir(parents=True, exist_ok=True)


_CONFIG_INSTANCE: Optional[AppConfig] = None


def get_default_config() -> AppConfig:
    """Return default configuration."""
    config = AppConfig()
    config.ensure_directories()
    return config


def get_config(reload: bool = False) -> AppConfig:
    """Load or return the singleton application configuration."""
    global _CONFIG_INSTANCE
    if _CONFIG_INSTANCE is not None and not reload:
        return _CONFIG_INSTANCE

    config = get_default_config()
    config_file = config.data_dir / "config.json"
    if config_file.exists():
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                config = AppConfig.model_validate(data)
                config.ensure_directories()
        except Exception:
            # Fall back to default if file is corrupt
            pass

    _CONFIG_INSTANCE = config
    return _CONFIG_INSTANCE


def save_config(config: AppConfig) -> None:
    """Save configuration to disk."""
    global _CONFIG_INSTANCE
    config.ensure_directories()
    config_file = config.data_dir / "config.json"
    with open(config_file, "w", encoding="utf-8") as f:
        f.write(config.model_dump_json(indent=2))
    _CONFIG_INSTANCE = config
