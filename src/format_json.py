#%%
import json
import numpy as np
import os,glob
import datetime
import pandas as pd

from numpy.lib.arraysetops import unique

class JsonPolar:
    def __init__(self):
        # file root names
        self.sleep_root='sleep'
        self.nightly_rc_root='nightly_recharge'
        self.exer_root='exercise'
        self.hr_root ='heart_rate_zones'
        self.act_zone_root='act_zone'
        self.act_sum_root='act_sum'
        self.ext='.json'

        self.sleep_flist=self.find_files(self.sleep_root)
        self.nightly_rch_flist=self.find_files(self.nightly_rc_root)
        self.exer_flist=self.find_files(self.exer_root)
        self.hr_flist=self.find_files(self.hr_root)
        self.act_zone_flist=self.find_files(self.act_zone_root)
        self.act_sum_flist=self.find_files(self.act_sum_root)

        self.all_data = pd.DataFrame()
        self.zone=[0,1,2,3,4,5] # activitets soner 0=1, 1=2, etc.

        self.date_list, self.tot_time_in_zone_date= self.get_tot_activity_zones_summary()
    
    def get_sleep(self):

        self.all_sleep_data=self.get_json_data(self.sleep_root+self.ext)
        if not self.all_sleep_data is False:
            self.nights=self.all_sleep_data['nights']
            self.sleep_data = pd.DataFrame.from_dict(self.nights)
            self.sleep_data["Timer_nattesøvn"] = (self.sleep_data["light_sleep"] + self.sleep_data["deep_sleep"] + self.sleep_data["rem_sleep"] + self.sleep_data["unrecognized_sleep_stage"] +
                                            self.sleep_data["total_interruption_duration"])

            self.sleep_data["light_sleep"] = self.sec_to_hours(self.sleep_data["light_sleep"])
            self.sleep_data["deep_sleep"] = self.sec_to_hours(self.sleep_data["deep_sleep"])
            self.sleep_data["rem_sleep"] = self.sec_to_hours(self.sleep_data["rem_sleep"])
            self.sleep_data["Timer_nattesøvn"] = self.sec_to_hours(self.sleep_data["Timer_nattesøvn"])
            self.sleep_data["unrecognized_sleep_stage"] = self.sec_to_hours(self.sleep_data["unrecognized_sleep_stage"])
            self.sleep_data["total_interruption_duration"] = self.sec_to_hours(self.sleep_data["total_interruption_duration"])

            self.all_data = self.all_data.append(self.sleep_data, ignore_index=True)
        else:
            print('No sleep data available')
        
    def get_nightly_recharge(self):
        self.all_nightly_recharge=self.get_json_data(self.nightly_rc_root+ self.ext)
        if not self.all_nightly_recharge is False:
            self.nr=self.all_nightly_recharge["recharges"]

            self.nightly_recharge = pd.DataFrame.from_dict(self.nr)

            self.all_data = self.all_data.merge(self.nightly_recharge, on = "date")
            self.all_data = self.all_data.sort_values(by ='date')
            self.all_data = self.all_data.reset_index(drop = True)
        else:
            print('No nightly recharge data available')
    
    def get_exercise(self):
        full_file_list=self.pair_list(self.hr_flist,self.exer_flist)
        print(full_file_list)
        self.all_exercise_data=self.get_json_file_list(full_file_list)
        if self.all_exercise_data is not False:
            self.df_exercise_summary = pd.DataFrame()
            for exercise in self.all_exercise_data:
                df_exercise = pd.DataFrame.from_dict(exercise, orient = "index").T #gjør exercise data til dataframe
                print(df_exercise)
                self.df_exercise_summary = self.df_exercise_summary.append(df_exercise, ignore_index=True)
            self.df_exercise_summary[["date", "time"]] = self.df_exercise_summary["start-time"].str.split("T", expand = True) #Splitter start-time kolonnen i to; date og time. 
            print(self.df_exercise_summary)
            #df_exercise_summary.drop("start-time")
            self.df_exercise_summary = pd.concat([self.df_exercise_summary.drop(['heart-rate'], axis=1), self.df_exercise_summary['heart-rate'].apply(pd.Series)], axis=1) #splitter dataen i heart-rate i to: maximum-heartrate og average-heart-rate
            self.df_exercise_summary = self.df_exercise_summary.rename(columns={"time":"Starttime_exercise", "duration":"Time_recorded_Polar", "average":"Average_HR_exercise", "maximum":"Peak_HR_exercise"})
            try:
                self.df_exercise_summary = self.df_exercise_summary.rename(columns={"training-load":"Vurdert_økt_belastning"}) 
            except:
                print("No training load available")
            try:
                self.all_data = self.all_data.merge(self.df_exercise_summary, on="date") #slår sammen exercise data med den andre dataen basert på datoen. Må vær
                                                                                    #obs på at mer enn en exercise kan skje samme dagen....
            except:
                self.all_data = self.all_data.append(self.df_exercise_summary, ignore_index=True)
        else:
            print('No exercise data available')
    
    def get_activity_summary(self):
        '''
        Kaja: Dette ser ikke ut til å virke
        '''
        self.all_activity_summary=self.get_json_file_list(self.act_sum_flist)
        if self.all_activity_summary is not False:
            self.df_activity_summary = pd.DataFrame()
            for activity in self.all_activity_summary:
                df_activity = pd.DataFrame.from_dict(activity, orient = "index").T
                self.df_activity_summary = self.df_activity_summary.append(df_activity[["date", "active-steps"]]) #er bare interessert i skritt telling, og trenger date for å merge i rett rad
            
            ##Mer enn en activity summary kan komme for en dag. Da vil vi ha den som har mest steg for den dagen siden det er den dataen som er mest oppdatert
            self.dictionary = {}
            for idx,date in enumerate(self.df_activity_summary["date"]):
                self.dictionary[date] = max(self.df_activity_summary.iloc[[idx]]["active-steps"])
            date_steps = pd.DataFrame.from_dict(self.dictionary, orient = "index").T #gjør dictionarien om til dataframe
            print(date_steps)
            self.all_data = self.all_data.merge(date_steps, on = "date") #merger anntall steg med resten av dataen
            self.all_data.rename(columns = {"active-steps": "Polar_steps"})
            print(self.all_data)
            
        else:
            print('No activity summary available')

    def get_json_file_list(self,list):
        data=[]
        for file in list:
            d=self.get_json_data(file)
            if(d):
                data.append(d)
            else:
                print('No data for:', file)
                return False
        return data

    def get_json_data(self,fname):
        try:
            f = open(fname)
            json_data=json.load(f)
            f.close()
            return json_data
        except:
            print('No data for: ', fname)
        return False

    def find_files(self,root_name,ext='*.json'):
        '''
        find all files in current directory with the given
        root name and extension and returns
        a list of files
        '''
        file_list=[]
        for file in glob.glob(root_name+'*'+self.ext):
            file_list.append(file)
        return file_list

    def sec_to_hours(self, column):
        '''
        Kaja: skriv doc streng
        '''
        hours = list(np.zeros(len(column)))
        minutes = list(np.zeros(len(column)))
        new_col = list(np.zeros(len(column)))
        for i in range(len(column)):
            hours[i] = int(int(column[i])//3600)
            minutes[i] = int(np.rint(int(column[i])%3600))//60
            #print(hours[i], ":", minutes[i])
            if len(str(minutes[i]))==2:
                new_col[i] = str(hours[i]) + ":" + str(minutes[i])
            else:
                new_col[i] = str(hours[i]) + ":0" + str(minutes[i])

        return pd.Series(new_col)

    def pair_list(self,list1,list2):
        '''
        adds one element from list 1 and list 2
        '''
        if(len(list1) == len(list2)):
            list=[]
            for idx,l1 in enumerate(list1):
                list.append(l1)
                list.append(list2[idx])
            return list
        print('Error : different length of lists')
        return None


    def convert_to_float(self,str_in):
        try:
            return float(str_in)
        except:
            return 0.

    def convert_string_to_min(self,str_json):
        to_split=['H','M','S']
        conversion=[60,1,1./60]
        total_time=0.
        if str_json:
            str1=str_json.split('PT') #remove PT
            for idx,c in enumerate(to_split):
                str1=str1[1].split(c)
                if len(str1)==1:
                    str1.insert(0,'0')
                total_time += conversion[idx]*self.convert_to_float(str1[0])
            return total_time
        else:
            print('Empty String : ', str_json)
            return 0
        
    def get_zones_json_file(self,file_name):
        f = open(file_name)
        zone_data=len(self.zone)*[0.]
        data = json.load(f)
        for d in data['samples']:
            d1=d['activity-zones']
            for z in self.zone:
                d2=d1[z]
                d3=d2.get('inzone')
                zone_data[z]+= self.convert_string_to_min(d3)
        return np.array(zone_data)

    def get_tot_activity_zones_summary(self):
        '''
        returns date and tot activity in each zone as a list for
        each date
        '''
        date_list=[]
        if len(self.act_zone_flist)>0:
            for file in self.act_sum_flist:
                f = open(file)
                data=json.load(f)
                date_list.append(data['date'])
                f.close()
            date_list=unique(date_list)
            time_zone_date=[]
            for date in date_list:
                time_zone_date.append(self.get_tot_time_in_zone_date(date))
        else:
            print('No activity zones and summary data avilable')
            
        return date_list, time_zone_date



    def get_tot_time_in_zone_date(self,date,datetime=True):
        '''
        Searches json files in folder and returns the most up to 
        date zone data (currently the one with most minutes)
        '''
        total_time_zone=np.zeros(6)
        for i,file in enumerate(self.act_sum_flist):
            f = open(file)
            data=json.load(f)
            if date == data['date']:
                fname2=self.act_zone_flist[i]
                time_in_file=self.get_zones_json_file(fname2)
                if np.sum(time_in_file) >= np.sum(total_time_zone):
                    total_time_zone=time_in_file
        if datetime:
            return self.convert_np_to_datetime(total_time_zone)
        else:
            return total_time_zone

    def convert_np_to_datetime(self,arr):
        l=[]
        for elem in arr:
            l.append(str(datetime.timedelta(minutes=elem)))
        return l
#read_sleep()
#read_excercise()
Test=JsonPolar()
Test.get_sleep() 
Test.get_nightly_recharge()
Test.all_data.to_excel("tmp.xlsx")
Test.get_exercise()
Test.all_data.to_excel("tmp2.xlsx")  # blir bare tull

print(Test.date_list)
print(Test.tot_time_in_zone_date)


#Test.get_activity_summary()

#%%
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
