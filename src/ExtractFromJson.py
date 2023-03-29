#%%
import json
import numpy as np
import os,glob
import datetime
import pandas as pd
import utils as u
#from dateutil.parser import parse
#from numpy.lib.arraysetops import unique

class JsonPolar:
    def __init__(self,sleep_file='',rch_file='', load_file='',
                 exer_f_list=[],hr_f_list=[],act_z_list=[],
                 act_sum_list=[],phys_info_list=[]):
        # file root names
        self.sleep_root='sleep'
        self.sleep_col_to_skip=['polar_user_x','sleep_start_time',
        'sleep_end_time','device_id','continuity','continuity_class','unrecognized_sleep_stage',
        'sleep_rating','sleep_goal','short_interruption_duration','long_interruption_duration',
        'sleep_cycles','group_duration_score','group_solidity_score','group_regeneration_score',
        'hypnogram','heart_rate_samples','polar_user_y','beat_to_beat_avg','hrv_samples','breathing_samples',
        'ans_charge_status','sleep_charge']
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
        if load_file == '':
            self.load_file='training_load.json'
        else:
            self.load_file=load_file
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
        u.my_write_to_excel(self.df_all_sleep_data,"sleep_tmp.xlsx")

        # collect all daily activity in self.df_all_daily_activity
        if self.get_daily_activity_zones():
            u.my_write_to_excel(self.df_all_daily_activity,"daily_activity_tmp.xlsx")

        # merge data 
        if(self.merge_activity_sleep()):
            u.my_write_to_excel(self.df_sleep_daily_act,"sleep_activity.xlsx")
            self.clean_sleep("sleep_activity_clean.xlsx")
        
        # get exercise_data
        self.get_exercise()
        u.my_write_to_excel(self.df_exercise_summary,'exercise_tmp.xlsx',index=False)

        # get training load
        self.get_training_load()
        u.my_write_to_excel(self.df_training_load,'training_load.xlsx',index=False)
    
    def get_training_load(self):
        load_data=self.get_json_data(self.load_file)
        data={'date':[],'Status_kardiobelastning':[],'VurderingStatusKardiobelastning':[],
              'TRIMP':[],'Belastning':[],'Toleranse':[]}
        trans={'Status_kardiobelastning':'cardio_load_ratio','VurderingStatusKardiobelastning':'cardio_load_status',
              'TRIMP':'cardio_load','Belastning':'strain','Toleranse':'tolerance'}
        for li in load_data:
            data['date'].append(li['date'])
            for key in trans.keys():
                data[key].append(li[trans[key]])
        self.df_training_load=pd.DataFrame(data)
        self.df_training_load['date']=pd.to_datetime(self.df_training_load['date'])



        
    def add_col_if_not(self,df,col_names):
        for col in col_names:
            if col not in df.columns:
                print('Adding blank column : ', col)
                df[col]=" "
    
    def clean_sleep(self,file_name):
        new_order=['date','Activity_steps','Polar_aktiv_tid','Activity_zone_0_not_used',
        		'Activity_zone_1_rest','Activity_zone_2_seated','Activity_zone_3_standing',
                'Activity_zone_4_walking','Activity_zone_5_running','Timer_nattesøvn',
                'light_sleep','deep_sleep','rem_sleep','total_interruption_duration',
                'nightly_recharge_status','ans_charge','sleep_score','heart_rate_avg',
                'heart_rate_variability_avg','breathing_rate_avg']
        self.add_col_if_not(self.df_sleep_daily_act,self.sleep_col_to_skip)
        df2=self.df_sleep_daily_act.drop(self.sleep_col_to_skip,axis=1)
        df2['date']=pd.to_datetime(df2.index)
        print('drop succeeded')
        self.add_col_if_not(df2,new_order)
        df2=df2[new_order]
        u.my_write_to_excel(df2,file_name,index=False)

    

    
    def merge_activity_sleep(self):
        if not self.df_all_sleep_data.empty and not self.df_all_daily_activity.empty:
            self.df_sleep_daily_act=self.df_all_sleep_data.set_index('date').join(self.df_all_daily_activity.set_index('date'),how='outer')
            self.df_sleep_daily_act['date2']=pd.to_datetime(self.df_sleep_daily_act.index)
#            self.df_sleep_daily_act['date']=self.df_sleep_daily_act['date'].dt.strftime('%d.%m.%Y')
#            self.df_sleep_daily_act.set_index('date')
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
            try:
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

