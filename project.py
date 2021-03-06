# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 11:53:36 2018

@author: Frank
"""

#import os
import pandas as pd
import numpy as np
import datetime
from tqdm import tqdm
import multiprocessing
#import matplotlib.pyplot as plt



def initialize():
    print("Initialize")
    global dfcot
    global dfres   
    global dfbez
    file = "El Orteca Resorts - Data 20170703_20170813.xlsx"
    
    xl = pd.ExcelFile(file) #Inladen van excelbestand
    # Print the sheet names
#    print(xl.sheet_names)
    
    # Load a sheet into a DataFrame by name: df1
    dfcot = xl.parse('Cottages')
    dfres = xl.parse("Reservations")
    dfres = dfres.assign(Assigned = np.zeros(len(dfres), dtype = int))
    startdate = datetime.datetime(2017,7,3)
    index = []
    for i in range(0,60): #Maak lijst van alle beschikbare data als kolom-index
        index.append(startdate + datetime.timedelta(days = i))
    
    dfbez = pd.DataFrame(np.zeros((820,60), dtype=int),columns = index)
    opties = ['Face South', 'Near Playground', 'Close to the Centre', 'Near Lake ',
       'Near car park', 'Accessible for Wheelchair', 'Child Friendly',
       'Dish Washer ', 'Wi-Fi Coverage ', 'Covered Terrace']
    dfres=dfres.assign(NrUpgrade = dfres[opties].sum(axis =1))
    dfcot=dfcot.assign(NrUpgrade = dfcot[opties].sum(axis =1))
    
def is_val(res_id, cot_id):#kijkt of een combinatie reservering/huis geldig is
    options = ['Face South', 'Near Playground', 'Close to the Centre', 'Near Lake ',
       'Near car park', 'Accessible for Wheelchair', 'Child Friendly',
       'Dish Washer ', 'Wi-Fi Coverage ', 'Covered Terrace']
    if dfres.loc[res_id-1]['# Persons'] > dfcot.iloc[cot_id-1]['Max # Pers']:
        return(False) #Huis is te klein
    for opt in options:
        if (dfres.loc[res_id - 1][opt] == 1) and (dfcot.iloc[cot_id - 1][opt] == 0):
            return (False) #Voor alle extra opties, kijk of deze gevraagd en aanwezig zijn
    if dfres.iloc[res_id-1]['Class'] > dfcot.iloc[cot_id-1]['Class']:
        return(False) # Minimaal de juiste klasse?
    datum = dfres.loc[res_id-1]['Arrival Date']#Vraag de aankomstdatum op van de reservering
    col = dfbez.columns.get_loc(datum)#Bijbehorende kolom opvragen
    for i in range(0,dfres.loc[res_id-1]['Length of Stay']):#eerste dag mag bezet zijn als het de laatste is van de vorige
        if dfbez.loc[cot_id - 1][col + i] != 0:#Controleer of het huis al bezet is op die dag
            return(False)
    return(True) #Voldoet aan alle eisen
            
def assign(res_id, cot_id):#WIP, werkt nog niet
    datum = dfres.loc[res_id-1]['Arrival Date']
    col = dfbez.columns.get_loc(datum)
    duration = dfres.loc[res_id-1]['Length of Stay']
    dfbez.loc[cot_id -1][col:col+duration] += 1
#    print(cot_id -1,col,duration)
#    print(dfbez.loc[cot_id -1][col:col+duration+1] )
    dfres.loc[res_id - 1,'Assigned']=cot_id
#    print("Assigning ", res_id , " to ", cot_id)

def fixed_assign():        
    fixed = dfres.loc[dfres['Cottage (Fixed)'] != 0] #maak subselectie van reserveringen met fixed huisje
    print("Assigning first selection")
    for i in range(len(fixed)):   
        res_id = fixed.iloc[i]['ID'] 
        cot_id = fixed.iloc[i]['Cottage (Fixed)']
        assign(res_id,cot_id)



def class_assign(todo,dfcot_class,dfbez):
#    from tqdm import tqdm
#    todo = pair[0]
#    dfcot_class=pair[1]
    todo = todo.loc[todo['Assigned'] == 0]
#    todo = todo.sort_values(by=['Wi-Fi Coverage '],ascending =False)
    
    
#    todo = todo.sort_values(by=['Dish Washer '],ascending =False) 
    todo = todo.sort_values(by=['Length of Stay'],ascending =False)   
    todo = todo.sort_values(by=['# Persons'],ascending =False)
    
    todo = todo.sort_values(by=['NrUpgrade'],ascending = False)
                      
    dfcot_class = dfcot_class.sort_values(by=['NrUpgrade'],ascending=True)
    dfcot_class=dfcot_class.sort_values(by=['Max # Pers'],ascending= True)
#    todo=todo[0:10]
    for j in tqdm(todo.index):
        k=0
        match = False
        res_id = todo.loc[j,"ID"] 
        while k < len(dfcot_class) and match == False:
            if is_val(res_id, dfcot_class.iloc[k]["ID"]):
                assign(res_id,dfcot_class.iloc[k]["ID"])
                match = True
#                print("Assigning ",res_id,"to ",dfcot_class.iloc[k]["ID"])
            else:
                k+=1
    klasse = dfcot_class.iloc[1]['Class']           
    result = dfres.loc[dfres['Class']==klasse]
    return(result)          
    
def final_assign():
    print("Excecuting final iteration")

    todo = dfres.loc[dfres['Assigned'] == 0]
    
    
    todo = todo.sort_values(by=['Class'],ascending =False)
    todo = todo.sort_values(by=['# Persons'],ascending =False)
    todo = todo.sort_values(by=['Length of Stay'],ascending =False)       
#    todo=todo[0:10]
    for j in tqdm(todo.index):
        k=0
        match = False
        res_id = todo.loc[j,"ID"] 
        while k < len(dfcot) and match == False:
            if is_val(res_id, dfcot.iloc[k]["ID"]):
                assign(res_id,dfcot.iloc[k]["ID"])
                match = True
#                print("Assigning ",res_id,"to ",dfcot_class.iloc[k]["ID"])
            else:
                k+=1
                
    print(len(dfres.loc[dfres["Assigned"]==0]), 'Personen nog niet ingedeeld')
if not 'dfcot' in globals():#Waar als deze nog niet bestaat
    initialize()
    fixed_assign()
    

if __name__ == '__main__':
#    multiprocessing.set_start_method('fork')
    print("Commence Threading")
    __spec__ = "ModuleSpec(name='builtins', loader=<class '_frozen_importlib.BuiltinImporter'>)"
    dfres_1 = dfres.loc[dfres['Class']  == 1]
    dfres_2 = dfres.loc[dfres['Class']  == 2]
    dfres_3 = dfres.loc[dfres['Class']  == 3]
    dfres_4 = dfres.loc[dfres['Class']  == 4]
    
    dfcot_1 = dfcot.loc[dfcot['Class'] == 1]
    dfcot_2 = dfcot.loc[dfcot['Class'] == 2]
    dfcot_3 = dfcot.loc[dfcot['Class'] == 3]
    dfcot_4 = dfcot.loc[dfcot['Class'] == 4]
    
    classification = [[dfres_1,dfcot_1,dfbez],
                      [dfres_2,dfcot_2,dfbez],
                      [dfres_3,dfcot_3,dfbez],
                      [dfres_4,dfcot_4,dfbez]]
#    classification = [[dfres_1,dfcot_1,dfbez]]
    pool = multiprocessing.Pool(4)
    dfres = pd.concat(pool.starmap(class_assign,classification))
    pool.close()
    pool.join()
    print(' ')
    print('Reconstructing availibility dataframe')
    done = dfres.loc[dfres['Assigned'] != 0]
    done = done.loc[done['Cottage (Fixed)'] == 0]
    for i in tqdm(done.index):
        assign(done.loc[i,'ID'],done.loc[i,'Assigned'])
        
    print(len(dfres.loc[dfres["Assigned"]==0]), 'Personen nog niet ingedeeld')
    
def writer():
    name = input("Naam:")
    name = name + ".xlsx"
    
    writer = pd.ExcelWriter(name)
    dfres.to_excel(writer,'Reservations')
    dfbez.to_excel(writer,'Bezetting')
    dfcot.to_excel(writer,'Cottages')
    writer.save()