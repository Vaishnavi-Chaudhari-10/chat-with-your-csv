
import sqlite3
import pandas as pd

from sql_validator import validate_sql


def create_database(df):
    connection = sqlite3.connect(":memory:")

    df.to_sql(
        "uploaded_data",
        connection,
        index=False,
        if_exists="replace"
    )

    return connection


def get_table_schema(connection):
    return pd.read_sql_query(
        "PRAGMA table_info(uploaded_data)",
        connection
    )


def get_table_preview(connection):
    return pd.read_sql_query(
        "SELECT * FROM uploaded_data LIMIT 5",
        connection
    )


def get_schema_text(connection):
    schema_df = get_table_schema(connection)

    columns = []

    for _, row in schema_df.iterrows():
        columns.append(f"    {row['name']} {row['type']}")

    return (
        "CREATE TABLE uploaded_data (\n"
        + ",\n".join(columns)
        + "\n);"
    )


def read_only_authorizer(action, arg1, arg2, database_name, trigger_name):
    """
    Allow SELECT queries and reads from uploaded_data only.
    Block database modifications and access to other tables.
    """

    # Allow SELECT operations.
    if action == sqlite3.SQLITE_SELECT:
        return sqlite3.SQLITE_OK

    # Allow reading only from uploaded_data.
    if action == sqlite3.SQLITE_READ:

        if arg1 is not None and arg1.lower() == "uploaded_data":
            return sqlite3.SQLITE_OK

        return sqlite3.SQLITE_DENY

    # Allow normal SQL functions but block potentially dangerous ones.
    if action == sqlite3.SQLITE_FUNCTION:

        function_name = (arg2 or "").lower()

        blocked_functions = {
            "load_extension",
            "readfile",
            "writefile",
            "fts3_tokenizer"
        }

        if function_name in blocked_functions:
            return sqlite3.SQLITE_DENY

        return sqlite3.SQLITE_OK

    # Allow recursive CTE queries if supported.
    recursive_action = getattr(sqlite3, "SQLITE_RECURSIVE", None)

    if recursive_action is not None and action == recursive_action:
        return sqlite3.SQLITE_OK

    # Deny all other operations.
    return sqlite3.SQLITE_DENY


def execute_query(connection, query):
    # First validate the SQL query using SQLGlot.
    validated_query = validate_sql(query)

    # Enable SQLite-level read-only restrictions.
    connection.set_authorizer(read_only_authorizer)

    try:
        result = pd.read_sql_query(
            validated_query,
            connection
        )

        return result

    finally:
        # Remove the temporary authorizer after execution.
        connection.set_authorizer(None)
