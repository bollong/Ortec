#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon May 21 15:10:53 2018

@author: frank
"""

import pandas as pd
import numpy as np
import datetime
from tqdm import tqdm
import regex as re

#import multiprocessing

def assign(res_id, cot_id):
    datum = dfres.get_value(index = res_id-1,col = 'Arrival Date')
    col = dfbez.columns.get_loc(datum)
    duration = dfres.get_value(index = res_id-1,col ='Length of Stay')
    dfbez.loc[cot_id -1][col:col+duration] += res_id
    dfres.loc[res_id - 1,'Assigned']=cot_id

def swap(res_id1,cot_id1,res_id2,cot_id2):
    datum = dfres.get_value(index = res_id1-1,col = 'Arrival Date')
    col = dfbez.columns.get_loc(datum)
    duration = dfres.get_value(index = res_id1-1,col ='Length of Stay')
    dfbez.loc[cot_id1-1][col:col+duration] = res_id2
    dfbez.loc[cot_id2-1][col:col+duration] = res_id1
    
def is_val_swap(res_id, cot_id):#kijkt of een combinatie reservering/huis geldig is
    options = ['Face South', 'Near Playground', 'Close to the Centre', 'Near Lake ',
       'Near car park', 'Accessible for Wheelchair', 'Child Friendly',
       'Dish Washer ', 'Wi-Fi Coverage ', 'Covered Terrace']
    if dfres.get_value(index=res_id-1,col='# Persons') > dfcot.get_value(index=cot_id-1,col='Max # Pers'):
        return(False) #Huis is te klein
    for opt in options:
        if (dfres.get_value(index=res_id - 1,col =opt) == 1) and (dfcot.get_value(index=cot_id - 1,col =opt) == 0):
            return (False) #Voor alle extra opties, kijk of deze gevraagd en aanwezig zijn
    if dfres.get_value(index=res_id - 1,col='Class') > dfcot.get_value(index=cot_id - 1,col='Class'):
        return(False) # Minimaal de juiste klasse?
    return(True) #Voldoet aan alle eisen         
    
def initialize():
    print("Initialize")
    global dfcot
    global dfres   
    global dfbez
    global test
#    file = 'startoplossing.xlsx
    file = 'startoplossing.xlsx'
    
    xl = pd.ExcelFile(file) 
    
    dfcot = xl.parse('Cottages')
    dfres = xl.parse("Reservations")
    dfres=dfres.sort_values(by='ID')
    startdate = datetime.datetime(2017,7,3)
    index = []
    for i in range(0,42): #Maak lijst van alle beschikbare data als kolom-index
        index.append(startdate + datetime.timedelta(days = i))
    
    dfbez = pd.DataFrame(np.zeros((819,42), dtype=int),columns = index)
    
    for i in tqdm(dfres.index):
        assign(dfres.get_value(index = i,col ='ID'),dfres.get_value(index=i,col='Assigned'))
        
if not 'dfres' in globals():
    initialize()
    
def score(cot_id):        
    gaps = 0
    legionella = 0
    weekendgaps = 0
    upgrades = 0
    possible_cap = np.array([2, 4, 5, 6, 8, 12])#mogelijke huizen, uit de handleiding
    
    temp= dfbez.loc[cot_id]
    #temp= dfbez[208:209]
    line = '0'
    for j in temp.index:
        if temp.loc[j] != 0:
            line=line+ str(0)
            #line = line + str(test.loc[j])
        else:
            line = line + str(datetime.date.isoweekday(j)) #1 = maandag ,2 = dinsdag , ... , 7 = zondag
    line = line + '0'
    leg = re.compile('0[1,2,3,4,5,6,7]+0')#werkt niet
    weekend = re.compile('5671234')
    weekendgaps+=len(weekend.findall(line))
#    if len(weekend.findall(line)) != 0:
#        print(line)
    g= leg.findall(line,overlapped = True)
    gaps+=len(g)
    for j in g:
        if len(j) > 23:
            legionella+=1
    temp_res = dfres[dfres['ID'].isin(pd.unique(temp))]
    
    temp_res=temp_res[temp_res['Cottage (Fixed)']==0]
    #test=test[0:10]
    for k in temp_res.index:
    #        res_in_review = dfres.loc[i]
        assigned = temp_res.get_value(index = k,col = 'Assigned')- 1 #corrigeren voor 
    #        cot_in_review = dfcot.loc[assigned]
        if dfcot.get_value(index = assigned,col = "Class") > temp_res.get_value(index=k,col = 'Class'): 
            upgrades += 1
    #        print('Class',dfcot.get_value(index = assigned,col = "Class"),dfres.get_value(index = k,col = 'Class'),k)
        else:
            eff_nr_pers = min(possible_cap[possible_cap >= temp_res.get_value(index= k,col = "# Persons")])
            if eff_nr_pers < dfcot.get_value(index = assigned,col = "Max # Pers"): 
                upgrades += 1
    return(6*gaps - 3*weekendgaps + 12*legionella + upgrades)
#    print(upgrades,'upgrades')    
#    print(gaps ,'gaps')
#    print(weekendgaps,'weekendgaps')
#    print(legionella,'legionella')
#    print(6*gaps - 3*weekendgaps + 12*legionella + upgrades,'score',cot_id)


def writer():
    name = input("Naam:")
    name = name + ".xlsx"
    
    writer = pd.ExcelWriter(name)
    dfres.to_excel(writer,'Reservations')
    dfbez.to_excel(writer,'Bezetting')
    dfcot.to_excel(writer,'Cottages')
    writer.save()
    
#swap(1292,10,1155,6)

temp=dfres[dfres['Cottage (Fixed)']==0]
temp=temp[temp['Arrival Date'] == pd.unique(temp['Arrival Date'])[0]]
temp=temp[temp['Length of Stay']==4]
s = 0
for i in pd.unique(temp['Assigned']):
    s+=score(i)
print(s)    
for i in tqdm(temp.index):
    cot_id1=temp.get_value(index=i,col='Assigned')
    for j in temp.index:
        cot_id2=temp.get_value(index=j,col='Assigned')
        if i!=j:
            x=score(cot_id1)+score(cot_id2)
            if is_val_swap(i+1,cot_id2) and is_val_swap(j+1,cot_id1):
                swap(i+1,cot_id1,j+1,cot_id2)
                y=score(cot_id1)+score(cot_id2)
                if y<x:
                    swap(i+1,cot_id1,j+1,cot_id2)
#                else:
#                    print('verwissel',i+1,j+1)
                    
#cot = 1
#x=pd.unique(dfbez.loc[0])[0]
#duration = dfres.get_value(index=x-1,col='Length of Stay')
#col = dfbez.columns.get_loc(dfres.get_value(index=x-1,col='Arrival Date'))
#dfbez.loc[cot-1][col:col+duration]=0