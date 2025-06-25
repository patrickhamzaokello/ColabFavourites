from pydantic_settings import BaseSettings
from typing import Optional
import os
from functools import lru_cache

class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "MW Music Recommender API"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Database Settings
    db_host: str
    db_user: str 
    db_password: str
    db_name: str
    db_port: int = 3306
    
    # Recommendation Engine Settings
    default_k_neighbors: int = 10
    max_k_neighbors: int = 50
    default_recommendations: int = 10
    max_recommendations: int = 100
    
    # Cache Settings
    cache_ttl: int = 3600  # 1 hour
    enable_caching: bool = True
    
    # Logging Settings
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Security Settings
    api_key: Optional[str] = None
    cors_origins: list = ["*"]
    
    # Model Settings
    svd_components: int = 20
    svd_iterations: int = 10
    bayesian_confidence_weight: float = 10.0
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        
        # For Google Colab userdata compatibility
        @classmethod
        def customise_sources(cls, init_settings, env_settings, file_secret_settings):
            return (
                init_settings,
                colab_userdata_settings,
                env_settings,
                file_secret_settings,
            )

def colab_userdata_settings(settings: BaseSettings) -> dict:
    """Load settings from Google Colab userdata if available"""
    try:
        from google.colab import userdata
        return {
            'db_host': userdata.get('mwonyaDBHost'),
            'db_user': userdata.get('mwonyaDBUser'),
            'db_password': userdata.get('mwonyaDBPassword'),
            'db_name': userdata.get('mwonyaDB')
        }
    except ImportError:
        # Not in Colab environment, return empty dict
        return {}
    except Exception:
        # userdata not available or keys don't exist
        return {}

@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()

# Environment-specific configurations
class DevelopmentSettings(Settings):
    debug: bool = True
    log_level: str = "DEBUG"

class ProductionSettings(Settings):
    debug: bool = False
    log_level: str = "WARNING"
    enable_caching: bool = True

class TestingSettings(Settings):
    debug: bool = True
    log_level: str = "DEBUG"
    # Use test database settings
    db_name: str = "test_mwonya"

def get_settings_for_env(env: str = None) -> Settings:
    """Get settings based on environment"""
    env = env or os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return ProductionSettings()
    elif env == "testing":
        return TestingSettings()
    else:
        return DevelopmentSettings()