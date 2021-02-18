import questionary
import typer

from omelette.cli.recipe import Recipe
from .validators import validate_underscore_name, validate_schedule_expression

app = typer.Typer()


@app.command()
def init():
    project_name = questionary.text("What is the name of your omelette (project)?", validate=lambda text: validate_underscore_name(text)).unsafe_ask()
    typer.echo(f"🍳 Cooking omelette {project_name}")


@app.command()
def add_recipe():
    try:
        answers = questionary.form(
            recipe_name=questionary.text("What is the name of your recipe?",
                                         validate=lambda text: validate_underscore_name(text)),
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
            choices=["AWS Fargate", "AWS Lambda"],  # TODO: make these Enums
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
        typer.echo(f"    Recipe type: {type_choice}")
        typer.echo(f"    Recipe trigger: {trigger_type}")
        typer.echo(f"    Trigger details: {trigger_details}")

        confirm = questionary.confirm("Confirm everything looks good?", auto_enter=False).unsafe_ask()

        if confirm:
            typer.echo(f"🍳 Great! Cooking recipe...")
            recipe = Recipe(
                name=answers["recipe_name"],
                recipe_type=type_choice,
                requires_disk_space=answers["disk_space"],
                trigger_type=trigger_type,
                trigger_details=trigger_details
            )
            recipe.create()
        else:
            typer.echo("Aborting recipe creation. Goodbye!")
            typer.Exit()
    except KeyboardInterrupt:
        typer.echo("Aborting recipe creation. Goodbye!")
        typer.Exit()


if __name__ == "__main__":
    app()
