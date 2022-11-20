#%%
import numpy as np
from datetime import date
import pathlib as pt

p=pt.Path('../../polar_data/6057')
#%%
today = date.today()
print("Today's date:", today)

a=[]
if a == []:
    print('ja')

print('You have not collected any data, press Y and <enter> to continue')
ans=input()
if ans == 'Y' or ans =='y':
    cont=True
else:
    cont=False
print(cont)
# %%
