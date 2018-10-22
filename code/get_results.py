# -*- coding: utf-8 -*-
"""
Created on Mon Oct 22 11:22:06 2018

@author: thomas
"""

import os
import docopt
from dotenv import load_dotenv
from pathlib import Path
import json

from csv_to_json import csv_to_json
import isos_and_intersections as iai

if __name__ == "__main__":
    #Parameters
    try:
        env_path = Path('./') / '.env'
        load_dotenv(dotenv_path=env_path)
        TOKEN = os.getenv("NAVITIA_TOKEN")
    except:
        TOKEN = os.getenv("NAVITIA_TOKEN")
        
    columns_with_array_of_str = [
        "colors_iso",
        "adresses",
        "excluded_modes",
        "durations"
        ]
    
    #JSON INPUT
    arguments = docopt(__doc__)
    infile = arguments["<infile_csv>"]
    outfile = arguments["<outfile_json>"]
    sep = arguments["<separator>"]
    json_file = csv_to_json(infile, outfile, sep, columns_with_array_of_str)
#    json_file = "./paracsv_to_jsonms/params_auto.json"
    params_auto = json.load(open(json_file, encoding='utf-8'))
    