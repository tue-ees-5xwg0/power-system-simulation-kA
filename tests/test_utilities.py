import pytest
import pandas as pd
from typing import List

def compare_pandas_dataframes_fp(test:  pd.DataFrame, control: pd.DataFrame, columns_to_compare: List[str]):
    """
    Returns True or False depending on if there is a difference between the dataframes. If a difference is found 
    this value is set to False and the column with the difference is added to the list. This function adds tolerance for floating-points.
    """
    
    comparison = test.compare(control).fillna(1)
    equal = True
    errors = []

    for column in columns_to_compare:
        if (comparison[column]['self'].tolist() == pytest.approx(comparison[column]['other'])) is not True:
            errors.append(column)
            equal = False
            
    return (equal, errors)