#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Modules externes
import os
import logging
import csv
import json
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry 
from requests import request
import xml.etree.ElementTree as ET


#Init logger
logger = logging.getLogger("__main__.{}".format(__name__))

def get_api_key(instance,institution) :
    """Retourne la clef d'api en fonction de l'institution traitée et de l'instance (production ou test de travail)

    Args:
        instance (string): TEST ou PROD 
        institution (string): Code de l'institution UB,UBM, IEP, INP, BXSA

    Returns:
        string: clef d'API
    """
    if instance == 'TEST' :
        api_key = os.getenv("TEST_{}_API".format(institution))
    else :
        api_key = os.getenv("PROD_{}_BIB_API".format(institution))
    return api_key

def get_request_body(institution) :
    """Retourne l'entête du corps des données json a passer à l'API

    Args:
        institution (string): Code institution UB,UBM, IEP, INP, BXSA

    Returns:
        json : données json à passer à l'API
    """
    institution_list = {
        "33PUDB_UB" : "Université de Bordeaux (UB)",
        "33PUDB_UBM" : "Université Bordeaux Montaigne (UBM)",
        "33PUDB_BXSA" : "Bordeaux Sciences Agro (BxSA)",
        "33PUDB_INP" : "Bordeaux INP (INP)",
        "33PUDB_IEP" : "Sciences Po Bordeaux (IEP)"
    }
    request_body = {
    "name": "CourseFaculties",
    "description": "Course Faculties",
    "sub_system": {
        "value": "FULFILLMENT",
        "desc": "Fulfillment"
    },
    "patron_facing": True,
    "language": {
        "value": "en",
        "desc": "English"
    },
    "scope": {
        "institution_id": {
        "value": "33PUDB_{}".format(institution),
        "desc": institution_list["33PUDB_{}".format(institution)]
        },
        "library_id": {
        "value": "",
        "desc": ""
        }
    },
    "row": []
    }
    return request_body


def get_error_message(response):
    """Extract error code & error message of an API response
    
    Arguments:
        response {object} -- API REsponse
    
    Returns:
        int -- error code
        str -- error message
    """
    error_code, error_message = '',''
    try :
        content = response.json()
    except : 
        # Parfois l'Api répond avec du xml même si l'en tête demande du Json cas des erreurs de clefs d'API 
        root = ET.fromstring(response.text)
        error_message = root.find(".//xmlb:errorMessage").text if root.find(".//xmlb:errorMessage").text else response.text 
        error_code = root.find(".//xmlb:errorCode").text if root.find(".//xmlb:errorCode").text else '???'
        return error_code, error_message 
    error_message = content['errorList']['error'][0]['errorMessage']
    error_code = content['errorList']['error'][0]['errorCode']
    return error_code, error_message
    
def request(httpmethod,api_key, data=None):
    """Envoi un appel à l'api Alma pour injecter les codes des départements et leur libellés

    Args:
        httpmethod (string): Méthode d'appel PUT, GET, POST.
        api_key (string): clef d'API 
        data (json, optional): . Defaults to None.
    Returns:
        array: status du traitement Success ou Error et Reponse de l'API
    """
    #20190905 retry request 3 time s in case of requests.exceptions.ConnectionError
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    response = session.request(
        method=httpmethod,
        headers= {
        "User-Agent" : "pyalma/0.1.0",
        "Authorization" : "apikey {}".format(api_key),
        "Accept" : 'application/json',
        "Content-Type" :'application/json',
    },
        url= "https://api-eu.hosted.exlibrisgroup.com/almaws/v1/conf/code-tables/CourseFaculties",
        data=data)
    try:
        response.raise_for_status()  
    except requests.exceptions.HTTPError:
        print(response.text)
        error_code, error_message= get_error_message(response)
        logger.error("Alma_Apis :: HTTP Status: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
        if error_code == '402263' :
            return 'Error_SetExist', "{} -- {}".format(error_code, error_message)
        return 'Error', "{} -- {}".format(error_code, error_message)
    except requests.exceptions.ConnectionError:
        error_code, error_message= get_error_message(response)
        logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
        return 'Error', "{} -- {}".format(error_code, error_message)
    except requests.exceptions.RequestException:
        error_code, error_message= get_error_message(response)
        logger.error("Alma_Apis :: Connection Error: {} || Method: {} || URL: {} || Response: {}".format(response.status_code,response.request.method, response.url, response.text))
        return 'Error', "{} -- {}".format(error_code, error_message)
    return "Success", response

def import_academic_dept(file,institution,plateforme,regles_filtrage,instance) :
    """Transforme le fichier fourni en json et intégre les départements via l'API Alma

    Args:
        file (strin): adresse du fichier à traiter
        institution (string): code de l'institution pour laquelle injecter les départements
        plateforme (string): code de la palteforme pour laquelle injecter les départements
        regles_filtrage (array): liste servant au filtrage des départements
        instance (string): Instance sur laquelle déclencher le traitementPROD ou TEST

    return :
        string : statut du traitement Success ou Error
        string : réponse de l'API
    """
    # Obtention de la clef d'API
    api_key = get_api_key(instance,institution)
    
    # Construction de l'entête du fichier json
    request_body = get_request_body(institution)
    
    ###Traitement du fichier en provenace de Moodle 
    # ############################################## 
    with open(file, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f, delimiter='\t')
        headers = next(reader)
        # We read the file
        for row in reader:
            if len(row) < 2:
                # Ligne vide 
                continue
            # Exclusion des départements non intégrés au circuit Leganto
            if "{}_{}_{}".format(institution,plateforme,row[4]) in regles_filtrage['Niv_1'] and "{}_{}_{}".format(institution,plateforme,row[4]) not in regles_filtrage['Niv_2']:
                code_tab_line = {
                    "code" : "{}_{}".format(plateforme,row[0]),
                    "description" : row[2],
                    "default": False,
                    "enabled": True
                }
                request_body["row"].append(code_tab_line)
        # logger.debug(json.dumps(request_body))
        return request('PUT',api_key=api_key,data=json.dumps(request_body))