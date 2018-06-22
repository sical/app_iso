# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 13:41:28 2018

@author: thomas
"""

import pandas as pd
from ast import literal_eval

def csv_to_json(csv_file, json_file, sep, columns_with_array):
    df = pd.read_csv(csv_file, sep=sep)
    
    for column in columns_with_array:
        df[column] = df[column].apply(literal_eval)
    
    df.to_json(json_file, orient='records')

if __name__ == "__main__":
    csv_file = "params_auto - Feuille 1.tsv"
    json_file = "params_auto.json"
    sep = "\t"
    columns_with_array = ["colors_iso","adresses"]
    
    df = csv_to_json(csv_file, json_file, sep, columns_with_array)