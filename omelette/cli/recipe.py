import os
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from cookiecutter.main import cookiecutter


class RecipeTypeEnum(Enum):
    AWS_FARGATE = "AWS Fargate"
    AWS_LAMBDA = "AWS Lambda"


class ProgrammingStyleEnum(Enum):
    FUNCTIONAL = "Functional"
    OBJECT_ORIENTED = "Object Oriented (Class)"


@dataclass
class Recipe:
    name: str
    recipe_type: RecipeTypeEnum
    programming_style: ProgrammingStyleEnum
    requires_disk_space: bool
    trigger_type: str
    trigger_details: Optional[str]

    def create(self):
        if self.recipe_type == RecipeTypeEnum.AWS_LAMBDA.value:
            cookiecutter(os.path.join(os.path.dirname(__file__), "templates/recipe/lambda/"),
                         no_input=True,
                         output_dir="./src/recipes/",
                         extra_context={
                             "recipe_name": self.name,
                         })
        else:
            cookiecutter(os.path.join(os.path.dirname(__file__), "templates/recipe/docker/"),
                         no_input=True,
                         output_dir="./src/recipes/",
                         extra_context={
                             "recipe_name": self.name,
                         })

        if self.programming_style == ProgrammingStyleEnum.OBJECT_ORIENTED.value:
            os.remove(f"./src/recipes/{self.name}/functional.py")
            os.rename(f"./src/recipes/{self.name}/object_oriented.py", f"./src/recipes/{self.name}/{self.name}.py")
        else:
            os.remove(f"./src/recipes/{self.name}/object_oriented.py")
            os.rename(f"./src/recipes/{self.name}/functional.py", f"./src/recipes/{self.name}/{self.name}.py")
