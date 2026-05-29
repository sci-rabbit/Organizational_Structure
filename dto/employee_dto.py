from dataclasses import dataclass
from datetime import date


@dataclass
class CreateEmployeeDto:
    full_name: str
    position: str
    hired_at: date | None