#                self.df_all_sleep_data = self.df_all_sleep_data.append(self.sleep_data, ignore_index=True)
                self.df_all_sleep_data = pd.concat([self.df_all_sleep_data,self.sleep_data],ignore_index=True)
                self.df_all_sleep_data.set_index('date')
            except:
                print('check file: ', self.sleep_root+self.ext, ' some data are missing')
        else:
            print('No sleep data available')
        
    def get_nightly_recharge(self):
        self.all_nightly_recharge=self.get_json_data(self.nightly_rc_root+ self.ext)
        if not self.all_nightly_recharge is False:
            try:
                self.nr=self.all_nightly_recharge["recharges"]

                self.nightly_recharge = pd.DataFrame.from_dict(self.nr)

                self.df_all_sleep_data = self.df_all_sleep_data.merge(self.nightly_recharge, on = "date")
                self.df_all_sleep_data = self.df_all_sleep_data.sort_values(by ='date')
                self.df_all_sleep_data = self.df_all_sleep_data.reset_index(drop = True)
            except:
                print('Check file: ', self.nightly_rc_root+ self.ext, ' data are missing' )
        else:
            print('No nightly recharge data available')
    
    def get_start_time(self,dict):
        T=parse(dict['start-time'])
        return 

    def get_exercise(self):
        if len(self.hr_flist)>0:
            times=['date','start_time','duration','heart_rate-qaverage','heart_rate-maximum']
            pt_times=['start-time','duration']
            ac_zone_names=['Activity_zone_0_not_used',\
                'Activity_zone_1_rest','Activity_zone_2_seated','Activity_zone_3_standing',\
                    'Activity_zone_4_walking']
            #df=pd.DataFrame(times+ac_zone_names)
            df=pd.DataFrame()
            dict={}
            for hr_file,exer_file in zip(self.hr_flist,self.exer_flist):
                exer_json=self.get_json_data(exer_file)
                T=parse(exer_json['start-time'])
                dict[times[0]]=[T.date()]
                dict[times[1]]=[T.time()]
                ll=str(datetime.timedelta(minutes=self.convert_string_to_min(exer_json.get('duration'))))
                ll=ll.split(".")[0] # remove microseconds
                dict[times[2]]=[ll]
                try:
                    dict[times[4]]=[exer_json.get('heart-rate')['maximum'] ] 
                    dict[times[3]]=[exer_json.get('heart-rate')['average']]    
                                  
                    in_zones=self.get_exer_zones_json_file(hr_file)
                    for idx,act in enumerate(ac_zone_names):
                        dict[act]=[in_zones[idx]]
#                    df=df.append(dict,ignore_index = True)
#                    self.df_exercise_summary=df
                except:
                    print('Could not get average or maximum heart rate for file')
                    print('exer_file '+exer_file)
                dfi=pd.DataFrame(dict)
                df=pd.concat([df,dfi],ignore_index=True)
            self.df_exercise_summary=df
        
    

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
        .....
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
        ''' activity zones '''
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

    def get_exer_zones_json_file(self,file_name):
        ''' exercise zones'''
        f = open(file_name)
        data = json.load(f)
#        print(data)
        zone_data=[]
        for d in data['zone']:
            d2=d.get('in-zone')
            zone_data.append(str(datetime.timedelta(minutes=self.convert_string_to_min(d2))))
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
            date_list= unique(date_list)
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
                    tot_active_steps=self.get_from_dict('active-steps',data)
                    tot_duration=self.get_from_dict('duration',data)
        if datetime:
            return self.convert_np_to_datetime(total_time_zone),tot_active_steps,tot_duration
        else:
            return total_time_zone,tot_active_steps,tot_duration
    
    def get_from_dict(self,name,dict):
        try:
            return dict[name]
        except:
            print('No ', name , ' available')
            return 0

    def convert_np_to_datetime(self,arr):
        l=[]
        for elem in arr:
            l.append(str(datetime.timedelta(minutes=elem)))
        return l

    def get_col_data(self,col_name,unique_name,df):
        try:
            return df.loc[df[col_name] == unique_name]
        except:
            print('Could not find data for '+ unique_name)
            return pd.DataFrame()
    


if __name__=='__main__':
#    os.chdir('test_data')
    try:
        os.chdir('../polar_data/REST_X/')
    except:
        print('Could not change directory')
        pass
    Test=JsonPolar()




# %%
