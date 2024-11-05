import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class ClientConfig:
    model: str
    base_url: Optional[str] = ""
    api_key: Optional[str] = ""
    temperature: Optional[float] = 0.2
    price_1k_token_in: Optional[int] = 0
    price_1k_token_out: Optional[int] = 0
    ext: Optional[Dict[str, str]] = None
