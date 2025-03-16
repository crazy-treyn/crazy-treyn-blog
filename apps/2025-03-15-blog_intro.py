import marimo

__generated_with = "0.11.20"
app = marimo.App()


@app.cell
def _():
    import numpy as np
    import altair as alt
    import pandas as pd
    import marimo as mo
    import polars as pl
    import pyarrow.parquet as pq
    import duckdb
    return alt, duckdb, mo, np, pd, pl, pq


@app.cell
def _(mo):
    mo.md(
        """
        # Welcome to my blog!

        <img src="public/logo.png" width="150" align="center" />

        I’m launching this blog to explore how reactive, Python-focused Marimo notebooks can be used as blog posts, turning each blog post into its own interactive app. This opens up the possibility of creating a more engaging experience where readers can interact directly with live python code running right in their browser.
        """
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Example 1:

        You can click and drag to highlight data points from the below chart, and you will see that the dataframe below as well as the Markdown above the chart, showing the Y value average based on your selection.
        """
    )
    return


@app.cell
def _(alt, mo, np, pd):
    # Create sample data
    data = pd.DataFrame({"x": np.arange(100), "y": np.random.normal(0, 1, 100)})

    # Create interactive chart
    chart = mo.ui.altair_chart(
        (
            alt.Chart(data)
            .mark_circle()
            .encode(x="x", y="y", size=alt.value(100), color=alt.value("steelblue"))
            .properties(height=400, title="Interactive Scatter Plot")
        )
    )
    return chart, data


@app.cell
def _(chart, df, mo):
    # View the chart and selected data as a dataframe
    df = chart.value

    average_y = mo.sql("SELECT AVG(Y) FROM df")[0,0]

    if average_y is None:
        avg_title = mo.md(f"###Select data points to show average")
    else:
        avg_title = mo.md(f"###The average Y value is: **{average_y}**")

    mo.vstack([avg_title, chart, df])
    return average_y, avg_title, df


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Example 2

        We can process millions of rows of public available data and aggregate and plot the results, all running locally in the browser with DuckDB. Although this Marimo notebook is read-only, I can give you a code editor to allow you to pass in your own SQL queries and see the resulting dataframe.

        First, we will create a table in memory with DuckDB based on [NYC Taxi Trip data.](https://d37ci6vzurychx.cloudfront.net/trip-data/yellow_tripdata_2023-01.parquet)
        """
    )
    return


@app.cell
def _(duckdb, mo, pq, tbl):
    #parquet_file_relative = "public/yellow_tripdata_2023-01.parquet"
    #parquet_file_full = "apps/public/yellow_tripdata_2023-01.parquet"

    path = mo.notebook_location() / "public" / "yellow_tripdata_2023-01.parquet"

    arrow_tbl = pq.read_table(path)

    duckdb.register("tbl", arrow_tbl)

    # Register the Parquet file as a table
    mo.sql(f"CREATE OR REPLACE VIEW taxi_trips AS SELECT * FROM tbl", )
    return arrow_tbl, path, taxi_trips


@app.cell
def _(mo, taxi_trips):
    total_rows = mo.sql("SELECT COUNT(1) as TaxiRowCount FROM taxi_trips", output=False)[0,0]

    # Example query: Count trips by passenger count
    query = """
        SELECT passenger_count, COUNT(*) as trip_count
        FROM taxi_trips
        GROUP BY passenger_count
        ORDER BY passenger_count
    """
    _schema = mo.sql('DESCRIBE taxi_trips', output=False)

    # Select only the two necessary columns and convert to a dictionary
    dict_values = dict(zip(_schema["column_name"], _schema["column_type"]))


    # Generate Markdown string
    markdown_str = "### List of Available Fields to Query\n\n"
    markdown_str += "| Field | Value |\n|---|---|\n"

    # Append key-value pairs as Markdown table rows
    for key, value in dict_values.items():
        markdown_str += f"| {key} | {value} |\n"

    # Print the Markdown output
    mo.md(markdown_str)
    return dict_values, key, markdown_str, query, total_rows, value


@app.cell
def _(mo, query):
    editor = mo.ui.code_editor(
        value=query,
        language="sql"
    )
    editor

    submit_query_btn = mo.ui.run_button(label="Run Query")

    mo.vstack([mo.md("Specify a query to run and click 'Run Query'"), editor, submit_query_btn])
    return editor, submit_query_btn


@app.cell
def _(editor, mo, submit_query_btn, total_rows):
    mo.stop(not submit_query_btn.value, mo.md("Run the query to continue.."))

    result = mo.sql(editor.value)

    # Display the result (as a Pandas DataFrame)
    title = mo.md(f"Total rows in the polars dataframe: {total_rows:,}")

    mo.vstack([title, result])
    return result, title


if __name__ == "__main__":
    app.run()
