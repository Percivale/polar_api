# -*- coding: utf-8 -*-
"""
Created on Thu Dec 23 08:37:16 2021

@author: kajah
"""

import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import datetime

def clean_up(df, remove_col = False, col_names = []):
    df = df[df["ID"] != np.nan]
    if remove_col:
        df.drop(columns = col_names)
    return 0

def get_patient(df, ID):
    return df[df["ID"] == ID]


def gen_percent(df,teller,nevner,ID="",debug=False):
    '''
    df: dataframe for all deltagere
    ID: for å hente ut prosent for enkeltdeltager:
        f.gen_percent(combined,ID=6001,teller='Time_in_zone',nevner='Polar_time')
        for alle:
        f.gen_percent(combined,teller='Time_in_zone',nevner='Polar_time')
    returnerer sum(teller)/sum(nevner)*100
    '''
    if debug:
        print("teller", teller)
        print("nevner",nevner)
    if ID=="":
        all_id=True
    else:
        all_id=False
    if all_id:
        ID_all=df["ID"].dropna().to_numpy()
        ID_all=np.unique(ID_all)
    else:
        ID_all=[ID]
    hr_p=[]
    id_p=[]
    ID_all=ID_all.astype(int)
    for ids in ID_all:
        df_patient = get_patient(df, ids)
        val=df_patient[teller].isna().to_numpy()
        avg_hr=df_patient[teller].to_numpy()
        max_hr=df_patient[nevner].to_numpy()
    
        max_hr = max_hr[~val]
        avg_hr = avg_hr[~val]
        max_hr=convert_if_datetime(max_hr,debug)
        avg_hr=convert_if_datetime(avg_hr,debug)
        if debug:
            print(ids)
            print('nevner=',max_hr)
            print('teller=',avg_hr)
        if(np.nansum(max_hr)==0):
            print("Advarsel!, "+ nevner+" blir null for ID: {:8d}".format(ids)+ ", sjekk data!")
            hr_p.append(float('NaN')) 
        else:
            hr_p.append(np.nansum(avg_hr)/np.nansum(max_hr)*100)
        id_p.append(ids)
    return np.array(id_p),np.array(hr_p)

def convert_if_datetime(vec,debug=False):
    """
    returnerer en array i minutter, hvis noen elementer er datetime.time
    """
    is_datetime=False
    for elem in vec:
        if isinstance(elem,datetime.time):
            is_datetime=True
            break
    if not is_datetime:
        return vec
    else:
        l=[]
        for elem in vec:
            if isinstance(elem,datetime.time):
                li=float(elem.hour*60.+elem.minute+elem.second/60.)
                l.append(li)
            else:
                l.append(float(elem))
        return np.array(l)

def statistics_patient(df, ID_list):
    for ID in ID_list:
        print("-------------------------------------")
        print(ID)
        print(df["Time_in_zone"][df["ID"] == ID].astype(float).describe())
        print("-------------------------------------")
    return 0


def get_combined_data(path: str, subname: str, avoid_folder: str,debug=False):
    """
    Henter data fra excel filer og kombinerer dataen i en dataframe (en slags tabell man kan jobbe med i python)

    Parameters
    ----------
    path : str
        Filvei til mappene som inneholder dataen som skal samles/kombineres.
    subname : str
        Felles navn som alle datafilene inneholder.
    avoid_folder : str
        Navn på mappe eller fil som skal unngås. Nyttig hvis en annen fil inneholder subname, men skal ikke være en del av den samlede dataen.

    Returns
    -------
    DataFrame
        Tabell som inneholder all dataen.

    """
    if debug:
        print("starting..")
    
    final_df = pd.DataFrame()
    column_names = ["ID", "HR_max", "Betablocker", "Nr_treatment", "Site", "Date", "reason_cancelled", "starttime", "Endtime", "Polar_time", "Time_in_zone", "treatment_time", "percent_time_in_zone" ,"Peak_HR",
                    "Avg_HR", "RPE_mean", "Time_RPE_target", "HIGT_percent","GT_percent", "Lex_percent","Uex_percent", "Transfers_percent", "Wheelchair_percent", "Balance_percent", "stb_persent", "outcome_percent", "passive_percent", "session_percent","HIGT_min", "GT_min", "Lex_min", "Uex_min", "UexTS_min", "Transfers_min", "Wheelchair_min", "Balance_min",
                    "outcome_min", "Passive_min", "Other_min", "Other_comment"]
    for subdir, dirs, files in os.walk(path): # iterates through files, starting from root "path"
        for file in files:
#            print(os.path.join(subdir, file))
 #           print(file)
            if avoid_folder in os.path.join(subdir, file):
                break
            if subname.lower() in file.lower():
                try:
                    df = pd.read_excel(os.path.join(subdir, file), skiprows=[0], names = column_names) #gets excel file as dataframe
                    final_df = final_df.append(df) #adds dataframes together
                    if debug:
                        print('Reading ', file, ', shape=', df.shape)
                except:
                    pass
                #if(len(df.columns) != len(column_names)):
                 #   print("Error: Number of columns do not match in file: " + os.path.join(subdir, file))
                  #  return 0
    if debug:
        print("finnished..")
                
    return final_df
    

def combine_files(path: str, subname: str, combined_filename: str, avoid_folder:str):
    """
    Parameters
    ----------
    path : str
        Filvei til mappene som inneholder dataen som skal samles/kombineres.
    subname : str
        Felles navn som alle datafilene inneholder.
    combined_filename : str
        Navn på excel filen som inneholder all dataen.
    avoid_folder : str
        Navn på mappe eller fil som skal unngås. Nyttig hvis en annen fil inneholder subname, men skal ikke være en del av den samlede dataen.


    Returns
    -------
    None.

    """
    
    combined_data = get_combined_data(path, subname, avoid_folder)
    new_file_path = path + "\\" + combined_filename
    combined_data.to_excel(new_file_path)
    
