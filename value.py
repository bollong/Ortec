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
#import regex as re

#import multiprocessing

def assign(res_id, cot_id):
    datum = dfres.get_value(index = res_id-1,col = 'Arrival Date')
    col = dfbez.columns.get_loc(datum)
    duration = dfres.get_value(index = res_id-1,col ='Length of Stay')
    dfbez.loc[cot_id -1][col:col+duration] += res_id
    dfres.loc[res_id - 1,'Assigned']=cot_id
    
def initialize():
    print("Initialize")
    global dfcot
    global dfres   
    global dfbez
    global test
#    file = 'startoplossing.xlsx
    file = 'startoplossingbb.xlsx'
    
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
    
    
gaps = 0
legionella = 0
weekendgaps = 0
upgrades = 0
possible_cap = np.array([2, 4, 5, 6, 8, 12])#mogelijke huizen, uit de handleiding

temp= dfbez
#temp= dfbez[208:209]
for i in (temp.index):
    test=dfbez.loc[i]
    line = '0'
    for j in test.index:
        if test.loc[j] != 0:
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

test=dfres[dfres['Cottage (Fixed)']==0]
#test=test[0:10]
for k in test.index:
#        res_in_review = dfres.loc[i]
    assigned = dfres.get_value(index = k,col = 'Assigned')- 1 #corrigeren voor 
#        cot_in_review = dfcot.loc[assigned]
    if dfcot.get_value(index = assigned,col = "Class") > dfres.get_value(index = k,col = 'Class'): 
        upgrades += 1
#        print('Class',dfcot.get_value(index = assigned,col = "Class"),dfres.get_value(index = k,col = 'Class'),k)
    else:
        eff_nr_pers = min(possible_cap[possible_cap >= dfres.get_value(index= k,col = "# Persons")])
        if eff_nr_pers < dfcot.get_value(index = assigned,col = "Max # Pers"): 
            upgrades += 1
#            print('Cap',dfres.get_value(index= k,col = "# Persons") , dfcot.get_value(index = assigned,col = "Max # Pers"),k)
#        res_in_review = dfres.loc[i]
#        assigned = res_in_review.loc['Assigned']- 1#corrigeren voor 
#        cot_in_review = dfcot.loc[assigned]
#        if cot_in_review.loc["Class"]>res_in_review.loc['Class']: upgrades += 1
#        eff_nr_pers = min(possible_cap[possible_cap > res_in_review.loc["# Persons"]])
#        if eff_nr_pers > cot_in_review.loc["Max # Pers"]: upgrades += 1

print(upgrades,'upgrades')    
print(gaps ,'gaps')
print(weekendgaps,'weekendgaps')
print(legionella,'legionella')
print(6*gaps - 3*weekendgaps + 12*legionella + upgrades,'score')

def writer():
    name = input("Naam:")
    name = name + ".xlsx"
    
    writer = pd.ExcelWriter(name)
    dfres.to_excel(writer,'Reservations')
    dfbez.to_excel(writer,'Bezetting')
    dfcot.to_excel(writer,'Cottages')
    writer.save()
        