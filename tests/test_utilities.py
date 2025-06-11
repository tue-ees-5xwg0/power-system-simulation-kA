import pytest
import pandas as pd
from typing import List

def compare_pandas_dataframes_fp(test:  pd.DataFrame, control: pd.DataFrame, columns_to_compare: List[str]):
    """
    Returns True or False depending on if there is a difference between the dataframes. If a difference is found 
    this value is set to False and the column with the difference is returned in the list. This function also adds tolerance for floating-points.
    """
    # check if all requested columns are present in the datasets
    for column in columns_to_compare:
        if column not in test.columns:
            raise KeyError(f'Column "{column}" not found in dataframe.')

    # compare the tables and set NaN values to 1
    comparison = test.compare(control).fillna(1)

    # get list of all columns with a difference for itarating
    columns_with_difference = list(set(comparison.columns.get_level_values(0)))
    
    equal = True
    errors = []

    # compare each difference with pytest tolerance for floating points
    for column in columns_with_difference:
        if (comparison[column]['self'].tolist() == pytest.approx(comparison[column]['other'])) is not True:
            errors.append(column)
            equal = False
            
    return (equal, errors)