def describe(df):
    df.describe()
    print("\n header: \n")
    df.head()
    return 0

#########figur av SMWT på alle måletidspunkt#####
def get_spss_data(path = "Z:\\Anacondatest", files = ["FIRST_ADM_2021.12.06_1", "FIRST_wk1_2021.12.06", "FIRST_wk2_2021.12.06", "FIRST_wk3_2021.12.03", "FIRST_wk4_2021.11.26", "FIRST_wk5_2021.11.26","FIRST_DC_2021.12.03", "FIRST_3M_2021.12.14"], 
                  columns = ["SixMWT_distance_adm", "SixMWT_distance_wk1", "SixMWT_distance_wk2", "SixMWT_distance_wk3", "SixMWT_distance_wk4", "SixMWT_distance_wk5", "SixMWT_distance_dc", "SixMWT_distance_3m"]):
    idx = 0
    final_df = pd.DataFrame()
    for file in files:
        file_path = os.path.join(path, file) + ".xlsx"
        #try:
        temp = pd.read_excel(file_path, usecols = columns[idx], dtype = object)
        final_df = final_df.append(temp)
        #except:
        #    print("Error: Was not able to read file " + file + ".")
        idx +=1
    return final_df


def plot(x, y, std, title:str, ymax:float, xlabel = "", ylabel = ""):   
    plt.figure(figsize = (12,7))
    plt.title(title, size = 24)
    plt.ylim(0,ymax)
    plt.xlabel(xlabel, size = 20)
    plt.ylabel(ylabel, size = 20)
    plt.xticks(fontsize = 18)
    plt.yticks(fontsize = 18)
    plt.errorbar(x, y, std, linewidth = 3.0)
    plt.scatter(x, y, s = 100)
    plt.show()
             
def table_statistic(file_name,col_names):
    '''
    file_name: name of spps file e.g. "FIRST_ADM_2022.01.18.sav"
    continous: list of continous variables e.g. ['Age', 'Height']
    categorical: list of categorical variables e.g. ['Gender','Stroke Type']
    returns pandas dataframe
    '''

    data={}
    m1=[]
    m2=[]
    s1=[]
    s2=[]
    names=[]
    try:
        df=pd.read_spss(file_name)
    except:
        print('Could not open file ' + file_name)
        return
    continous,categorical=get_category(df,col_names)
    if not continous == []:
        m1,s1=get_all_columns_from_dataframe(df,continous)
    if not categorical ==[]:
        names,m2,s2=get_all_categorical_from_dataframe(df,categorical)
    data['Type']=continous+names
    data['Middelverdi']=m1+m2
    data['Standardavvik']=s1+s2
    return pd.DataFrame(data)

def get_category(df,col_names):
    cont=[]
    cat=[]
    for col in col_names:
        try:
            val=df[col]
            if val.dtype.name == 'category':
                cat.append(col)
            else:
                cont.append(col)
        except:
            print('No column named ' + col)
    return cont,cat
        
def get_all_columns_from_dataframe(df,col_names):
    m=[]
    s=[]
    for col_name in col_names:
        mi,si=get_col_from_dataframe(df,col_name)
        m.append(mi)
        s.append(si)
    return m,s
def unpack_list(t):
    return [item for sublist in t for item in sublist]


def get_all_categorical_from_dataframe(df,col_names):
    names=[]
    counts=[]
    freqs=[]
    for col in col_names:
        name,count,freq=category_stats(df[col])
        names.append(name)
        counts.append(count)
        freqs.append(freq)
    return unpack_list(names),unpack_list(counts),unpack_list(freqs)
    
def get_col_from_dataframe(df,col_name):
    '''
    col_name (string) - a single name
    returns average an std dev of a single column in dataframe df if 
    col_name is not found it returns NaN
    '''
    try:
        a=df[col_name]
    except:
        print('column ' + col_name +' is not in dataframe')
        a=[]
    return get_simple_stats(a)

def get_simple_stats(col):
    if len(col)>0:
        return np.nanmean(col),np.nanstd(col)
    else:
        return float('NaN'), float('NaN')
        
def category_stats(col):
    names=[]
    freq_l=[]
    count_l=[]
    if col.dtype.name == 'category':
        val=np.array(col.value_counts())
        if len(val)==1:
            freq_l.append(1)
            count_l.append(val[0])
            names.append(col.cat.categories[0])
        elif len(val)==2:
            freq_l.append(val[0]/(val[0]+val[1]))
            count_l.append(float(val[0]))
            names.append(col.cat.categories[0])
        else:
            for idx,vali in enumerate(val):
                freq_l.append(vali/sum(val))
                count_l.append(vali)
                names.append(col.cat.categories[idx])
    else:
        print(col.name + 'Is not a categorical value')
    return names,count_l,freq_l
        





def gjennomsnitt_test(files, columns=[], mappe="//ihelse.net/Forskning/hst/ID1321/" ):
    m=[]
    s=[]
    if columns==[]:
        all_col=True
    else:
        all_col=False
    for file in files:
        print('reading file ', file)
        df=pd.read_spss(mappe+file)
        if all_col:
            columns=df.columns
        for col_name in columns:
            try:
                a=df[col_name]
                m.append(a.mean())
                s.append(a.std())
                print(col_name, ' middelverdi= ', a.mean(), 'standardavvik= ', a.std())
            except:
                pass
    return m,s

