
#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Modules externes
from datetime import datetime, date
import csv
import logging
import re

#Parametres
ACADEMIC_DEPT_TO_DEPT = {
            'UB_FMT_101' : 'BUSH_LEGANTO_DEPT',
            'UB_FMT_131' : 'BUSH_LEGANTO_DEPT',
            }

DOMAIN_LIST = [
    'u-bordeaux.fr',
    'u-bordeaux-montaigne.fr',
    'sciencespobordeaux.fr',
    '@enitab.fr',
    '@ipb.fr']

CONF_INSTITUTIONS = {
    'UB' : {
        'type_identifiant' : 'eppn',
        'domain' : 'u-bordeaux.fr'
    },
    'UBM' : {
        'type_identifiant' : 'uid',
        'domain' : 'u-bordeaux-montaigne.fr'
    },
    'IEP' : {
        'type_identifiant' : 'eppn',
        'domain' : 'sciencespobordeaux.fr'
    },
    'BXSA' : {
        'type_identifiant' : 'uid',
        'domain' : 'antitab.fr'
    }, 
    'INP' : {
        'type_identifiant' : 'eppn',
        'domain' : 'ipb.fr'
    }
}

#init logger
logger = logging.getLogger("__main__.{}".format(__name__))

def formate_date(date) :
    """Formate la date au format attendu par le chargeur jj-mm-AAAA

    Args:
        date (string): timestamp

    Returns:
        string : date formatée
    """
    if date is None :
        return ""
    elif date == 0 :
        return ""
    else :
        return datetime.fromtimestamp(int(date)).strftime("%d-%m-%Y")

def date_de_fin_de_cour() :
    month = datetime.now().month
    year = datetime.now().year
    # entre janvier et août l'année de fin est égale à l'année en cour
    if month >= 1 and month < 8:
        return date(int(year),8,1).strftime("%d-%m-%Y")
    # Entre août et décembre l'année de fin est égale à l'anée suivante
    else :
        return date(int(year)+1, 8, 1).strftime("%d-%m-%Y")

def traitement_des_enseignants(enseignants,institution):
    enseignants_list = enseignants.split(',')
    if CONF_INSTITUTIONS[institution]['type_identifiant'] == 'eppn' :
        #Si on nous envoie des eppns, on exclu tous les individus non membres de la communauté universitaire
        for enseignant in enseignants_list :
            domain = re.findall('^(.*?)@(.*?)$', enseignant)
            if domain[0][1] not in DOMAIN_LIST :
                enseignants_list.remove(enseignant)
    else :
        # Si ce sont des uid on les suffixe par le non de domaine de l'institution
        for i in range(len(enseignant)):
            enseignants_list[i] = "{}@{}".format(enseignant,CONF_INSTITUTIONS[institution]['domain'])
    return ",".join(enseignants_list)    



def process_file(file_name,out_file,institution,plateforme,regles_filtrage) :
    logger.debug(__name__)
    default_end_course_date = date_de_fin_de_cour()
    # Ouverture du fichier de chargement pour écriture
    chargeur = open(out_file, "w",  encoding='utf-8')
    chargeur.write("COURSE_CODE\tCOURSE_TITLE\tSECTION_ID\tACAD_DEPT\tPROC_DEPT\tTERM1\tTERM2\tTERM3\tTERM4\tSTART_DATE\tEND_DATE\tNUM_OF_PARTICIPANTS\tWEEKLY_HOURS\tYEAR\tSEARCH_ID1\tSEARCH_ID2\tMULTI_SEARCH_ID\tINSTR1\tINSTR2\tINSTR3\tINSTR4\tINSTR5\tINSTR6\tINSTR7\tINSTR8\tINSTR9\tINSTR10\tALL_INSTRUCTORS\tOPERATION\tOLD_COURSE_CODE\tOLD_COURSE_SECTION\tSUBMIT_LISTS_BY\tCAMPUS_AND_PARTICIPANTS\tREADING_LIST_NAME""\n")

    ###Traitement du fichier en provenace de Moodle 
    # ##############################################
    try : 
        with open(file_name, 'r', encoding='utf-8', newline='') as f:
            reader = csv.reader(f, delimiter='\t')
            headers = next(reader)
            # We read the file
            for row in reader:
                if len(row) < 2:
                    continue
                if "{}_{}_{}".format(institution,plateforme,row[8]) in regles_filtrage['Niv_1'] and "{}_{}_{}".format(institution,plateforme,row[9]) not in regles_filtrage['Niv_2']:
                    COURSE_CODE  = "{}_{}".format(row[0],row[1])
                    COURSE_TITLE  = row[2]
                    SECTION_ID  = ""
                    ACAD_DEPT  = "{}_{}".format(plateforme,row[7])
                    PROC_DEPT  = ACADEMIC_DEPT_TO_DEPT["{}_{}_{}".format(institution,plateforme,row[8])]
                    TERM1  = ""
                    TERM2 = ""
                    TERM3 = ""
                    TERM4 = ""
                    START_DATE  = formate_date(row[4])
                    # On renseigne par défaaut les dates de fin de cour vides avec la date de l'année en cour
                    END_DATE  = default_end_course_date if row[5] is not None else formate_date(row[5]) 
                    NUM_OF_PARTICIPANTS  = row[11]
                    WEEKLY_HOURS  = ""
                    YEAR  = ""
                    SEARCH_ID1  = row[3]
                    SEARCH_ID2 = ""
                    MULTI_SEARCH_ID  = ""
                    INSTR1  = ""
                    INSTR2 = ""
                    INSTR3 = ""
                    INSTR4 = ""
                    INSTR5 = ""
                    INSTR6 = ""
                    INSTR7 = ""
                    INSTR8 = ""
                    INSTR9 = ""
                    INSTR10 = ""
                    ALL_INSTRUCTORS  = traitement_des_enseignants(row[10],institution=institution)
                    OPERATION  = ""
                    OLD_COURSE_CODE  = ""
                    OLD_COURSE_SECTION  = ""
                    SUBMIT_LISTS_BY  = ""
                    CAMPUS_AND_PARTICIPANTS  = ""
                    READING_LIST_NAME  = ""
                    chargeur.write("{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\n".format(
                        COURSE_CODE, COURSE_TITLE, SECTION_ID, ACAD_DEPT, PROC_DEPT, TERM1, TERM2, TERM3, TERM4,START_DATE, END_DATE, NUM_OF_PARTICIPANTS, WEEKLY_HOURS,
                        YEAR, SEARCH_ID1, SEARCH_ID2,MULTI_SEARCH_ID, INSTR1, INSTR2,INSTR3,INSTR4,INSTR5,INSTR6,INSTR7,INSTR8,INSTR9,INSTR10,ALL_INSTRUCTORS,
                        OPERATION, OLD_COURSE_CODE, OLD_COURSE_SECTION, SUBMIT_LISTS_BY, CAMPUS_AND_PARTICIPANTS, READING_LIST_NAME))
                else :
                    continue
        logger.info("{}::Fichier traité avec succès".format(file_name))
        return "Success"
    except Exception as e:
        logger.error("{}::Impossible de traiter le fichier::{}".format(file_name,str(e)))
        return "Error"
