# -*- coding: utf-8 -*-
"""
Created on Wed Apr 25 11:53:36 2018

@author: Frank
"""

#import os
import pandas as pd
import numpy as np
import datetime

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
    for i in range(0,50): #Maak lijst van alle beschikbare data als kolom-index
        index.append(startdate + datetime.timedelta(days = i))
    
    dfbez = pd.DataFrame(np.zeros((820,50), dtype=int),columns = index)

if not 'dfcot' in globals():#Waar als deze nog niet bestaat
    initialize()

def is_val(res_id, cot_id):#kijkt of een combinatie reservering/huis geldig is
    options = ['Face South', 'Near Playground', 'Close to the Centre', 'Near Lake ',
       'Near car park', 'Accessible for Wheelchair', 'Child Friendly',
       'Dish Washer ', 'Wi-Fi Coverage ', 'Covered Terrace']
    if dfres.iloc[res_id-1]['# Persons'] < dfcot.iloc[cot_id-1]['Max # Pers']:
        return(False) #Huis is te klein <----fout??
    for opt in options:
        if (dfres.iloc[res_id - 1][opt] == 1) and (dfcot.iloc[cot_id - 1][opt] == 0):
            return (False) #Voor alle extra opties, kijk of deze gevraagd en aanwezig zijn
    if dfres.iloc[res_id-1]['Class'] <= dfcot.iloc[cot_id-1]['Class']:
        return(False) # Minimaal de juiste klasse?
    datum = dfres.iloc[res_id-1]['Arrival Date']#Vraag de aankomstdatum op van de reservering
    col = dfbez.columns.get_loc(datum)#Bijbehorende kolom opvragen
    for i in range(1,dfres.iloc[1,res_id-1]['Length of Stay']):#eerste dag mag bezet zijn als het de laatste is van de vorige
        if dfbez.iloc[cot_id - 1][col + i] == 1:#Controleer of het huis al bezet is op die dag
            return(False)
    return(True) #Voldoet aan alle eisen
            
def assign(res_id, cot_id):#WIP, werkt nog niet
#    if not is_val(res_id, cot_id):#sanity check, misschien weglaten in eindversie
#        print("ERROR: verboden toekenning")
#    else:
    datum = dfres.iloc[res_id-1]['Arrival Date']
    col = dfbez.columns.get_loc(datum)
    duration = dfres.iloc[res_id-1]['Length of Stay']
    dfbez.iloc[cot_id -1][col:col+duration] = 1
    dfres.loc[res_id - 1]['Assigned']=cot_id
        
fixed = dfres.loc[dfres['Cottage (Fixed)'] != 0] #maak subselectie van reserveringen met fixed huisje
print("Assigning first selection")
for i in range(len(fixed)):   
#    res_id = fixed.iloc[i]['ID'] 
#    cot_id = fixed.iloc[i]['Cottage (Fixed)']
#    assign(res_id,cot_id)
    datum = fixed.iloc[i]['Arrival Date'] #arrivaldate opvragen
    col = dfbez.columns.get_loc(datum) #bijbehorende kolom
    row = fixed.iloc[i]['Cottage (Fixed)']-1 #rij van de huis
    duration = fixed.iloc[i]['Length of Stay']
    dfbez.iloc[row][col:col+duration] = 1 #Invullen in het bezettings dataframe
    res_id = fixed.iloc[i]['ID'] #Toekennen van huis aan reserverings frame
    dfres.loc[res_id-1,'Assigned']=row+1 #row is opgehaald als het fixed cottage id -1
#
#def greedy():
#    for i in range(5):
#        print("Commence iteration ", i)
#        todo = dfres.loc[dfres['Assigned'] == 0]
#        for j in range(len(todo)):
#            if

#from pandas import ExcelWriter
#
#writer = ExcelWriter('Test1.xlsx')
#dfbez.to_excel(writer,'reserveringen')
#writer.save()


#def check():
#    for i in range(len(dfbez)): 
#        if dfres.iloc[res_id-1]['# Persons'] < dfbez.iloc[cot_id-1]['Max # Pers']:
#        return(True) 
         
#if dfres.loc[dfres['Assigned'] == 341]['# Persons'] <= dfcot.loc[dfcot['ID'] == 341]['Max # Pers']:
#    print('true')


def check():
    upgrade = 0
    options2 = ['Face South', 'Near Playground', 'Close to the Centre', 'Near Lake ',
       'Near car park', 'Accessible for Wheelchair', 'Child Friendly',
       'Dish Washer ', 'Wi-Fi Coverage ', 'Covered Terrace']
    for i in range(90,91):
        test1 = dfres.loc[dfres['Assigned'] == i]
        test2 = dfcot.loc[dfcot["ID"] == i]
        for y in range(0,len(test1)):
            if test1['# Persons'].iloc[y] > test2['Max # Pers'].iloc[0]:
#                return(False)
                print('res',test1['ID'].iloc[y], 'past niet in', test2['ID'].iloc[0], 'door personen')
#                upgrade = 1
                
            if test1['Class'].iloc[y] > test2['Class'].iloc[0]:
#                return(False)
                print('res',test1['ID'].iloc[y], 'past niet in', test2['ID'].iloc[0], 'door klasse')
            elif test1['Class'].iloc[y] < test2['Class'].iloc[0]:
                upgrade = 1
                
            for opt in options2:
                if (test1[opt].iloc[y] == 1) and (test2[opt].iloc[0] == 0):
                    print('res',test1['ID'].iloc[y], 'past niet in', test2['ID'].iloc[0], 'door opties')
#                elif (test1[opt].iloc[y] == 0) and (test2[opt].iloc[0] == 1):
#                    upgrade = 1
            
            datum = test1['Arrival Date']
            col = dfbez.columns.get_loc(datum)
            for j in range(1,test1['Length of Stay'].iloc[y]):
                if dfbez.loc[dfres['Assigned'] == i][col + j] == 1:
                    print('false voor id nummer', test1['ID'].iloc[y], 'voor huisje', test2['ID'].iloc[0])    
            
            
 
        

            

