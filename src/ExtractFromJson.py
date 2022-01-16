#%%
import json
import numpy as np
import os,glob
import datetime
import pandas as pd

from numpy.lib.arraysetops import unique

class JsonPolar:
    def __init__(self,sleep_file='',rch_file='',
                 exer_f_list=[],hr_f_list=[],act_z_list=[],
                 act_sum_list=[],phys_info_list=[]):
        # file root names
        self.sleep_root='sleep'
        self.nightly_rc_root='nightly_recharge'
        self.exer_root='exercise'
        self.hr_root ='heart_rate_zones'
        self.act_zone_root='act_zone'
        self.act_sum_root='act_sum'
        self.ext='.json'
        if sleep_file=='':
            self.sleep_flist=self.find_files(self.sleep_root)
        else:
            self.sleep_flist=sleep_file
        if rch_file == '':
            self.nightly_rch_flist=self.find_files(self.nightly_rc_root)
        else:
            self.nightly_rch_flist=rch_file
        if exer_f_list == []:
            self.exer_flist=self.find_files(self.exer_root)
        else:
            self.exer_flist=exer_f_list
        if hr_f_list == []:
            self.hr_flist=self.find_files(self.hr_root)
        else:
            self.hr_flist=hr_f_list
        if act_z_list == []:
            self.act_zone_flist=self.find_files(self.act_zone_root)
        else:
            self.act_zone_flist=act_z_list
        if act_sum_list == []:
            self.act_sum_flist=self.find_files(self.act_sum_root)
        else:
            self.act_sum_flist=act_sum_list

        self.all_data = pd.DataFrame()
        self.df_all_sleep_data=pd.DataFrame()
        self.df_all_daily_activity=pd.DataFrame()
        self.df_sleep_daily_act=pd.DataFrame()
        self.zone=[0,1,2,3,4,5] # activitets soner 0=1, 1=2, etc.

        
        # collect and store all data in self.df_all_sleep_data
        self.get_sleep()
        self.get_nightly_recharge()
        # --------------all sleep data collected------------------------------------#
        self.my_write_to_excel(self.df_all_sleep_data,"sleep_tmp.xlsx")

        # collect all daily activity in self.df_all_daily_activity
        if self.get_daily_activity_zones():
            self.my_write_to_excel(self.df_all_daily_activity,"daily_activity_tmp.xlsx")

        # merge data 
        if(self.merge_activity_sleep()):
            self.my_write_to_excel(self.df_sleep_daily_act,"sleep_activity.xlsx")

    def my_write_to_excel(self,df,file_name):
        '''
        give user a chance to close excel file
        '''
        file_not_closed=True
        while file_not_closed:
            try:
                df.to_excel(file_name)
                file_not_closed=False
            except:
                print(" File "+file_name+" not closed, please close before continue")
                input("Press Enter to continue...")
        print('Wrote file: '+file_name)

    
    def merge_activity_sleep(self):
        if not self.df_all_sleep_data.empty and not self.df_all_daily_activity.empty:
            self.df_sleep_daily_act=self.df_all_sleep_data.set_index('date').join(self.df_all_daily_activity.set_index('date'))
            return True
        else:
            if self.df_all_sleep_data.empty:
                print('No sleep data, cannot merge with daily activity')
            if self.df_all_daily_activity.empty:
                print('No daily activity, cannot merge with sleep data')
            return False

        
    
    def get_daily_activity_zones(self):
        if len(self.act_zone_flist)>0:
            self.date_list, self.tot_time_in_zone_date,self.active_steps_daily,self.duration = self.get_tot_activity_zones_summary()
            self.df_all_daily_activity["date"]=self.date_list
            self.df_all_daily_activity["Activity_steps"]=self.active_steps_daily
            self.df_all_daily_activity["Polar_aktiv_tid"]=self.duration
            cat=['rest','seated','standing','walking','running','not_used']
            zone_name=['1_','2_','3_','4_','5_','0_']
            for idx,zone in enumerate(self.zone):
                name='Activity_zone_'+zone_name[idx]+cat[idx]
                self.df_all_daily_activity[name]=self.tot_time_in_zone_date[:,zone]
            self.df_all_daily_activity.set_index('date')
            return True
        else:
            print('No daily activity available')
            return False
        



    
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

            self.df_all_sleep_data = self.df_all_sleep_data.append(self.sleep_data, ignore_index=True)
            self.df_all_sleep_data.set_index('date')
        else:
            print('No sleep data available')
        
    def get_nightly_recharge(self):
        self.all_nightly_recharge=self.get_json_data(self.nightly_rc_root+ self.ext)
        if not self.all_nightly_recharge is False:
            self.nr=self.all_nightly_recharge["recharges"]

            self.nightly_recharge = pd.DataFrame.from_dict(self.nr)

            self.df_all_sleep_data = self.df_all_sleep_data.merge(self.nightly_recharge, on = "date")
            self.df_all_sleep_data = self.df_all_sleep_data.sort_values(by ='date')
            self.df_all_sleep_data = self.df_all_sleep_data.reset_index(drop = True)
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

    def convert_string_to_min(self,str_json,datetime=False):
        to_split=['H','M','S']
        conversion=[60,1,1./60]
        sep=[':',':','']
        total_time=0.
        total_time_str=''
        if str_json:
            str1=str_json.split('PT') #remove PT
            for idx,c in enumerate(to_split):
                str1=str1[1].split(c)
                if len(str1)==1:
                    str1.insert(0,'00')
                total_time += conversion[idx]*self.convert_to_float(str1[0])
                total_time_str += str1[0]+sep[idx]
            if not datetime:
                return total_time
            else:
                return total_time_str
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
            active_step=[]
            duration=[]
            for date in date_list:
                ti,act_step,di=self.get_tot_time_in_zone_date(date)
                time_zone_date.append(ti)
                active_step.append(act_step)
                duration.append(self.convert_string_to_min(di,datetime=True))

        else:
            print('No activity zones and summary data avilable')
            return False
 
        return np.array(date_list), np.array(time_zone_date),np.array(active_step),np.array(duration)



    def get_tot_time_in_zone_date(self,date,datetime=True):
        '''
        Searches json files in folder and returns the most up to 
        date zone data (currently the one with most minutes)
        '''
        total_time_zone=np.zeros(6)
        tot_active_steps=0
        for i,file in enumerate(self.act_sum_flist):
            f = open(file)
            data=json.load(f)
            if date == data['date']:
                fname2=self.act_zone_flist[i]
                time_in_file=self.get_zones_json_file(fname2)
                if np.sum(time_in_file) >= np.sum(total_time_zone):
                    total_time_zone=time_in_file
                    tot_active_steps=data['active-steps']
                    tot_duration=data['duration']
        if datetime:
            return self.convert_np_to_datetime(total_time_zone),tot_active_steps,tot_duration
        else:
            return total_time_zone,tot_active_steps,tot_duration

    def convert_np_to_datetime(self,arr):
        l=[]
        for elem in arr:
            l.append(str(datetime.timedelta(minutes=elem)))
        return l

if __name__=='__main__':
    Test=JsonPolar()
# %%
