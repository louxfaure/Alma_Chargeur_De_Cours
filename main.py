#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Modules externes
import os
import re
import logging
import modules.logs as logs
from modules import traitement_dept_univ, traitement_cours,transferts_ftp,mail

APP_NAME = "Alma-chargeur-cours"
LOGS_LEVEL = 'INFO'
LOGS_DIR = os.getenv('LOGS_PATH')
INSTANCE = 'PROD'
LOGS_FILE = "{}/{}".format(os.getenv('LOGS_PATH'),APP_NAME)
REMOTE_FILE_PATH_IN = '/DEPOT/LEGANTO/CHARGEMENT'
REMOTE_FILE_PATH_OUT = '/DEPOT/LEGANTO/CHARGEUR'
REMOTE_FILE_PATH_ARCHIVE = '/DEPOT/LEGANTO/ARCHIVES'
LOCAL_FILE_PATH_IN = '/tmp/leganto'
LOCAL_FILE_PATH_OUT = '/tmp/cours_out'
NB_ERROR = 0


REGLES_FILTRAGE_SUR_DEPT = {
    'Niv_1' : ['UB_FMT_101','UB_FMT_131'],
    'Niv_2' : ['UB_FMT_2']
    }

#On initialise le logger
logs.setup_logging(name=APP_NAME, level=LOGS_LEVEL,log_dir=LOGS_FILE)
logger = logging.getLogger(__name__)
logger.info(os.getenv("SFTP_UB_HOSTNAME"))

def envoie_rapport_traitement():
    logger.debug(NB_ERROR)
    msg = mail.Mail()
    with open('/tmp/{}.txt'.format(APP_NAME)) as f:
        text = f.read()
    if NB_ERROR > 0 :
        msg.envoie(os.getenv('ADMIN_MAIL'),os.getenv('ADMIN_MAIL'),"[{}] : warning".format(APP_NAME),text)
    else :
        msg.envoie(os.getenv('ADMIN_MAIL'),os.getenv('ADMIN_MAIL'),"[{}] : Service lancé avec succés".format(APP_NAME),text)

#Création du répertoire de stockage temporaire
if not os.path.exists(LOCAL_FILE_PATH_IN):
    os.mkdir(LOCAL_FILE_PATH_IN)
if not os.path.exists(LOCAL_FILE_PATH_OUT):
    os.mkdir(LOCAL_FILE_PATH_OUT)
# Récupération des fichiers
statut,file_list = transferts_ftp.load_file(REMOTE_FILE_PATH_IN,LOCAL_FILE_PATH_IN)
if statut == 'Error' :
    NB_ERROR =+ 1
    envoie_rapport_traitement()
    exit()
# file_list = ['UB_FMT_Cours_2022-06-17.csv','UB_FMT_Categories_2022-06-17.csv']
if len(file_list) == 0 :
    logger.error("Pas de fichiers à traiter")
    NB_ERROR =+ 1
    envoie_rapport_traitement()
    exit()
 
for file in file_list :
    # Récupération  des paramètres des sous traitements à partir du nom des fichiers
    file_name = re.findall('^(.*?)_(.*?)_(.*?)_(.*?)\..*', file)
    institution= file_name[0][0]
    plateforme = file_name[0][1]
    type_donnees = file_name[0][2]
    date_file = file_name[0][3]

    
    if type_donnees == 'Categories' :
        # Import des départements
        statut, reponse = traitement_dept_univ.import_academic_dept(file="{}/{}".format(LOCAL_FILE_PATH_IN,file),
                                                                    institution=institution,
                                                                    plateforme=plateforme,
                                                                    regles_filtrage=REGLES_FILTRAGE_SUR_DEPT,
                                                                    instance=INSTANCE)
        if statut == 'Error' :
            logger.error("{}::Erreur sur l'injection des département::{}".format(file,reponse))
            NB_ERROR =+ 1
        else :
            logger.info("{}::Injection des département réussie".format(file))
    else :
        #Préparation du fichier d'import des cours

        # Création du répertoire de transfert
        rep_path_out = "{}/{}".format(LOCAL_FILE_PATH_OUT,institution)
        if not os.path.exists(rep_path_out):
            os.mkdir(rep_path_out)
        file_path_out = "{}/{}_{}_{}_Pour_Chgt_{}.csv".format(rep_path_out,institution,plateforme,type_donnees,date_file)
        statut = traitement_cours.process_file('{}/{}'.format(LOCAL_FILE_PATH_IN,file),
                                    file_path_out,
                                    institution=institution,
                                    plateforme=plateforme,
                                    regles_filtrage=REGLES_FILTRAGE_SUR_DEPT)
        if statut == 'Error' :
            NB_ERROR =+ 1
# On récupère la liste des institutions pour lesquels on a un fichier à déposer. On a créé un répertoire par institution
institution_list = [f.name for f in os.scandir(LOCAL_FILE_PATH_OUT) if f.is_dir()]
statut = transferts_ftp.put_file(institution_list, LOCAL_FILE_PATH_OUT,REMOTE_FILE_PATH_OUT,LOCAL_FILE_PATH_IN,REMOTE_FILE_PATH_ARCHIVE,REMOTE_FILE_PATH_IN)
if statut == 'Error' :
    logger.error("{}::Erreur sur l'injection des département::{}".format(file,reponse))
    NB_ERROR =+ 1
# Envoi du rapport d'erreur à l'administrateur
envoie_rapport_traitement()
