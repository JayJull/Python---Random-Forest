from dataclasses import dataclass, field
from typing import Callable

SendFn = Callable[[str, str], None]


@dataclass
class BusinessData:
    business_name: str = ""
    category:      str = ""
    rating:        float = 0.0
    review_count:  int = 0
    phone:         str = ""
    website:       str = ""
    address:       str = ""
    maps_url:      str = ""


@dataclass
class DatabaseCounter:
    saved:   int = 0
    skipped: int = 0