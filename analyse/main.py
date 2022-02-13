# -*- coding: utf-8 -*-
"""
Created on Thu Dec 23 08:37:09 2021

@author: kajah
"""
#%%
import file as f
import pandas as pd
#%%

#%%
path="Z:\\Anacondatest"

combined = f.get_combined_data(path, subname = "Clinical", avoid_folder = "Gamle",debug=True)
#f.describe(combined)

#f.combine_files(path, subname = "Clinical", combined_filename = "XXXClinical_Combined.xlsx", avoid_folder = "Gamle")


#%%

#%%
pd.set_option("display.max_columns", None)
print(combined.describe())
print(combined.head())
print("nr 6017: ", combined[["HR_max", "Avg_HR"]][combined["ID"] == 6017])
#print(combined["Polar_time"][10])
#print(combined["Endtime"][10]-combined["starttime"][10])

#%%

#%%
#print(f.hr_percent(combined, 6017))
f.statistics_patient(combined, 6017)
f.statistics_patient(combined, combined["ID"])

#%%
f.hr_percent(combined, all_id=True)

#%%

spss_data = f.get_spss_data()
print(spss_data.head())
#%%

#%%

std = [172.6830, 205.2286, 176.7577, 161.1435, 201.1390, 77.7817, 211.8569, 136.6441]
x = ["adm", "wk1", "wk2","wk3","wk4","wk5", "dc", "3mo"]
y = [173.979, 242.878, 226.200, 239.150, 287.250, 364.000, 306.553, 491.063]

f.plot(x, y, std, title = "six minute walk test", ymax=700, xlabel = "Time", ylabel = "Distance [m]")
#%%