import pandas as pd


def round_columns_based_on_reference(
    df: pd.DataFrame, reference_column: str, target_columns: list[str]
) -> pd.DataFrame:
    """
    Round selected columns in a DataFrame based on the value of a reference column.

    Parameters:
    - df: The input DataFrame.
    - reference_column: Column used to determine rounding precision (e.g., "Close").
    - target_columns: List of columns to apply the rounding to.

    Returns:
    - DataFrame with rounded columns.
    """

    if df.empty or reference_column not in df.columns:
        return df.copy()

    median_value = df[reference_column].median()

    if median_value < 1:
        decimals = 4
    elif median_value < 10:
        decimals = 3
    elif median_value < 100:
        decimals = 2
    elif median_value < 1000:
        decimals = 1
    else:
        decimals = 0

    df_rounded = df.copy()
    for col in target_columns:
        if col in df_rounded.columns:
            df_rounded[col] = df_rounded[col].round(decimals)

    return df_rounded
