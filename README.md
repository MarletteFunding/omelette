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
Omelette currently comes with the following Eggs. Since an Egg is just a Python module, it's easy to create your own if 
you need something not in this list. We are always looking to add more eggs to our basket, so please submit a pull request 
if you think something would be useful to add! 
* **File** - Helper functions for common tasks dealing with files, e.g., reading to a string, PGP encryption/decryption
* **SFTP** - Wrapper around PySFTP that makes it a bit easier to work with private keys.
* **S3** - Wrapper around boto3 S3 client that adds more logging and retry logic to tasks like uploading/downloading files.
* **SftpS3Interface** - Utility class to move files from S3 to SFTP and vice-versa.
* **Snowflake** - Wrapper around snowflake.connector that simplifies the API a bit and adds helpful functions like writing query results to files.
* **Slack** - Wrapper around Slack WebClient that adds retry logic and simplifies posting job alerts to channels. 


#### Recipes
A recipe is nothing more than a Python module or script. They are meant to be reusable jobs that can be changed for different 
business requirements by only changing the configuration. An example is exporting data from a Snowflake query to a file, and sending
that file to an external vendor's SFTP server. We may work with a dozen vendors, have several dozen queries/files to send, but the 
main steps remain the same. We just need to provide different database credentials, a different sql file, and different SFTP connection parameters.
Within one recipe, we can configure many different jobs that follow the same steps.

#### Jobs
A job is simply a different configuration for a recipe. One recipe will have many jobs. At the most basic level, a job can be 
a `settings.toml` file with any configuration values. Or a job may be a separate directory with an included .sql file, additional Python modules,
or any other required files to complete the recipe differently than the base steps. 

#### Project Structure
When initializing a new Omelette project, this is what the base structure will look like. The root level has files like 
.gitignore, pyproject.toml (for Poetry packaging), a README, a Dockerfile, and a serverless.yml file. 
There is also a directory called `recipes/` and this is where individual recipes and their respective jobs are defined.


#### Configuration


#### Logging

### Getting Started
#### Installation
```poetry add git+ssh://git@github.com/MarletteFunding/omelette.git#2.0.5```


