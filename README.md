<p align="center">
  <img src="./omelette.png">
</p>
<h2 align="center">Serverless Python ETL, Made O̶v̶e̶r̶ Easy</h2>

### Overview
Omelettes are a classic breakfast dish. As simple as 2-3 ingredients, or more complex
with all kinds of toppings mixed in. No matter what toppings you choose, the base is always the same.
Learn how to make one type of omelette, and there's a good chance you can figure out how to 
make any other kind with small changes to your toppings. 

We think the same thing can apply to ETL - given a few basic tools, repeated tasks shouldn't require much more than 
changes to configuration. When it comes to adding different types of tasks, you also shouldn't have to reinvent the wheel
every time when it comes to project setup, configuration, logging, and deployment. 

#### Meet Omelette
Omelette is an opinionated, yet flexible, serverless ETL framework built with Python in mind. Designed to make repeated
tasks easier by providing common tools for moving data from a given source to a different target. 

- Command Line Interface for initializing new projects or adding new recipes (tasks).
- Collection of source/target tools and connectors, called Eggs (*not to be confused with Python eggs).
- TOML-based Settings class for easy access to all of your configuration. 
- Customizable logging based on standard library logging.config.

### Core Concepts
#### Eggs
An Egg is a reusable Python module or component. Omelette currently comes with the following Eggs. Since an Egg is just a Python module, it's easy to create your own if 
you need something not in this list. We are always looking to add more eggs to our basket, so please submit a pull request 
if you think something would be useful to add! 
* **Files** - Helper functions for common tasks dealing with files, e.g., reading to a string, PGP encryption/decryption
* **SFTP** - Wrapper around PySFTP that makes it a bit easier to work with private keys.
* **S3** - Wrapper around boto3 S3 client that adds more logging and retry logic to tasks like uploading/downloading files.
* **SftpS3Interface** - Utility class to move files from S3 to SFTP and vice-versa.
* **Snowflake** - Wrapper around snowflake.connector that simplifies the API a bit and adds helpful functions like writing query results to files.
* **Slack** - Wrapper around Slack WebClient that adds retry logic and simplifies posting job alerts to channels. 
* **Kafka** - Class that allows simple Kafka consuming and publishing. Handles things like building SSL context, and mapping to JSON Schema or Cloudevents specs. 


#### Recipes
A recipe is nothing more than a Python module or script. They are meant to be reusable jobs that can be changed for different 
business requirements by only changing the configuration. An example is exporting data from a Snowflake query to a file, and sending
that file to an external vendor's SFTP server. We may work with a dozen vendors, have several dozen queries/files to send, but the 
main steps remain the same. We just need to provide different database credentials, a different sql file, and different SFTP connection parameters.
Within one recipe, we can configure many different jobs that follow the same steps.

Recipes are meant to be made simpler by pulling in Eggs as needed. In the example above, we could use the Snowflake egg to write query results to a file,
and then use the SFTP egg to put that file on the SFTP server. Since these tasks are already defined for the Egg, no need to look up how the underlying
components work every time.

#### Jobs
A job is simply a different configuration for a recipe. One recipe will have many jobs. At the most basic level, a job can be 
a `settings.toml` file with any configuration values. Or a job may be a separate directory with an included .sql file, additional Python modules,
or any other required files to complete the recipe differently than the base steps. 

#### Project Structure
When initializing a new Omelette project, this is what the base structure will look like. The root level has files like 
.gitignore, pyproject.toml (for Poetry packaging), a README, a Dockerfile, and a serverless.yml file. 
There is also a directory called `recipes/` and this is where individual recipes and their respective jobs are defined.


#### Configuration
Configuration variables are stored in .toml files within each job folder. The default is expecting a file called `settings.toml`,
but you can set a custom path as needed. 

