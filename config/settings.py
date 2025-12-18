import os 
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel
from typing import List, Optional 

ROOT_DIR = Path(__file__).parent.parent
load_dotenv(ROOT_DIR / ".env")

class DatabaseSettings(BaseModel):
    server: str = os.getenv("DB_SERVER", "localhost")
    name: str = os.getenv("DB_NAME", "trading_db")
    driver: str = os.getenv("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    user: Optional[str] = os.getenv("DB_USER") or None
    password: Optional[str] = os.getenv("DB_PASSWORD") or None

    @property
    def connection_string(self) -> str:
        if self.user and self.password:
            return (
                f"mssql+pyodbc://{self.user}:{self.password}@{self.server}/{self.name}"
                f"?driver={self.driver.replace(' ', '+')}"
            )
        else:
            return (
                f"mssql+pyodbc://@{self.server}/{self.name}"
                f"?driver={self.driver.replace(' ', '+')}&Trusted_Connection=yes"
            )


class HyperliquidSettings(BaseModel):
    testnet: bool = os.getenv("HL_TESTNET", "true").lower() == "true"
    account_address: str = os.getenv("HL_ACCOUNT_ADDRESS", "")
    private_key: str = os.getenv("HL_PRIVATE_KEY", "")

    @property
    def base_url(self) -> str:
        if self.testnet:
            return "https://api.hyperliquid-testnet.xyz"
        return "https://api.hyperliquid.xyz"


class TradingSettings(BaseModel):
    max_position_size_pct: float = float(os.getenv("MAX_POSITION_SIZE_PCT", "20"))
    max_total_exposure_pct: float = float(os.getenv("MAX_TOTAL_EXPOSURE_PCT", "50"))
    max_daily_loss_pct: float = float(os.getenv("MAX_DAILY_LOSS_PCT", "5"))
    default_leverage: int = int(os.getenv("DEFAULT_LEVERAGE", "3"))
    default_slippage: float = float(os.getenv("DEFAULT_SLIPPAGE", "0.01"))
    trading_coins: List[str] = os.getenv("TRADING_COINS", "BTC,ETH,SOL").split(",")


class Settings(BaseModel):
    database: DatabaseSettings = DatabaseSettings()
    hyperliquid: HyperliquidSettings = HyperliquidSettings()
    trading: TradingSettings = TradingSettings()
    root_dir: Path = ROOT_DIR


settings = Settings()

if __name__ == "__main__":
    print(f"DB: {settings.database.connection_string}")
    print(f"HL Testnet: {settings.hyperliquid.testnet}")