# -*- coding: utf-8 -*-
"""
Created on Fri Jun  8 22:08:54 2018

@author: Frank
"""
import warnings
warnings.simplefilter(action = 'ignore',category=FutureWarning)
import pandas as pd
import numpy as np
import datetime
import multiprocessing

#Moeten mogelijk geimporteerd worden
import regex as re #Wordt gebruikt voor partroonherkenning
from tqdm import tqdm #Geeft een progressbar

def initialize():
    print("Initialize")
    global dfcot
    global dfres   
    global dfbez
    file = "startoplossing.xlsx"
    
    xl = pd.ExcelFile(file)

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
    dfcot=dfcot.assign(Score=np.zeros(len(dfcot),dtype=int))
    
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
            
def assign(res_id, cot_id):#Ken een reservering toe aan een huis
    datum = dfres.get_value(index = res_id-1,col = 'Arrival Date')
    col = dfbez.columns.get_loc(datum)
    duration = dfres.get_value(index = res_id-1,col ='Length of Stay')
    dfbez.loc[cot_id -1][col:col+duration] += res_id
    dfres.loc[res_id - 1,'Assigned']=cot_id

def fixed_assign():        
    fixed = dfres.loc[dfres['Cottage (Fixed)'] != 0] #maak subselectie van reserveringen met fixed huisje
    print("Assigning first selection")
    for i in range(len(fixed)):   
        res_id = fixed.iloc[i]['ID'] 
        cot_id = fixed.iloc[i]['Cottage (Fixed)']
        assign(res_id,cot_id)



def class_assign(todo,dfcot_class,dfbez):#kent reserveringen toe binnen een klasse
    todo = todo.loc[todo['Assigned'] == 0]
    todo = todo.sort_values(by=['Length of Stay'],ascending =False)   
    todo = todo.sort_values(by=['# Persons'],ascending =False)
    
    todo = todo.sort_values(by=['NrUpgrade'],ascending = False)
                      
    dfcot_class = dfcot_class.sort_values(by=['NrUpgrade'],ascending=True)
    dfcot_class=dfcot_class.sort_values(by=['Max # Pers'],ascending= True)
    for j in (todo.index):
        k=0
        match = False
        res_id = todo.loc[j,"ID"] 
        while k < len(dfcot_class) and match == False:
            if is_val(res_id, dfcot_class.iloc[k]["ID"]):
                assign(res_id,dfcot_class.iloc[k]["ID"])
                match = True
            else:
                k+=1
    klasse = dfcot_class.iloc[1]['Class']           
    result = dfres.loc[dfres['Class']==klasse]
    return(result)          
    
def final_assign():#Kent alle reserveringen toe met vaste nummers
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

def score(cot_id):#Berekent score van een huix\s
    gaps = 0
    legionella = 0
    weekendgaps = 0
    upgrades = 0
    possible_cap = np.array([2, 4, 5, 6, 8, 12])#mogelijke huizen, uit de handleiding
    
    temp= dfbez.loc[cot_id-1]
    line = '0'
    for j in temp.index:
        if temp.loc[j] != 0:
            line=line+ str(0)
        else:
            line = line + str(datetime.date.isoweekday(j)) #1 = maandag ,2 = dinsdag , ... , 7 = zondag
    line = line + '0'
    leg = re.compile('0[1,2,3,4,5,6,7]+0')
    weekend = re.compile('5671234')
    weekendgaps+=len(weekend.findall(line))
    g= leg.findall(line,overlapped = True)
    gaps+=len(g)
    for j in g:
        if len(j) > 23:
            legionella+=1
    temp_res = dfres[dfres['ID'].isin(pd.unique(temp))]
    
    temp_res=temp_res[temp_res['Cottage (Fixed)']==0]
    for k in temp_res.index:
        assigned = temp_res.get_value(index = k,col = 'Assigned')- 1 
        if dfcot.get_value(index = assigned,col = "Class") > temp_res.get_value(index=k,col = 'Class'): 
            upgrades += 1
        else:
            eff_nr_pers = min(possible_cap[possible_cap >= temp_res.get_value(index= k,col = "# Persons")])
            if eff_nr_pers < dfcot.get_value(index = assigned,col = "Max # Pers"): 
                upgrades += 1
    return(6*gaps - 3*weekendgaps + 12*legionella + upgrades)
    
def swap(res_id1,cot_id1,res_id2,cot_id2):#Wisseld een reservering om naar een ander huis
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

def writer(name):
#    name = input("Naam:")
    name = name + ".xlsx"
    
    writer = pd.ExcelWriter(name)
    dfres.to_excel(writer,'Reservations')
    dfbez.to_excel(writer,'Bezetting')
    dfcot.to_excel(writer,'Cottages')
    writer.save()
    
if not 'dfcot' in globals():#Waar als deze nog niet bestaat
    initialize()
    fixed_assign()
    

if __name__ == '__main__':#Om recursie in het multiprocessing te voorkomen
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
    
    final_assign()
    writer('Startoplossing')
    
for cot_id in dfcot.index:
    dfcot.set_value(cot_id,'Score',score(cot_id+1))
startscore=0
for i in dfcot.index:
    startscore+=score(i+1)
print('Begin score'+str(startscore))
s=0
while startscore != s:#deze zijn gelijk als er geen verandering plaats meer vindt
    startscore = s
    temp=dfres[dfres['Cottage (Fixed)']==0]
    notzero = pd.unique(dfcot[dfcot['Score']!=0].loc[:]['ID'])
    dfcot.sort_values(by='Score',ascending=False)
#    temp=temp[temp['ID'].isin(notzero)]
#    dfcot.sort_values(by='Score',ascending=False)
    for start_res in tqdm(temp.index):
        start_res+=1
        cot_id1=dfres.get_value(index=start_res-1,col='Assigned')
        current=dfbez.loc[cot_id1-1]
        t=current[current==start_res].index
        duration = dfres.get_value(index=start_res-1,col='Length of Stay')
        startdate=t[0]
        col=dfbez.columns.get_loc(startdate)
    #    enddate=t[-1]
    #    print(startdate,enddate)
        improved=False
        mat=dfbez.as_matrix()
        s_start_res=dfcot.get_value(index=cot_id1 - 1,col='Score')
        for cot_id2 in dfcot.index:
            if not improved:#mogelijk verbeteren
                cot_id2+=1#Vervang misschien door lookup zodra er gesorteerd wordt
                if max((mat[cot_id2-1][col:col+duration]))==0:
                    s1=s_start_res+dfcot.get_value(index=cot_id2 - 1,col='Score')
                    if is_val_swap(start_res,cot_id2):
                        swap(start_res,cot_id1,0,cot_id2)
                        s2=score(cot_id1)+score(cot_id2)
                        if s2>=s1:
                            swap(start_res,cot_id2,0,cot_id1)
#                            print('verlies',s2-s1)
    #                        print('swapping back', start_res,cot_id2)
                        else:
                            improved = True
                            dfres.set_value(start_res-1,'Assigned',cot_id2)
                            dfcot.set_value(cot_id1-1,'Score',score(cot_id1))
                            dfcot.set_value(cot_id2-1,'Score',score(cot_id2))



                                
#                            print('winst',s1,s2, start_res,cot_id2)
    #                        print('Assuming', start_res,cot_id2)

    s=0
    for i in dfcot.index:
        s+=score(i+1)
    print(s)
    writer('Score' + str(s))
