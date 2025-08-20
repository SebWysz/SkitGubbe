# Configuration settings (simplified) for the sticks strategy competition

import os
from dataclasses import dataclass
from typing import Optional

# New minimal settings surface used by active code.
@dataclass(frozen=True)
class Settings:
    strategies_dir: str = os.getenv('SKIT_STRATEGIES_DIR', 'strategies')
    time_limit_ms: int = int(os.getenv('TIME_LIMIT_MS', '50'))
    default_games: int = int(os.getenv('TOURNAMENT_GAMES', '20'))
    singlestore_uri: Optional[str] = os.getenv('SINGLESTORE_URI')
    force_db: bool = os.getenv('SKIT_FORCE_DB') == '1'
    auto_load_dotenv: bool = os.getenv('SKIT_AUTO_LOAD_DOTENV', '1') == '1'

# Singleton instance accessed by modules that adopt the new interface.
SETTINGS = Settings()

# Helper (optional): provide backward compatible accessor.
def get_settings() -> Settings:
    return SETTINGS