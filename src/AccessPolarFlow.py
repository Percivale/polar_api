#!/usr/bin/env python

from __future__ import print_function
from typing import final
from accesslink.endpoints import resource, transaction

from utils import load_config, save_config, pretty_print_json, write_json
from accesslink import AccessLink
import pandas as pd
import requests
import numpy as np
import os
import shutil
import glob
import ExtractFromJson as EFJ
from datetime import date


try:
    input = raw_input
except NameError:
    pass


CONFIG_FILENAME = "config.yml"


class PolarAccessLinkExample(object):
    """Example application for Polar Open AccessLink v3."""

    def __init__(self):
        self.config = load_config(CONFIG_FILENAME)

        if "access_token" not in self.config:
            print("Authorization is required. Run authorization.py first.")
            return

        self.accesslink = AccessLink(client_id=self.config["client_id"],
                                     client_secret=self.config["client_secret"])
        self.sleep_file_="sleep.json"
        self.nightly_rch_file_="nightly_recharge.json"
        self.phys_info_file_list_=[]
        self.act_zone_file_list_=[]
        self.act_sum_file_list_=[]
        self.heart_rate_zone_file_list_=[]
        self.exer_file_list_=[]

        self.collected_data=False

        self.running = True
        self.show_menu()

    def show_menu(self):
        while self.running:
            print("\nChoose an option:\n" +
                  "-----------------------\n" +
                  "1) Get all data\n"+
                  "2) Formater data fra json til excel\n"+
                  "3) Exit\n" +
                  "-----------------------")
            self.get_menu_choice()

    def get_menu_choice(self):
        choice = input("> ")
        {
            "3": self.exit,
            #"0": print("Seconds to hours:\n ", self.sec_to_hours([3600, 20000, 12112]), "Index column test:\n ", self.index_col(["02.12.2021","02.12.2021", "03.12.2021", "04.12.2021", "04.12.2021"])),
            "1":self.get_available_data,
            "2":self.format_json,
        }.get(choice, self.get_menu_choice)()
    
    def format_json(self):
        cont=True
        if not self.collected_data:
            print('You have not collected any data, press [Y]/n to continue')
            ans=input()
            if ans == 'Y' or ans =='y' or ans=='':
                cont=True
            else:
                cont=False
        if cont:
            print('Converting json files to excel ....')
            JS=EFJ.JsonPolar(self.sleep_file_,self.nightly_rch_file_,self.exer_file_list_,
                            self.heart_rate_zone_file_list_,self.act_zone_file_list_,self.act_sum_file_list_,
                            self.phys_info_file_list_)
        else:
            print('Returning to main menu, choose 1, 2, or 3')
            return
            
        

    def get_user_information(self):
        user_info = self.accesslink.users.get_information(user_id=self.config["user_id"],
                                                          access_token=self.config["access_token"])
        pretty_print_json(user_info)

    def check_available_data(self):
        available_data = self.accesslink.pull_notifications.list()
        if not available_data:
            print("No new data available.")
            return
        print("Available data:")
        pretty_print_json(available_data)

        for item in available_data["available-user-data"]:
            print("Available data ", item["data-type"])
            if item["data-type"] == "EXERCISE":
                self.get_exercises()
            elif item["data-type"] == "ACTIVITY_SUMMARY":
                self.get_daily_activity()
            elif item["data-type"] == "PHYSICAL_INFORMATION":
                self.get_physical_info()
    
    def move_all_json_files(self):
        backup_dir='../old_data'
        try:
            os.mkdir(backup_dir)
        except:
            print('Directory '+ backup_dir+ ' exists')

        try:
            for file in glob.glob(r'*.json'):
                shutil.move(file, backup_dir)
                print(file,' --> ' +backup_dir+file)
        except:
            print('No files moved ')

    def change_directory(self):
        self.new_dir='../data/'+self.config["user_id"] + str(date.today())
        try:
            os.mkdir(self.new_dir)
            os.chdir(self.new_dir)
        except:
            print('Could not create directory ' + self.new_dir)
            print('Dumping all files in current directory')

    def get_available_data(self):
        self.collected_data=True
        # All sleep data to file
        write_json(self.get_sleep(),self.sleep_file_)
        write_json(self.get_nightly_recharge(),self.nightly_rch_file_)

        available_data = self.accesslink.pull_notifications.list()
        if not available_data:
            print('Only sleep and nightly recharge data available')
            print("No new data available.")
            return

        print("Available data:")
        pretty_print_json(available_data)

        for item in available_data["available-user-data"]:
            print("Datatypes: ", item["data-type"])
            if item["data-type"] == "EXERCISE":
                print("Collecting exercise data....")
                self.get_exercises() # writes json files                
            elif item["data-type"] == "ACTIVITY_SUMMARY":
                print("Collecting activity summary data....")
                self.get_daily_activity()
            elif item["data-type"] == "PHYSICAL_INFORMATION":
                print("Collecting physical information...")
                self.get_physical_info()
            
    def revoke_access_token(self):
        self.accesslink.users.delete(user_id=self.config["user_id"],
                                     access_token=self.config["access_token"])

        del self.config["access_token"]
        del self.config["user_id"]
        save_config(self.config, CONFIG_FILENAME)

        print("Access token was successfully revoked.")

        self.exit()

    def exit(self):
        self.running = False

    def get_exercises(self):
        transaction = self.accesslink.training_data.create_transaction(user_id=self.config["user_id"],
                                                                       access_token=self.config["access_token"])
        if not transaction:
            print("No new exercises available.")
            return

        resource_urls = transaction.list_exercises()["exercises"]
        fname='exercise'
        fname2='heart_rate_zones'
        for id,url in enumerate(resource_urls):
            exercise_summary = transaction.get_exercise_summary(url)
            exercise_hr = transaction.get_heart_rate_zones(url)
            print("Exercise summary:")
            pretty_print_json(exercise_summary)
            f1=fname + str(id)+".json"
            write_json(exercise_summary,f1)
            f2=fname2 + str(id)+".json"
            write_json(exercise_hr ,f2)
            self.exer_file_list_.append(f1)
            self.heart_rate_zone_file_list_.append(f2)

        transaction.commit()


    def get_sleep(self):
        headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + str(self.config["access_token"])
        }
        r = requests.get('https://www.polaraccesslink.com/v3/users/sleep', params={

        }, headers = headers)
        
        return r.json()

    def get_nightly_recharge(self):
        headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + str(self.config["access_token"])
        }

        r = requests.get('https://www.polaraccesslink.com/v3/users/nightly-recharge', params={

        }, headers = headers)

        return r.json()

    def get_daily_activity(self):
        transaction = self.accesslink.daily_activity.create_transaction(user_id=self.config["user_id"],
                                                                        access_token=self.config["access_token"])
        if not transaction:
            print("No new daily activity available.")
            return

        resource_urls = transaction.list_activities()["activity-log"]
        fname="act_sum"
        fname2="act_zone"
        id=0
        for url in resource_urls:
            id += 1
            print("daily activity url ",url)
            activity_summary = transaction.get_activity_summary(url)
            activity_zones = transaction.get_zone_samples(url)  ##Hvis du tar med activity_zones får du med heart rate zones
            print("Activity summary:")
            pretty_print_json(activity_summary)
            f1=fname + str(id)+".json"
            write_json(activity_summary,f1)
            print("Activity zones:")
            pretty_print_json(activity_zones)
            f2=fname2 + str(id)+".json"
            write_json(activity_zones,f2)
            self.act_sum_file_list_.append(f1)
            self.act_zone_file_list_.append(f2)
        transaction.commit()
        return 

    def get_physical_info(self):
        transaction = self.accesslink.physical_info.create_transaction(user_id=self.config["user_id"],
                                                                       access_token=self.config["access_token"])
        if not transaction:
            print("No new physical information available.")
            return

        resource_urls = transaction.list_physical_infos()["physical-informations"]
        fname='physical_information'
        for id,url in enumerate(resource_urls):
            physical_info = transaction.get_physical_info(url)
            print("Physical info:")
            pretty_print_json(physical_info)
            f1=fname + str(id)+".json"
            write_json(physical_info,f1)
            self.phys_info_file_list_.append(f1)

        transaction.commit()
        
    def format_time(self, time_column):
        """function that transform times like PT1H4M38.090S to 01:04:38"""

        return time_column

    def index_col(self, date_column):
        index1 = list(np.zeros(len(date_column)))
        index1[0] = 1
        for i in range(len(date_column)-1):
            if date_column[i] == date_column[i+1]:
                index1[i+1] = index1[i]
            else:
                
                index1[i+1] = int(index1[i]+1)

        return pd.Series(index1)

    def sec_to_hours(self, column):
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

    def format_excel(self):
        """
        Henter samlet dataframe med data fra daily-activity, exercise, physical-information, sleep og nightly recharge.
        Deretter forflytter den dataen inn i en ny dataframe med andre kolonnenavn, og et par ekstra kolonner i tillegg. 
        """

        columns = ["ID", "index1", "date", "Polar_steps", "Polar_time_walking", "Polar_time_running", "Ble_ikke_brukt_dag", "Ble_ikke_brukt_natt",
        "Kontinuerligpuls_laveste", "Kontinuerligpuls_høyeste", "Timer_nattesøvn", "Lett_søvn", "Dyp_søvn", "REM_søvn", "Avbrudd_søvn", "Sleep_HR",
        "Sleep_HRV", "Sleep_respiratory_frequency", "Nightly_Recharge_status", "ANS", "Sleepscore", "HRV_test", "HRV_stand", "Restitusjon", 
        "Fitnesstest_Vo2max", "Fitnesstest_vurdering", "Status_kardiobelastning", "VurderingStatusKardiobelastning", "TRIMP", "Belastning", "Toleranse",
        "Starttime_exercise", "Endtime_exercise", "Time_recorded_Polar", "Time in zone_1_grey", "Time in zone_2_blue", "Time in zone_3_green", "Time in zone_4_yellow",
        "Time in zone_4_yellow", "Time in zone_5_red", "Peak_HR_exercise", "Average_HR_exercise", "Vurdert_økt_belastning"]
        final_df = pd.DataFrame(columns = columns)

        #df = self.get_dataframes()
        #print(df)
        path = "Exercise_summary.xlsx"
        print('Writing to file: ' + path)

        #df.to_excel(path)
        
        try:
            final_df[["date", "Lett_søvn", "Timer_nattesøvn", "Dyp_søvn", "REM_søvn", "Avbrudd_søvn", "Sleep_HR",
            "Sleep_HRV", "Sleep_respiratory_frequency", "Sleepscore", "Nightly_Recharge_status", "ANS"]] = df[["date", "light_sleep", "Timer_nattesøvn", "deep_sleep", "rem_sleep",
            "total_interruption_duration", "heart_rate_avg", "heart_rate_variability_avg", "breathing_rate_avg", "sleep_score", "nightly_recharge_status", "ans_charge"]]
        except:
            print("sleep and recharge went wrong")

        final_df["index1"] = self.index_col(final_df["date"])

        try:
            final_df[["Kontinuerligpuls_laveste", "Kontinuerligpuls_høyeste"]] = df[["Kontinuerligpuls_laveste", "Kontinuerligpuls_høyeste"]]
        except:
            print("lacks physical info")

        try:
            final_df[["Starttime_exercise", "Endtime_exercise", "Time_recorded_Polar", "Peak_HR_exercise", "Average_HR_exercise"]] = df[["Starttime_exercise", "Endtime_exercise", "Time_recorded_Polar", "Peak_HR_exercise", "Average_HR_exercise"]]    
        except: 
            print("no exercise data")

        #print(df)
        #path = "all_data.xlsx"
        #print("Writing all data to file: "+ path)
        #final_df.to_excel(path)
        return 0


if __name__ == "__main__":
    PolarAccessLinkExample()