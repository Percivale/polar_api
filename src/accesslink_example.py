#!/usr/bin/env python

from __future__ import print_function
from typing import final
from accesslink.endpoints import resource, transaction

from utils import load_config, save_config, pretty_print_json
from accesslink import AccessLink
import pandas as pd
import requests
import numpy as np


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

        self.running = True
        self.show_menu()

    def show_menu(self):
        while self.running:
            print("\nChoose an option:\n" +
                  "-----------------------\n" +
                  #"0) test new funcs \n" +
                  "1) Get all data\n"+
                  "2) Exit\n" +
                  "3) Trykk på 3 for å få excel fil\n"+
                  "-----------------------")
            self.get_menu_choice()

    def get_menu_choice(self):
        choice = input("> ")
        {
            "2": self.exit,
            #"0": print("Seconds to hours:\n ", self.sec_to_hours([3600, 20000, 12112]), "Index column test:\n ", self.index_col(["02.12.2021","02.12.2021", "03.12.2021", "04.12.2021", "04.12.2021"])),
            "1":self.get_available_data,
            "3":self.format_excel,

        }.get(choice, self.get_menu_choice)()

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
            if item["data-type"] == "EXERCISE":
                self.get_exercises()
            elif item["data-type"] == "ACTIVITY_SUMMARY":
                self.get_daily_activity()
            elif item["data-type"] == "PHYSICAL_INFORMATION":
                self.get_physical_info()

    def get_available_data(self):
        all_data = pd.DataFrame()
        nights = self.get_sleep2()["nights"]

        sleep_data = pd.DataFrame.from_dict(nights)
        print(sleep_data)
        all_data = all_data.append(sleep_data)

        nr = self.get_nightly_recharge2()["recharges"]
        nightly_recharge = pd.DataFrame.from_dict(nr)
        all_data = all_data.merge(nightly_recharge, on = "date")
        #all_data = all_data.append(nightly_recharge)
        print(nightly_recharge)
        path = "sleep.xlsx"  
        print("Exporting sleep data to excel file... " + path)
 #       path = input("Enter the path and name of the excel file:\n (example: C:\\User\\MyFiles\\Polar_data\\Exercise_summary.xlsx)\n")
               
        all_data.to_excel(path)

        available_data = self.accesslink.pull_notifications.list()

        if not available_data:
            print("No new data available.")
            return

        print("Available data:")
        pretty_print_json(available_data)

        for item in available_data["available-user-data"]:
            print("Datatypes: ", item["data-type"])
            
            if item["data-type"] == "EXERCISE":
                print("Collecting exercise data....")
                excercise_summary = self.get_exercises()
                if len(excercise_summary) >0:
                    df_exercise_summary = pd.DataFrame()
                    for exercise in excercise_summary:
                        df_exercise = pd.DataFrame.from_dict(exercise, orient = "index").T
                        df_exercise_summary = df_exercise_summary.append(df_exercise)
                    
                    path = "exercise.xlsx"  
                    print("Exporting exercise data to excel file... " + path)
                    #path = input("Enter the path and name of the excel file:\n (example: C:\\User\\MyFiles\\Polar_data\\Exercise_summary.xlsx)\n")
                    df_exercise_summary.to_excel(path)
                

            elif item["data-type"] == "ACTIVITY_SUMMARY":
                print("Collecting activity summary data....")
                activity_summary, act_zones = self.get_daily_activity()
                if len(activity_summary)>0:
                    df_activity_summary = pd.DataFrame()
                    df_act_zones=pd.DataFrame()
                    for idx,activity in enumerate(activity_summary):
                        df_activity = pd.DataFrame.from_dict(activity, orient = "index").T
                        df_activity_z = pd.DataFrame.from_dict(act_zones[idx], orient = "index").T

                        df_activity_summary = df_activity_summary.append(df_activity)
                        df_act_zones = df_act_zones.append(df_activity_z)
                    path = "activity.xlsx"  
                    print("Exporting activity data to excel file... " + path)
                    #path = input("Enter the path and name of the excel file:\n (example: C:\\User\\MyFiles\\Polar_data\\Activity_summary.xlsx)\n")
                    df_activity_summary.to_excel(path)
                    path = "activity_zones.xlsx"  
                    print("Exporting activity data to excel file... " + path)
                    #path = input("Enter the path and name of the excel file:\n (example: C:\\User\\MyFiles\\Polar_data\\Activity_summary.xlsx)\n")
                    df_act_zones.to_excel(path)

            elif item["data-type"] == "PHYSICAL_INFORMATION":
                print("Collecting physical information...")
                physical_info_summary = self.get_physical_info()
                if len(physical_info_summary)>0:
                    df_physical_info_summary = pd.DataFrame()
                    for physical_info in physical_info_summary:
                        df_physical_info = pd.DataFrame.from_dict(physical_info, orient = "index").T
                        df_physical_info_summary = df_physical_info_summary.append(df_physical_info)
                    path = "physical_info.xlsx"  
                    print("Exporting physical info to excel file... " + path)
                    #path = input("Enter the path and name of the excel file:\n (example: C:\\User\\MyFiles\\Polar_data\\Physical_information_summary.xlsx)\n")
                    df_physical_info_summary.to_excel(path)

            
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
        exercises = []
        for url in resource_urls:
            exercise_summary = transaction.get_exercise_summary(url)
            exercise_hr = transaction.get_heart_rate_zones(url)
            exercises.append(exercise_hr)
            print("Exercise summary:")
            pretty_print_json(exercise_summary)
            exercises.append(exercise_summary)
        transaction.commit()
        return exercises

    def get_sleep(self):
        transaction = self.accesslink.sleep.create_transaction(user_id = self.config["user_id"],
                                                                access_token = self.config["access_token"])
        if not transaction:
            print("No sleep data available")
            return
        resource_urls = transaction.list_sleep()["sleep"]
        sleep_data = []

        for url in resource_urls:
            sleep_summary = transaction.get_sleep_summary(url)
            print("Sleep summary:")
            pretty_print_json(sleep_summary)
            sleep_data.append(sleep_summary)
        transaction.commit()
        return sleep_data

    def get_sleep2(self):
        headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer 2607ed26a2f65697e2b7378842710f62'
        }

        r = requests.get('https://www.polaraccesslink.com/v3/users/sleep', params={

        }, headers = headers)
        print(type(r))
        return r.json()

    def get_nightly_recharge2(self):
        headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer 2607ed26a2f65697e2b7378842710f62'
        }

        r = requests.get('https://www.polaraccesslink.com/v3/users/nightly-recharge', params={

        }, headers = headers)

        #print(type(r))
        #print(r.json())
        return r.json()


    def get_nightly_recharge(self):
        transaction = self.accesslink.nightly_recharge.create_transaction(user_id = self.config["user_id"],
                                                                access_token = self.config["access_token"])
        if not transaction:
            print("No nightly recharge data available")
            return
        resource_urls = transaction.list_nightly_recharge()["nightly_recharge"]
        nightly_recharge_data = []

        for url in resource_urls:
            nightly_recharge_summary = transaction.get_nightly_recharge_summary(url)
            #print("Nightly Recharge summary:")
            #pretty_print_json(nightly_recharge_summary)
            nightly_recharge_data.append(nightly_recharge_summary)
        transaction.commit()
        return nightly_recharge_data

    def get_daily_activity(self):
        transaction = self.accesslink.daily_activity.create_transaction(user_id=self.config["user_id"],
                                                                        access_token=self.config["access_token"])
        if not transaction:
            print("No new daily activity available.")
            return

        resource_urls = transaction.list_activities()["activity-log"]
        activities = []
        act_zones=[]
        for url in resource_urls:
            activity_summary = transaction.get_activity_summary(url)
            activity_zones = transaction.get_zone_samples(url)  ##Hvis du tar med activity_zones får du med heart rate zones
            activities.append(activity_summary)
            act_zones.append(activity_zones)
            print("Activity summary:")
            pretty_print_json(activity_summary)
        

        transaction.commit()
        return activities,act_zones

    def get_physical_info(self):
        transaction = self.accesslink.physical_info.create_transaction(user_id=self.config["user_id"],
                                                                       access_token=self.config["access_token"])
        if not transaction:
            print("No new physical information available.")
            return

        resource_urls = transaction.list_physical_infos()["physical-informations"]
        physical_info_summary = []
        for url in resource_urls:
            physical_info = transaction.get_physical_info(url)
            
            physical_info_summary.append(physical_info)
            print("Physical info:")
            pretty_print_json(physical_info)

        transaction.commit()
        return physical_info_summary

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

    def get_dataframes(self):
        """
        Samler all data fra Polar API og samler det i en dataframe. 
        """

        ####Sleep and nightly recharge####
        all_data = pd.DataFrame()
        nights = self.get_sleep2()["nights"]

        sleep_data = pd.DataFrame.from_dict(nights)
        sleep_data["Timer_nattesøvn"] = (sleep_data["light_sleep"] + sleep_data["deep_sleep"] + sleep_data["rem_sleep"] + sleep_data["unrecognized_sleep_stage"] +
                                        sleep_data["total_interruption_duration"])

        sleep_data["light_sleep"] = self.sec_to_hours(sleep_data["light_sleep"])
        sleep_data["deep_sleep"] = self.sec_to_hours(sleep_data["deep_sleep"])
        sleep_data["rem_sleep"] = self.sec_to_hours(sleep_data["rem_sleep"])
        sleep_data["Timer_nattesøvn"] = self.sec_to_hours(sleep_data["Timer_nattesøvn"])
        sleep_data["unrecognized_sleep_stage"] = self.sec_to_hours(sleep_data["unrecognized_sleep_stage"])
        sleep_data["total_interruption_duration"] = self.sec_to_hours(sleep_data["total_interruption_duration"])

        print(sleep_data)
        all_data = all_data.append(sleep_data, ignore_index=True)


        nr = self.get_nightly_recharge2()["recharges"]
        nightly_recharge = pd.DataFrame.from_dict(nr)

        all_data = all_data.merge(nightly_recharge, on = "date")
        all_data = all_data.sort_values(by ='date')
        all_data = all_data.reset_index(drop = True)

        #print(all_data.columns)
        print("ALL DATA: ", all_data.columns)

        available_data = self.accesslink.pull_notifications.list()

        if not available_data:
            print("Only sleep and nightly recharge available.")
            return all_data

        print("Available data:")
        pretty_print_json(available_data)

        for item in available_data["available-user-data"]:
            print("Datatypes: ", item["data-type"])
            
            ######Exercise########
            if item["data-type"] == "EXERCISE":
                print("Collecting exercise data....")
                excercise_summary = self.get_exercises()  #henter exercise data
                if len(excercise_summary) >0:
                    df_exercise_summary = pd.DataFrame()
                    for exercise in excercise_summary:
                        df_exercise = pd.DataFrame.from_dict(exercise, orient = "index").T #gjør exercise data til dataframe
                        print(df_exercise.columns)

                        df_exercise_summary = df_exercise_summary.append(df_exercise, ignore_index=True)
                    df_exercise_summary[["date", "time"]] = df_exercise_summary["start-time"].str.split("T", expand = True) #Splitter start-time kolonnen i to; date og time. 
                    print(df_exercise_summary.columns)
                    #df_exercise_summary.drop("start-time")
                    df_exercise_summary = pd.concat([df_exercise_summary.drop(['heart-rate'], axis=1), df_exercise_summary['heart-rate'].apply(pd.Series)], axis=1) #splitter dataen i heart-rate i to: maximum-heartrate og average-heart-rate
                    df_exercise_summary = df_exercise_summary.rename(columns={"time":"Starttime_exercise", "duration":"Time_recorded_Polar", "average":"Average_HR_exercise", "maximum":"Peak_HR_exercise"})
                    try:
                        df_exercise_summary = df_exercise_summary.rename(columns={"training-load":"Vurdert_økt_belastning"}) 
                    except:
                        print("No training load available")
                    
                    try:
                        all_data = all_data.merge(df_exercise_summary, on="date") #slår sammen exercise data med den andre dataen basert på datoen. Må vær
                                                                                    #obs på at mer enn en exercise kan skje samme dagen....
                    except:
                        all_data = all_data.append(df_exercise_summary, ignore_index=True)
                
            #######Activity summary##########
            elif item["data-type"] == "ACTIVITY_SUMMARY":
                print("Collecting activity summary data....")
                activity_summary,act_zones = self.get_daily_activity()
                if len(activity_summary)>0:
                    df_activity_summary = pd.DataFrame()
                    for activity in activity_summary:
                        df_activity = pd.DataFrame.from_dict(activity, orient = "index").T
                        df_activity_summary = df_activity_summary.append(df_activity[["date", "active-steps"]]) #er bare interessert i skritt telling, og trenger date for å merge i rett rad
                    
                    ##Mer enn en activity summary kan komme for en dag. Da vil vi ha den som har mest steg for den dagen siden det er den dataen som er mest oppdatert
                    dictionary = {}
                    idx = 0
                    for date in df_activity_summary["date"]:
                        if date in dictionary.keys() and int(dictionary[date])<int(df_activity_summary["active-steps"]): #hvis datoen er i dictionary og antall steg
                            dictionary[date] = df_activity_summary.iloc[[idx]]["active-steps"]          #er mer for en annen dato, so bytter vi ut med et større antall steg
                        elif date not in dictionary.keys():
                            dictionary[date] = df_activity_summary.iloc[[idx]]["active-steps"] #hvis datoen er ny, så legger vi inn anntall steg
                        idx +=1
                    date_steps = pd.DataFrame.from_dict(dictionary, orient = "index").T #gjør dictionarien om til dataframe
                    print(date_steps)
                    all_data = all_data.merge(date_steps, on = "date") #merger anntall steg med resten av dataen
                    all_data.rename(columns = {"active-steps": "Polar_steps"})
                    
            ########Physical_information########
            elif item["data-type"] == "PHYSICAL_INFORMATION":
                print("Collecting physical information...")
                physical_info_summary = self.get_physical_info()
                if len(physical_info_summary)>0:
                    for physical_info in physical_info_summary:
                        df_physical_info = pd.DataFrame.from_dict(physical_info, orient = "index").T
                        print(df_physical_info.columns)
                        df_physical_info.rename(columns = {"resting-heart-rate":"Kontinuerligpuls_laveste", "maximum-heart-rate": "Kontinuerligpuls_høyeste", "vo2-max":"Fitnesstest_Vo2max"})
                        df_physical_info[["date", "time"]] = df_physical_info["created"].str.split("T", expand = True) #Splitter created kolonnen i dato og tid
                        all_data = all_data.merge(df_physical_info[["date", "Kontinuerligpuls_laveste", "Kontinuerligpuls_høyeste", "Fitnesstest_Vo2max"]], on = "date")
        return all_data
        

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

        df = self.get_dataframes()
        print(df)
        path = input("Write excel path:\n(example: C:\\User\\MyFiles\\Polar_data\\Exercise_summary.xlsx)\n")

        df.to_excel(path)
        
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

        print(df)
        path = input("Write excel path:\n")
        final_df.to_excel("all_data.xlsx")
        return 0


if __name__ == "__main__":
    PolarAccessLinkExample()