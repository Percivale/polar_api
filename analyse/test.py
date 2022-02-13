#%%
import pandas as pd
import os
import matplotlib.pyplot as plt
import numpy as np
import datetime
import file as f

print(os.getcwd())
#f.table_statistic("../data/FIRST_test_python_2022.01.20.sav",continous=['Age','Height'])

mappe='../data/'
df=pd.read_spss(mappe+"FIRST_test_python_2022.01.20.sav")
df['Gender'].dtype=='category'
a=df['Gender']
#f.category_stats(a)
#a=f.get_col_from_dataframe(df,'Age')
#a=f.get_all_columns_from_dataframe(df,['Age','Height'])
#b=f.table_statistic(mappe+"FIRST_test_python_2022.01.20.sav",continous=['Age','Height'],categorical=[])
n,m,s=f.category_stats(df['Gender'])# %%
f.table_statistic("../data/FIRST_test_python_2022.01.20.sav",['Age','Height','Gender','Gender','Type_stroke'])
# %%
