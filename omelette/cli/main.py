import os

import questionary
import typer

from cookiecutter.main import cookiecutter
from tomlkit import parse

from omelette.cli.recipe import Recipe, RecipeTypeEnum, ProgrammingStyleEnum
from omelette.cli.validators import validate_underscore_name, validate_schedule_expression

app = typer.Typer()


def get_omelette_version():
    with open(os.path.join(os.path.dirname(__file__), "../../pyproject.toml"), "r") as f:
        data = parse(f.read())

    return data["tool"]["poetry"]["version"]


@app.command()
def init():
    project_name = questionary.text("What is the name of your omelette (my_project)?", validate=lambda text: validate_underscore_name(text)).unsafe_ask()
    use_sls = questionary.confirm("Deploy using Serverless framework?", default=True).ask()
    omelette_version = get_omelette_version()
    typer.echo(f"🍳 Cooking omelette {project_name}")
    cookiecutter(os.path.join(os.path.dirname(__file__), "templates/project/"),
                 no_input=True,
                 extra_context={
                     "git_repo_name": project_name.replace("_", "-"),
                     "project_name": project_name,
                     "omelette_version": omelette_version
                 })
    if not use_sls:
        os.remove(f"./{project_name}/serverless.yml")

    typer.echo(f"🍳 Omelette {project_name} finished!")


@app.command()
def add_recipe():
    try:
        answers = questionary.form(
            recipe_name=questionary.text("What is the name of your recipe?",
                                         validate=lambda text: validate_underscore_name(text)),
            programming_style=questionary.select("Should this recipe use functions or a class (OOP)?",
                                                 choices=[ProgrammingStyleEnum.FUNCTIONAL.value, ProgrammingStyleEnum.OBJECT_ORIENTED.value]),
            long_running=questionary.confirm("Could your recipe ever take longer than 15 minutes to run?"),
            memory_size=questionary.confirm("Could your recipe ever need more than 3 GB memory?"),
            disk_space=questionary.confirm("Could your recipe ever need more than 0.5 GB disk space?"),
        ).unsafe_ask()

        if answers["long_running"] or answers["memory_size"]:
            recommendation = "AWS Fargate"
        else:
            recommendation = "AWS Lambda"

        typer.echo(f"\nBased on your answers, we recommend going with {typer.style(recommendation, fg=typer.colors.GREEN, bold=True)}.")
        type_choice = questionary.select(
            f"Hit enter to confirm, or change this option if you are sure the tool matches your needs.",
            choices=[RecipeTypeEnum.AWS_FARGATE.value, RecipeTypeEnum.AWS_LAMBDA.value],
            default=recommendation
        ).unsafe_ask()

        if type_choice == "AWS Lambda":
            trigger_choices = ["Schedule", "S3", "SQS", "SNS", "No Trigger (manual only)"]  # TODO: make these Enums
        else:
            trigger_choices = ["Schedule", "No Trigger (manual only)"]  # TODO: make these Enums

        trigger_type = questionary.select(
            "How should we launch your recipe?",
            choices=trigger_choices
        ).unsafe_ask()

        trigger_details = None

        if trigger_type == "Schedule":
            trigger_details = questionary.text("How often should your recipe run (either cron or rate type)?",
                                       validate=lambda text: validate_schedule_expression(text)).unsafe_ask()
        elif trigger_type == "S3":
            trigger_details = questionary.text("Which S3 bucket?").unsafe_ask()
        elif trigger_type == "SQS":
            trigger_details = questionary.text("What is the SQS queue name?").unsafe_ask()
        elif trigger_type == "SNS":
            trigger_details = questionary.text("What is the SNS topic name?").unsafe_ask()
        elif trigger_type == "No Trigger (manual only)":
            trigger_details = None
        else:
            typer.echo("Error: No matching trigger type. Goodbye!")
            typer.Exit()

        typer.echo(f"🍳 Crafting recipe: {answers['recipe_name']}")
        typer.echo(f"    Programming style: {answers['programming_style']}")
        typer.echo(f"    Recipe type: {type_choice}")
        typer.echo(f"    Recipe trigger: {trigger_type}")
        typer.echo(f"    Trigger details: {trigger_details}")

        confirm = questionary.confirm("Confirm everything looks good?", auto_enter=False).unsafe_ask()

        if confirm:
            typer.echo(f"🍳 Great! Cooking recipe...")
            recipe = Recipe(
                name=answers["recipe_name"],
                programming_style=answers["programming_style"],
                recipe_type=type_choice,
                requires_disk_space=answers["disk_space"],
                trigger_type=trigger_type,
                trigger_details=trigger_details,
            )
            recipe.create()
            typer.echo(f"Recipe created! Goodbye!")
        else:
            typer.echo("Aborting recipe creation. Goodbye!")
            typer.Exit()
    except KeyboardInterrupt:
        typer.echo("Aborting recipe creation. Goodbye!")
        typer.Exit()


if __name__ == "__main__":
    app()
