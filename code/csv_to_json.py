# -*- coding: utf-8 -*-
"""
Created on Thu Jun 21 13:41:28 2018

@author: thomas
"""

import pandas as pd
from ast import literal_eval

def csv_to_json(csv_file, json_file, sep, columns_with_array_of_str):
    df = pd.read_csv(csv_file, sep=sep, encoding='utf-8')
    
    for column in columns_with_array_of_str:
        df[column] = df[column].apply(literal_eval)
    
    with open(json_file, 'w', encoding='utf-8') as file:
        df.to_json(file, orient='records', force_ascii=False)
        
    return json_file

#if __name__ == "__main__":
#    csv_file = "./params/params_auto - Feuille 1.tsv"
#    json_file = "./params/params_auto.json"
#    sep = "\t"
#    columns_with_array_of_str = ["colors_iso","adresses"]
#    
#    df = csv_to_json(csv_file, json_file, sep, columns_with_array_of_str)