#%%
import json
import numpy as np
import os,glob
import datetime

from numpy.lib.arraysetops import unique

def convert_to_float(str_in):
    try:
        return float(str_in)
    except:
        return 0.

# Opening JSON file
def convert_string_to_min(str_json):
    to_split=['H','M','S']
    conversion=[60,1,1./60]
    total_time=0.
    if str_json:
        str1=str_json.split('PT') #remove PT
        for idx,c in enumerate(to_split):
            str1=str1[1].split(c)
            if len(str1)==1:
                str1.insert(0,'0')
            total_time += conversion[idx]*convert_to_float(str1[0])
        return total_time
    else:
        print('Empty String : ', str_json)
        return 0
    
def get_zones_json_file(file_name):
    f = open(file_name)
    zone=[0,1,2,3,4,5]
    zone_data=len(zone)*[0.]
    data = json.load(f)
    for d in data['samples']:
        d1=d['activity-zones']
        for z in zone:
            d2=d1[z]
            d3=d2.get('inzone')
            zone_data[z]+= convert_string_to_min(d3)
    return np.array(zone_data)

def get_data_from_json(zone_file='act_zone', sum_file='act_sum'):

    #find all json files, only store number
    file_list=[]
    for file in glob.glob(zone_file+"*.json"):
        ext=(file.split('act_zone')[1]).split('.json')[0]
        file_list.append(ext)
    # find unique dates
    date_list=[]
    for i in file_list:
        f = open(sum_file+str(i)+'.json')
        data=json.load(f)
        date_list.append(data['date'])
        f.close()
    date_list=unique(date_list)
    time_zone_date=[]
    for date in date_list:
        time_zone_date.append(get_time_zone_data(date,file_list))
    
    return date_list,time_zone_date


def get_time_zone_data(date,file_list,zone_file='act_zone', sum_file='act_sum',datetime=True):
    '''
    Searches json files in folder and returns the most up to 
    date zone data (currently the one with most minutes)
    '''
    total_time_zone=np.zeros(6)
    for i in file_list:
        f = open(sum_file+i+'.json')
        data=json.load(f)
        if date == data['date']:
            fname2=zone_file+i+'.json'
            time_in_file=get_zones_json_file(fname2)
            if np.sum(time_in_file) >= np.sum(total_time_zone):
                total_time_zone=time_in_file
    if datetime:
        return convert_np_to_datetime(total_time_zone)
    else:
        return total_time_zone

def convert_np_to_datetime(arr):
    l=[]
    for elem in arr:
        l.append(str(datetime.timedelta(minutes=elem)))
    return l

if __name__=='__main__':
    date,zone=get_data_from_json()
    #%%
    try:
        os.chdir('tmp')
    except:
        pass
    date='2022-01-07'
    zone_file='act_zone'
    sum_file='act_sum'
    total_time_zone=np.zeros(6)
    for i in range(1,51):
        f = open(sum_file+str(i)+'.json')
        data=json.load(f)
        if date == data['date']:
            print(data)
            fname2=zone_file+str(i)+'.json'
            time_in_file=get_zones_json_file(fname2)
            total_time_zone += time_in_file
            print(time_in_file, ' file: ', fname2)
    print('Overall Time ', total_time_zone)


#%%
    f = open('act_sum1.json')
    f2=open('act_zone1.json')


    # returns JSON object as
    # a dictionary
    data = json.load(f)
    data2 =json.load(f2)
    zone=0
    total_time=0.
    for d in data2['samples']:
        d1=d['activity-zones']
        d2=d1[zone]
        d3=d2.get('inzone')
        print(d3)
        total_time += convert_string_to_min(d3)
        print(total_time)

# %%
