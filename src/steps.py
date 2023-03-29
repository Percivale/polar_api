#%%
import pandas as pd
import pathlib as pt
import datetime
import os
import numpy as np
import sys

root_name=sys.argv[1]
#id_nr='60xx'
#root_name='Clinical_'+id_nr

def parse_clinical():
    file=root_name+'.xlsx'
    try:
        df=pd.read_excel(file)
        date=df[df.columns[5]]
        start_time=df[df.columns[7]]
        end_time=df[df.columns[8]]
        return pd.to_datetime(date),start_time,end_time,df
    except:
        print('could not open file ', file)
        print('Wrong directory?')
        print('Current directory is ', os.getcwd())
        return 0,0,0,pd.DataFrame()


def find_file_with_steps(date,start,path='.', col='BINNED_STEPS_TIMESTAMP'):
    start_date_time=datetime.datetime.combine(date,start)
    skip_file=False
    for csv_file in pt.Path(path).rglob('*.csv'):
        try:
            df=pd.read_csv(csv_file,sep=',')
        except:
            skip_file=True
            print('could not open file ', csv_file)
        if not skip_file:
            try:
                a=pd.to_datetime(df[col])
                idx=date_in_col(start_date_time,a)
                if idx >-1:
#                    print('Found file')
                    return csv_file
            except:
                pass
 #               print(col, ' not in file ', csv_file)
        skip_file=False
        
    return ''


def date_in_col(date,series):
    for idx,d in enumerate(series):
        if date == d:
            return idx
    return -1

def extract_steps_from_file(file,date,start,stop,
                            dcol='BINNED_STEPS_TIMESTAMP', 
                            step_col='BINNED_STEPS_STEPS_IN_BIN'):
    start_date_time=datetime.datetime.combine(date,start)
    stop_date_time=datetime.datetime.combine(date,stop)
    df=pd.read_csv(file,sep=',')
    dates=pd.to_datetime(df[dcol])
    steps=df[step_col].to_numpy()
    id_start=date_in_col(start_date_time,dates)
    id_stop=date_in_col(stop_date_time,dates)
    if id_start == -1 or id_stop == -1:
        print('No steps available')
        tot_steps=0
    else:
        tot_steps=np.sum(steps[id_start:id_stop+1])
    return tot_steps



    
#print(os.getcwd())
#try:
#    os.chdir('../polar_data/steps')
#except:
#    pass
date,start_time,end_time,df=parse_clinical()
steps=[]
for d,t0,tf in zip(date,start_time,end_time):
    if type(t0) is datetime.time:
        file=find_file_with_steps(d,t0)
        if file == '':
            print('could not find date in step file')
            steps.append(0)
        else:
            steps.append(extract_steps_from_file(file,d,t0,tf))
    else:
        print('No values at date ', d)
        steps.append(0)
    print('date: ', d, ' steps ', steps[-1])
print('Finnished')
df['steps_per_session']=steps
df.to_excel(root_name+'with_steps.xlsx', index=False)



#start_date_time=datetime.datetime.combine(date[0],start_time[0])
#files=find_file_with_steps(date[0],start_time[0])
#df=pd.read_csv(files[1],sep=',')
#a=pd.to_datetime(df['BINNED_STEPS_TIMESTAMP'])
# %%
