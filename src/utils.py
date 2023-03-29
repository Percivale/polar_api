#!/usr/bin/env python

import json
import yaml
import pandas as pd

def my_write_to_excel(df:pd.DataFrame,file_name,index=True):
        '''
        give user a chance to close excel file
        '''
        file_not_closed=True
        while file_not_closed:
            try:
                with pd.ExcelWriter(file_name,date_format='DD.MM.YYYY',datetime_format='DD.MM.YYYY',engine='xlsxwriter') as writer:
                    df.to_excel(writer,index=index)
                file_not_closed=False
            except Exception as e:
                print("The following exception occurred ", e.__class__)
                print(" If file "+file_name+" not closed, please close before continue")
                input("Press enter after closing to continue")
                
        print('Wrote file: '+file_name)

def load_config(filename):
    """Load configuration from a yaml file"""
    with open(filename) as f:
        return yaml.safe_load(f)


def save_config(config, filename):
    """Save configuration to a yaml file"""
    with open(filename, "w+") as f:
        yaml.safe_dump(config, f, default_flow_style=False)


def pretty_print_json(data):
    print(json.dumps(data, indent=4, sort_keys=True))

def write_json(data, fname):
    with open(fname, 'w') as outfile:
        json.dump(data, outfile)