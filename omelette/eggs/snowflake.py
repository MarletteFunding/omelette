import csv
import json
import logging

import snowflake.connector
from snowflake.connector.cursor import DictCursor

logger = logging.getLogger(__name__)


class Snowflake:
    """Wrapper around snowflake.connector. Provides helper methods for common tasks to simplify the API a bit."""

    def __init__(self, user: str, password: str, account: str, region: str, warehouse: str, database: str, role: str,
                 schema: str = None, **kwargs):
        self.conn = snowflake.connector.connect(
            user=user,
            password=password,
            account=account,
            region=region,
            warehouse=warehouse,
            database=database,
            role=role,
            schema=schema
        )
        self.cursor = None

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()

    def query(self, query_string: str):
        logger.info(f"Executing query: {query_string}")
        self.cursor = self.conn.cursor()
        return self.cursor.execute(query_string)

    def query_dict(self, query_string: str):
        logger.info(f"Executing query: {query_string}")
        self.cursor = self.conn.cursor(DictCursor)
        return self.cursor.execute(query_string)

    def stage_file(self, file_path: str, stage_name: str, table_name: str = None,
                   file_format: str = None, copy: bool = False) -> None:
        logger.info(f"Staging file {file_path} to stage {stage_name}")

        try:
            self.conn.cursor().execute(f"PUT file:///{file_path} @{stage_name}")
        except Exception as e:
            logger.error(f"Error staging file: {e}.")
            raise e

        if copy and table_name:
            try:
                self.conn.cursor().execute(f"COPY INTO {table_name} FROM @{stage_name} "
                                           f"FILES = ('{file_path}') FILE_FORMAT = {file_format}")
            except Exception as e:
                logger.error(f"Error copying file: {e}.")
                raise e

    def copy_staged_file(self, stage_name: str, table_name: str) -> None:
        pass

    def write_results_to_file(self, *, query_string: str, output_file_name: str, file_format: str = "CSV",
                              delimiter: str = ",", chunk_size: int = 10_000) -> str:
        logger.info(f"Writing SF query results to file: {output_file_name}")

        with open(output_file_name, "w") as f:
            rows = []
            processed_count = 0
            results = self.query_dict(query_string)

            if file_format.upper() == "CSV":
                writer = csv.DictWriter(f, delimiter=delimiter, fieldnames=[col[0] for col in self.cursor.description])
                writer.writeheader()

            for row in results:
                processed_count += 1

                if file_format.upper() == "JSON":
                    rows.append(json.dumps(row))
                elif file_format.upper() == "CSV":
                    rows.append(row)

                if len(rows) % chunk_size == 0:
                    if file_format.upper() == "JSON":
                        f.write("".join(rows))
                    elif file_format.upper() == "CSV":
                        writer.writerows(rows)

                    rows = []

            if len(rows) > 0:
                if file_format.upper() == "JSON":
                    f.write("".join(rows))
                elif file_format.upper() == "CSV":
                    writer.writerows(rows)

        logger.info(f"Successfully wrote SF query results to file: {output_file_name}")
        return output_file_name
