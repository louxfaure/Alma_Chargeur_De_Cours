#!/usr/bin/python3
# -*- coding: utf-8 -*-
#Modules externes
import os
import logging
import pysftp

#Init logger
logger = logging.getLogger("__main__.{}".format(__name__))
cnopts = pysftp.CnOpts(knownhosts=os.getenv('KNOWN_HOSTS'))
# cnopts = pysftp.CnOpts()
# cnopts.hostkeys = None

# Récupération des fichiers
def load_file(remote_file_path_in,local_file_path_in):
    try :
        # Connexion au serveur
        with pysftp.Connection(host=os.getenv("SFTP_UB_HOSTNAME"), username=os.getenv("SFTP_UB_LOGIN"), password=os.getenv("SFTP_UB_PW"),cnopts=cnopts,log=True) as sftp:
            logger.info("Récupération des fichiers::Connexion au serveur ftp ok")
            file_list = sftp.listdir(remote_file_path_in)
            try : 
                # Transfert des fichiers
                sftp.get_d(remote_file_path_in, local_file_path_in, preserve_mtime=True)
            except Exception as e:
                logger.error("Récupération des fichiers::Impossible de transférer les fichiers ::{}".format(str(e)))
                sftp.close()
                return "Error", str(e)

            logger.info("Récupération des fichiers::Fichiers transférés avec succès::{}".format(file_list))
            sftp.close()
            return "Success",file_list
    except Exception as e:
        logger.error("Récupération des fichiers::Impossible de se connecter au serveur ftp::{}".format(str(e)))
        return "Error", str(e)

#Transfert des fichiers à charger, Archivage et suppression des fihiers source sur le ftp
def put_file(institutions_list,local_file_path_out, remote_file_path_out,local_file_path_in,remote_file_path_archive,remote_file_path_in):
    try :
        # Connexion au serveur
        with pysftp.Connection(host=os.getenv("SFTP_UB_HOSTNAME"), username=os.getenv("SFTP_UB_LOGIN"), password=os.getenv("SFTP_UB_PW"),cnopts=cnopts) as sftp:
            # Transfert des fichiers formatés vers le serveurs
            for inst in institutions_list :
                # Suppression des fichiers existants
                sftp.chdir("{}/{}".format(remote_file_path_out,inst))
                file_list = sftp.listdir()
                for file in file_list :
                    sftp.remove(file)
                #Dépôt des fichiers
                try :
                    sftp.put_r("{}/{}".format(local_file_path_out,inst),"{}/{}".format(remote_file_path_out,inst),confirm=False,preserve_mtime=True)    
                except Exception as e:
                    logger.error("Dépôt des fichiers traités::Impossible transférer les fichiers pour {}::{}".format(inst,str(e)))
                    sftp.close()
                    return "Error"
            # Archivages des fichiers sources
            try :
                sftp.put_r(local_file_path_in,remote_file_path_archive,confirm=False,preserve_mtime=True)
            except Exception as e:
                logger.error("Archivage des des fichiers :: Impossible de transférer les fichiers ::{}".format(str(e)))
                sftp.close()
                return "Error"
            # Suppression des fichiers
            sftp.chdir(remote_file_path_in)
            file_list = sftp.listdir()
            for file in file_list :
                sftp.remove(file)
            logger.info("Nettoyage du répertoire::Succés")
            return "Success"
    except Exception as e:
        logger.error("Dépôt des fichiers traités::Impossible de se connecter au serveur ftp::{}".format(str(e)))
        return "Error"