Certain secrets (e.g. passwords) that should not be checked into Git can be interpolated from
environment variables. If you declared an item as `my_var = "${EXAMPLE_VALUE}"`, you will
need to have an environment variable `EXAMPLE_VALUE` defined. To avoid
passing secrets in plaintext in the run environment, you can also define variables in AWS Systems Manager
Parameter Store (SSM). To do so, simply prefix the value with `ssm:/` and the code will automatically
fetch and decode the param at runtime.

These configuration files are parsed by the [TOML Kit](https://github.com/sdispater/tomlkit) library, and then stored 
as attributes on an object called [Settings](#Settings). 

Every settings.toml file must have a `default` table. These default values are shared across all environments.

```
[default]
output_file_name = "example.csv"
```

After the `default` table, a table for each environment should exist, e.g. "local", "dev", and "prod". These tables override
any values that exist in the `default` table with the same name; in other words - environment settings take precedence over default settings.
Below we have two environments, `local` and `dev`, each with a custom `database_username` variable. In `dev`, we override the default `output_file_name`.
```
[default]
output_file_name = "example.csv"

[local]
database_username = "local_user"

[dev]
output_file_name = "example_dev.csv"
database_username = "dev_user"
```

Since TOML and TOML Kit support nested tables/sections, we use them within the context of an environment. To declare a group of settings
for a given environment, prefix the table name with the name of the environment, e.g. `local.mysql`.

```
[default]
output_file_name = "example.csv"

[local]
    [local.mysql]
    username = "local_user"
    password = "secret password"
```

Read more below for how these values are accessed in Settings.

#### Settings
The [Settings](omelette/utils/settings.py) class reads `settings.toml` files, and sets attributes on itself for 
every item in the config file. However, it will only ever load settings from the `default` table and the table (and its children) matching 
the current environment, e.g., `local`. The environment **must** be set with a variable `PROJECT_ENV`, otherwise the fallback 
is `local` so nothing will ever touch production by accident. The value of this variable needs to match a corresponding section in your `settings.toml` file,
but you are free to name environments as you wish. There's no difference if you call an environment `dev` or `sandbox` or `test`, so long as
you set `PROJECT_ENV=dev` or `PROJECT_ENV=sandbox` or `PROJECT_ENV=test`.

Initialization:
```
from omelette import Settings
settings = Settings(config_filepath=custom_path + "settings.toml")
```

By default, it extracts the environment from the `PROJECT_ENV` variable, but you can override if needed by passing an `env` argument:
```
settings = Settings(config_filepath=custom_path + "settings.toml", env="dev")
```

After your config file is read, the default and environment-specific values are set to be accessible from the Settings object
in either dict-notation, or dot-notation. Inspired by [Dynaconf](https://www.dynaconf.com/), this means you can do the following:
```
# Get
settings.user
settings.get("user")
settings["user"]

# Get nested settings e.g. from [local.mysql] section of settings.toml
settings.mysql.user
settings.get("mysql").user
settings["mysql"]["user"]

# Set
settings.user = "Omelette"
settings["user"] = "Omelette"

# Iterate
for x in settings.items()
for x in settings.keys()
for x in settings.values()
```

This flexibility makes it easier to access settings vs always having to use dict-notation, get environment variables every time, 
or use ConfigParser and pass the section for every variable. 

Because Settings is a dict-like object, you can also set values to update config or store state as your job progresses. 
This can however introduce side effects since you are bringing state into functions, but it can be handy to throw variables in here
instead of passing them down a large tree of functions as standard arguments.

#### Logging
Omelette provides a function `init_logging` which initializes handlers, formatters, and loggers with Python's logging.config.dictConfig.
Similar to Settings, you can pass a custom `env` argument but the default is your `PROJECT_ENV` environment variable.
We set the root log level based on your environment (local, sbx = DEBUG, all others = INFO), but you can also pass this as an
override with the `root_level` argument, OR by setting an environment variable `ROOT_LOG_LEVEL`. We also expose the logging.config option
`disable_existing_loggers` as an argument, defaulted to False. 

##### Customizing module loggers: 
You can customize the log level for any module by passing a dictionary where keys are module names, and values are log levels. 
Example as read from `settings.toml`:

```
# settings.toml
[logging]
boto3 = "DEBUG"
botocore = "ERROR"

# recipe.py
init_logging(loggers=settings.logging)
```

##### Special Handling for AWS Lambda
Since AWS Lambda controls the logging environment, we can't/shouldn't set any custom formatters or logging config. What 
we can do though is set the overall log level. When running a lambda recipe, use the `is_lambda` option, which when set to True
will skip the dictConfig initialization and just call `logging.getLogger().setLevel(log_level)` with either the default
environment level, or a custom level passed in like `init_logging(level="DEBUG")`.

### Getting Started
#### Installation
```poetry add git+ssh://git@github.com/MarletteFunding/omelette.git#0.1.1```

or
 
```pip install git+ssh://git@github.com/MarletteFunding/omelette.git#0.1.1```

#### Initialize a new Omelette Project
`omelette init` will set up a new project in the current directory. This should be run from within a new, empty directory
and will generate all required files. If you choose to use Serverless for deployment, it will add a serverless.yml file.
```
$ omelette init
? What is the name of your omelette (my_project)? snowflake_etl
? Deploy using Serverless framework? Yes
🍳 Cooking omelette snowflake_etl
🍳 Omelette snowflake_etl finished!
```

#### Add a Recipe
`omelette add-recipe` will ask you a few questions and set up a new recipe based on your answers. Currently it supports
AWS Fargate (Docker) or AWS Lambda tasks. It will generate all recipe files and add a sample recipe that you can either customize or overwrite.

```
$ omelette add-recipe
? What is the name of your recipe? snowflake_to_s3
? Should this recipe use functions or a class (OOP)? Functional
? Could your recipe ever take longer than 15 minutes to run? Yes
? Could your recipe ever need more than 3 GB memory? Yes
? Could your recipe ever need more than 0.5 GB disk space? Yes

Based on your answers, we recommend going with AWS Fargate.
? Hit enter to confirm, or change this option if you are sure the tool matches your needs. AWS Fargate
? How should we launch your recipe? Schedule
? How often should your recipe run (either cron or rate type)? rate(1 day)
🍳 Crafting recipe: snowflake_to_s3
    Programming style: Functional
    Recipe type: AWS Fargate
    Recipe trigger: Schedule
    Trigger details: rate(1 day)
? Confirm everything looks good? Yes
🍳 Great! Cooking recipe...
Recipe created! Goodbye!
```

### Deployment

Omelette uses the [Serverless Framework](https://www.serverless.com/) for deployment. Using the CLI will automatically
update the [serverless.yml](serverless.yml) file (still in development) and add either a new `function` for AWS Lambda recipes, or a `step_functions` state machine
for AWS Fargate tasks. We use AWS Step Functions to run Fargate tasks instead of ECS Scheduled Tasks, mainly because of its ability to retry jobs, catch errors, 
and integrate with other services. By default we set up an error state that can be configured to call a Lambda that sends an alert, e.g. to Slack,
and we set the retry count to 2. 

Serverless.yml is the master container for all deployment artifacts, but we package individual components (functions or state machine definitions)
with each recipe so that code + infrastructure are close together and always easy to find. It makes it easier to modify deployment
settings too when each recipe is isolated. 

### Contributing:
* Make your changes locally
* Increment the version number in pyproject.toml
* Commit & push changes to Github, open PR, merge to master after approval
* Create a new release in Github, tagging it with the same version number in pyproject.toml
* Releases can be installed specifically by Poetry by settings the `rev` tag in pyproject.toml for omelette, e.g.:
  ```
  [tool.poetry.dependencies]
  python = "^3.7"
  data-utils = {git = "https://github.com/MarletteFunding/omelette", rev = "0.1.5"}
  ```
