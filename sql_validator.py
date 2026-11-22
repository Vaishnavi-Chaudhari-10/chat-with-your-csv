import sqlglot
from sqlglot import exp


def validate_sql(query):

    if not query or not query.strip():
        raise ValueError("SQL query is empty.")

    try:
        parsed_queries = sqlglot.parse(query, read="sqlite")
    except Exception as e:
        raise ValueError(f"Invalid SQL syntax: {e}")

    if len(parsed_queries) != 1 or parsed_queries[0] is None:
        raise ValueError("Only one SQL statement is allowed.")

    parsed = parsed_queries[0]

    if not isinstance(parsed, exp.Select):
        raise ValueError("Only SELECT queries are allowed.")

    tables = parsed.find_all(exp.Table)

    if not tables:
        raise ValueError("The query must read from uploaded_data.")

    for table in tables:
        if table.name.lower() != "uploaded_data":
            raise ValueError(
                "Queries can only access the uploaded_data table."
            )

    return query
