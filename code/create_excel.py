import pandas as pd

import pandas.io.formats.excel

# https://stackoverflow.com/questions/39892684/how-can-i-format-the-index-columns-with-xlsxwriter
pandas.io.formats.excel.ExcelFormatter.header_style = None


def create_dataframes():
    """
    Load and merge datasets, indicators, and links CSV files into a single DataFrame.

    - Reads 'datasets.csv', 'indicators.csv', and 'links.csv'.
    - Adds prefixes to all columns except the join keys.
    - Merges indicators and datasets into links on their respective IDs.
    - Sorts and sets a MultiIndex for the resulting DataFrame.
    - Fills missing values with an empty string.

    Returns:
        pd.DataFrame: The merged and indexed DataFrame ready for export.
    """
    datasets = pd.read_csv("datasets.csv")
    indicators = pd.read_csv("indicators.csv")
    links = pd.read_csv("links.csv")

    ind_cols = indicators.set_index("indicator_id").columns.to_list()
    indicators.rename(
        columns={col: "indicator_" + col for col in ind_cols}, inplace=True
    )
    data_cols = datasets.set_index("dataset_id").columns.to_list()
    datasets.rename(columns={col: "dataset_" + col for col in data_cols}, inplace=True)

    index = [
        "indicator_category",
        "indicator_id",
        "indicator_name",
        "indicator_source",
        "indicator_description",
    ]
    return (
        links.merge(indicators, on="indicator_id", how="left")
        .merge(datasets, on="dataset_id", how="left")
        .sort_values(["indicator_category", "indicator_id"])
        .set_index(index)
        .fillna("")
    )


def write_to_excel(df, filename="catalog.xlsx"):
    """
    Write a DataFrame to an Excel file with custom formatting using XlsxWriter.

    - Writes the DataFrame to the specified Excel file.
    - Applies custom header formatting.
    - Sets column widths and enables text wrapping for all columns.
    - Applies alternating row background color for readability.
    - Merges repeated MultiIndex cells for a cleaner look.

    Args:
        df (pd.DataFrame): The DataFrame to export.
        filename (str): The name of the Excel file to create.
    """
    # Create a Pandas Excel writer using XlsxWriter as the engine.

    with pd.ExcelWriter(filename, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=True, sheet_name="catalog")
        workbook = writer.book
        worksheet = writer.sheets["catalog"]
        wrap_format = workbook.add_format(
            {"text_wrap": True, "align": "left", "valign": "top"}
        )
        grey_format = workbook.add_format(
            {"bg_color": "#F2F2F2", "text_wrap": True, "align": "left", "valign": "top"}
        )

        header_format = workbook.add_format(
            {
                "bold": True,
                "text_wrap": True,
                "valign": "top",
                "fg_color": "#D7E4BC",
                "border": 1,
            }
        )

        n_index = len(df.index.names)
        n_rows = len(df)
        n_cols = len(df.columns)

        # Write the column headers with the defined format.
        for col_num, value in enumerate(df.index.names):
            worksheet.write(0, col_num, value, header_format)

        # Write the data columns headers with the defined format.
        for col_num, value in enumerate(df.columns):
            worksheet.write(0, col_num + n_index, value, header_format)

        # Set wrap for all index columns
        for idx in range(n_index):
            worksheet.set_column(idx, idx, 30, wrap_format)

        # Set wrap for data columns
        for col_num in range(n_index, n_index + n_cols):
            worksheet.set_column(col_num, col_num, 50, wrap_format)

        # Apply alternating row color (starting after header row)
        for row in range(1, n_rows + 1):
            fmt = grey_format if row % 2 == 0 else wrap_format
            # worksheet.set_row(row, 60, fmt)
            # Write data columns
            for col in range(n_cols):
                value = df.iloc[row - 1, col]
                worksheet.write(row, col + n_index, value, fmt)

        # --- Merge repeated MultiIndex cells ---
        # Get the index values as a DataFrame
        idx_df = pd.DataFrame(df.index.tolist(), columns=df.index.names)
        start_row = 1  # Excel row index (0 is header)

        for col in range(n_index - 1, n_index):
            col_values = idx_df.iloc[:, col]
            last_val = None
            merge_start = start_row
            for row in range(n_rows):
                val = col_values.iloc[row]
                if val != last_val and row > 0:
                    if row + start_row - merge_start > 1:
                        worksheet.merge_range(
                            merge_start,
                            col,
                            row + start_row - 1,
                            col,
                            last_val,
                            wrap_format,
                        )
                    merge_start = row + start_row
                last_val = val
            # Merge the last group
            if n_rows + start_row - merge_start > 1:
                worksheet.merge_range(
                    merge_start, col, n_rows + start_row - 1, col, last_val, wrap_format
                )


if __name__ == "__main__":
    df = create_dataframes()
    write_to_excel(df, "catalog.xlsx")
    print("Excel file created successfully.")
