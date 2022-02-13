def get_sleep_from_json(fsleep='sleep.json',fnrch='nightly_recharge.json'):
    '''
    Kaja sin kode
    '''
    f = open(fsleep)
    nights=json.load(f)
    f.close()
    f = open(fnrch)
    nr=json.load(f)
    f.close()
    nights=nights["nights"]
    nr=nr["recharges"]
    all_data = pd.DataFrame()
    sleep_data = pd.DataFrame.from_dict(nights)
    print(sleep_data)
    all_data = all_data.append(sleep_data)
    nightly_recharge = pd.DataFrame.from_dict(nr)
    all_data = all_data.merge(nightly_recharge, on = "date")
    #all_data = all_data.append(nightly_recharge)
    print(nightly_recharge)
    path = "sleep_ah.xlsx"  
    print("Exporting sleep data to excel file... " + path)
    all_data.to_excel(path)

def get_excercise_from_json(froot_e='exercise', froot_hr='heart_rate_zones'):
    '''
    Kaja sin kode
    '''
    excercise_summary = []
    for id,file in enumerate(glob.glob(froot_e+'*.json')):
            print(file)
            f = open(file)
            excercise_summary.append( json.load(f))
            f.close()
            f=open(froot_hr+str(id)+'.json')
            excercise_summary.append( json.load(f))
            f.close()  
    if len(excercise_summary) >0:
            df_exercise_summary = pd.DataFrame()
            for exercise in excercise_summary:
                df_exercise = pd.DataFrame.from_dict(exercise, orient = "index").T
                df_exercise_summary = df_exercise_summary.append(df_exercise)          
            path = "exercise_ah.xlsx"  
            print("Exporting exercise data to excel file... " + path)
            #path = input("Enter the path and name of the excel file:\n (example: C:\\User\\MyFiles\\Polar_data\\Exercise_summary.xlsx)\n")
            df_exercise_summary.to_excel(path)  

