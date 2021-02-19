import logging
import os

from omelette import init_logging
from omelette import Settings

from omelette.eggs import Sftp, Snowflake, Slack, Files

init_logging(is_lambda=True)
logger = logging.getLogger(__name__)

settings = Settings(config_filepath="settings.toml")


def main():
    logger.info(f"Starting Example Recipe")

    sql_file = "./example_path_to_sql_file.sql"
    if not os.path.exists(sql_file):
        raise Exception("Sql file matching job name not found.")

    # Read sql file into string
    sql_query = Files.read_file_to_str(sql_file)
    output_file_name = settings.output_file_name  # Read from [default] section in settings.toml.

    # Read init settings from [{env}.snowflake] section in settings.toml. Names must match expected Snowflake egg args.
    sf_conn = Snowflake(**settings.snowflake)

    # Write query results to file.
    sf_conn.write_results_to_file(query_string=sql_query,
                                  output_file_name=output_file_name,
                                  file_format="CSV",
                                  delimiter="|")

    # Read init settings from [{env}.sftp] section in settings.toml. Names must match expected Sftp egg args.
    sftp_conn = Sftp(**settings.sftp)

    # Put file on SFTP
    sftp_conn.put(localpath=output_file_name, remotepath=f"{settings.sftp.directory}/{output_file_name}")

    # Cleanup file
    os.remove(output_file_name)


if __name__ == "__main__":
    slack = Slack(**settings.slack)

    try:
        main()
    except Exception as e:
        slack.send_slack_alert(f"Error running Snowflake to SFTP: {e}")
