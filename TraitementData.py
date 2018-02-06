# -*- coding: utf-8 -*-
"""
Created on Fri Dec  8 16:39:59 2017

@author: perez
"""

"""
===========================================================================================================
                                        LECTURE DES FICHIERS
===========================================================================================================
"""
import numpy as np

def cint(txt):      # Convertit une donnée texte d'un fichier INSEE en un entier
    if (txt == 'Z') or (txt == 'ZZ') or (txt == 'ZZZ') or (txt == 'ZZZZ'):  # A étudier (fichier MobPro)
        return(0)
    else:
        return(round(float(txt)))

def readfile(nomFichier):
    with open(nomFichier, 'r') as f:
        data = f.readlines() 
    return(data)

def add_ligne(txtLigne, indicesExtract, nbIdComm, J, iDep, res):
    converted_ligne = [0]*(J+nbIdComm) #On créer une liste contenant (le nombre de colonnes à extraire+nbIdComm) 0
    ligne = txtLigne.split(";") #On créer une liste contenant les éléments de la lignes séparés par un ; en string
    onlyDep = 0 # Indicateur permettant de savoir si la ligne correspond au département ou non
    
    i_r = 0     # indice lecture    (dans indicesExtract)
    i_w = 0     # indice écriture   (dans converted_ligne)
    while i_r < nbIdComm:
        idCommune = ligne[indicesExtract[i_r]] #On extrait l'identifiant de la commune
        converted_ligne[i_w:i_w+2] = idCommune[:2], idCommune[2:] #On remplit les 2 premières colonnes avec l'identifiant séparé en 2
        if (iDep == None) or (converted_ligne[i_w] == iDep): #Si on a pas choisir de département ou la ligne correspond au département
            onlyDep += 1
        i_r += 1
        i_w += 2 #On incrémente l'indice d'écriture pour ne pas écrasé ce qui a déjà été écrit
            
    if not(onlyDep): #Ne se fait que si onlyDep=0 ==> la ligne ne correspond pas au département
        return(res) #On retourne res sans l'avoir modifié
      
    for i in indicesExtract[i_r:]:
        converted_ligne[i_w] = cint(ligne[i])
        i_w += 1
        
    res.append(converted_ligne)
    return()
     
def extractUsefulData(txtDataBrut, iData, iDep = None):
    """ 
    Paramètre iData = type de fichier lu
        si iData = 1 : mobilités pro
        si iData = 2 : flux mobilité pro
        ...
    --------------------------------------------
    Paramètre iDep = extraction des données du département n° iDep
    """
    if iData == 1:
        indicesExtract = [0,5,9] #0 : Département et commune du lieu de résidence; 5 : CSP; 9 : Indicateur du lieu de travail
        nbIdComm = 1 #Utilité ?
    elif iData == 2:
        indicesExtract = [0,2,4]
        nbIdComm = 2 #Utilité ?
    J = len(indicesExtract) #Nombre de colonnes à extraire
    N = len(txtDataBrut) #Nombre de lignes du document
    res = []
    for i in range(1,N):
        add_ligne(txtDataBrut[i], indicesExtract, nbIdComm, J, iDep, res) #Traitement pour chaque ligne
    return(res)

def loadData(txtNomFichier, iData, iDep = None):
    txtDataBrut = readfile(txtNomFichier)
    return(extractUsefulData(txtDataBrut, iData, iDep))

"""
===========================================================================================================
                                        TRAITEMENT DES FICHIERS
===========================================================================================================
"""
def normalisationModalites(mData):
    nbModalites = [5, 2]   # nombre de modalités de chaque variable
    for ligne in mData:
        # CSP = 0 Autre; 1 Cadre; 2 Pro. intermédiaire; 3 Employé; 4 Ouvrier
        if ligne[2] not in [3,4,5,6]:   
            ligne[2] = 2
        ligne[2] -= 2   
        
        # Lieu de travail = 0 Hors commune résidence; 1 commune résidence
        if ligne[3] != 1:
            ligne[3] = 0
    return(nbModalites)

def regroupeParCommune(mData, vNbModalites):
    N = len(mData)
    J = len(vNbModalites)
    i = 0
    res = []
    while i < N:
        newCommune = [[0 for kj in range(j)] for j in vNbModalites]
        newCommune.insert(0, mData[i][1])
        nHabitantCommune = 0               
        while i < N and mData[i][1] == newCommune[0]:
            for j in range(1,J+1):
                newCommune[j][mData[i][j+1]] += 1            
            i += 1
            nHabitantCommune += 1
        for j in range(1,J+1):
            for kj in range(vNbModalites[j-1]):
                newCommune[j][kj] /= nHabitantCommune
        res.append(newCommune)
    return(res)
    
def concatenationDonnees(mData1, mData2):
    N1, N2 = len(mData1), len(mData2)
    notFound, idNF = [], []
    for i1 in range(N1):
        i2 = 0
        while i2 < N2 and int(mData1[i1][0]) != int(mData2[i2][0]):
            i2 += 1
        if i2 == N2:
            notFound.append(mData1[i1][0])
            idNF.append(i1)
        else:
            mData1[i1].insert(1, mData2[i2][1])
    if len(idNF) != 0:
        for i in range(len(idNF)):
            del(mData1[idNF[i]-i])
    del(mData2)
    return(notFound)
    
def concatenationDonneesWNumpy(mData, mDataN):
    N1, N2 = len(mData), mDataN.shape[0]
    notFound, idNF = [], []
    for i1 in range(N1):
        i2 = 0
        while i2 < N2 and int(mData[i1][0]) != int(mDataN[i2,0]):
            i2 += 1
        if i2 == N2:
            notFound.append(mData[i1][0])
            idNF.append(i1)
        else:
            mData[i1].insert(1, list(mDataN[i2,1:]))
    if len(idNF) != 0:
        for i in range(len(idNF)):
            del(mData[idNF[i]-i])
    return(notFound)

def delNotFoundCommNumpy(mData,mDataN):         # Suppression des communes de la matrice numpy mDataN non trouvées dans mData
    N1, N2 = len(mData), mDataN.shape[0]
    notFound = []
    for i2 in range(N2):
        i1 = 0
        while i1 < N1 and int(mData[i1][0]) != int(mDataN[i2,0]):
            i1 += 1
        if i1 == N1:
            notFound.append(mDataN[i2,0])
    p = N2-len(notFound); q = mDataN.shape[1]
    if p < N2:
        newDataN = np.zeros((p,q))
        j = 0
        for i in range(N2):
            if not(mDataN[i,0] in notFound):
                newDataN[j,:] = mDataN[i,:]
                j += 1
    return(newDataN)              
                            
def splitSet(y):
    N = y.shape[0]  
    sets = np.random.binomial(1,0.8,N)
    uniq, count = np.unique(sets, return_counts=True)
    trainingSet = np.zeros(count[1], dtype = 'int')
    validationSet = np.zeros(count[0], dtype = 'int')
    p, q = 0, 0
    for i in range(N):
        if sets[i]:
            trainingSet[p] = i
            p += 1
        else:
            validationSet[q] = i
            q += 1
    return(trainingSet, validationSet)
            
def checkComm(mDataComm):
    res = []
    for i in range(len(mDataComm)):
        res.append(mDataComm[i][0])
    return(res)
    
    
    
    
