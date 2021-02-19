from dataclasses import dataclass
from typing import Optional


@dataclass
class Recipe:
    name: str
    recipe_type: str
    requires_disk_space: bool
    trigger_type: str
    trigger_details: Optional[str]

    def create(self):
        print("Created recipe!")
