#!/usr/bin/env python

"""
Python script to upload project folders/files to MetaboLights Labs Projects

Dependencies:
    os, sys, argparse, json, requests, subprocess

Usage:
    python uploadToMetaboLightsLabs.py -t <MetaboLights Labs API_KEY> -i [ <filesToUpload> ] -p <MetaboLights Labs Project_ID> -n -s <ENV>
    or
    uploadToMetaboLightsLabs.py -t <MetaboLights Labs API_KEY> -i [ <filesToUpload> ] -p <MetaboLights Labs Project_ID> -n -s <ENV>

Arguments:
    -t MetaboLights Labs API_KEY
    -i pathToFile1, pathToFile2, . . ., pathToFileN
    -p MetaboLights Labs Project ID
    -n Create new project if project doesnt exist
    -s server [ "prod", "dev", "test" ]
"""

import os
import sys
import argparse
import logging
import json
import requests
import shutil
import subprocess
import tempfile

api_token = None
directories = []
files = []
project_id = None
new_project_flag = False
log_file = "cli.log"
env = "dev"
servers = ["prod", "dev", "test"]
serverPortDictionary = {
    "prod": {
        "server": "http://www.ebi.ac.uk/metabolights/",
        "port": ""
    },
    "dev": {
        "server": "http://wwwdev.ebi.ac.uk/metabolights/",
        "port": ""
    },
    "test": {
        "server": "http://localhost.ebi.ac.uk:8080/metabolights/",
        "port": ""
    }
}
tmpdir = ""


def main(arguments):
    logging.basicConfig(filename=log_file, level=logging.INFO)
    usage = """
    python uploadToMetaboLightsLabs.py -t <MetaboLights Labs API_KEY> -i [ <filesToUpload> ] -p <MetaboLights Labs Project_ID> -n -s <ENV>
    or
    uploadToMetaboLightsLabs.py -t <MetaboLights Labs API_KEY> -i [ <filesToUpload> ] -p <MetaboLights Labs Project_ID> -n -s <ENV>
    or
    python uploadToMetaboLightsLabs.py -t <MetaboLights Labs API_KEY> -I <path to IsaTab folder> -p <MetaboLights Labs Project_ID> -n -s <ENV>
    or 
    uploadToMetaboLightsLabs.py -t <MetaboLights Labs API_KEY> -I <path to IsaTab folder> -p <MetaboLights Labs Project_ID> -n -s <ENV>
Arguments:
    -t MetaboLights Labs API_KEY

    --i pathToFile1, pathToFile2, . . ., pathToFileN
    or
    --I pathToIsaTabfolder

    -p MetaboLights Labs Project ID
    -n Create new project if project doesnt exist
    -s server [ "prod", "dev", "test" ]
    """
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     usage=usage)
    parser.add_argument('-t', required=True, help='MetaboLights API Key')
    parser.add_argument('--i', required=False, nargs='+',
                        help="Input folder(s)/file(s)")
    parser.add_argument('--I', required=False,
                        help="Input folder containing ISA-Tab, raw, and maf files")
    parser.add_argument('-p', help='MetaboLights Labs Project ID')
    parser.add_argument('-n',
                        help='Create new MetaboLights Labs Project if doesnt exist',
                        action='store_true')
    parser.add_argument('-s', help='Server details. Allowed values are '.join(
        servers), choices=servers)
    args = parser.parse_args(arguments)
    # parser.print_help()
    logging.info("Validating Input Parameters")
    # validating input
    if parseInput(args):
        # Input validation success
        logging.info("Input validation Success")
        # Request MetaboLights Labs webservice for aspera upload configuration
        logging.info("Requesting project aspera upload configuration")
        asperaConfiguration = requestUploadConfiguration()
        logging.info("Required project details obtained")
        # Compile the aspera CLI command from the configuration
        logging.info("Compling aspera command")
        asperaCommand = compileAsperaCommand(asperaConfiguration)
        logging.info("Checking aspera Environment variables")
        executeAsperaUpload(asperaCommand)
    else:
        logging.info("Input validation Failed: Terminating program")
        print "Invalid Input: Please check the " + log_file + " for more details"


def executeAsperaUpload(cmds):
    cmd = filter(None, cmds[1])
    cmd = filter(bool, cmd)
    os.environ["ASPERA_SCP_PASS"] = cmds[0]
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    out, err = p.communicate()
    logging.info(out)
    if err:
        logging.error(err)
    else:
        logging.info("Files uploaded successfully")


def compileAsperaCommand(asperaConfiguration):
    asperaConfiguration = json.loads(asperaConfiguration)
    filesLocation = (str(
        ' '.join(str(e) for e in directories).strip() + " " + ' '.join(
            str(e) for e in files))).strip()
    remoteHost = asperaConfiguration['asperaUser'] + "@" + asperaConfiguration[
        'asperaServer'] + ":/" + env + "/userSpace/" + asperaConfiguration[
                     'asperaURL']
    logging.info(
        "Project Location:" + " '/" + env + "/userSpace/" + asperaConfiguration[
            'asperaURL'] + "'")
    asperaSecret = asperaConfiguration['asperaSecret']
    return [asperaSecret,
            "ascp -QT -L . -l 1g " + filesLocation + " " + remoteHost]


def requestUploadConfiguration():
    # Requesting MetaboLightsLabs Webservice for the project configuration
    url = serverPortDictionary[env][
              "server"] + "webservice/labs-workspace/asperaConfiguration"
    payload = json.dumps({'api_token': api_token, 'project_id': project_id,
                          'new_project_flag': new_project_flag})
    headers = {'content-type': "application/json", 'cache-control': "no-cache"}
    try:
        response = requests.request("POST", url, data=str(payload),
                                    headers=headers)
    except requests.exceptions.RequestException as e:  # This is the correct syntax
        logging.error(e)
        print "Request failed! Refer to the log file for more details"
        sys.exit(1)
    return json.loads(response.text)['content']


def parseInput(args):
    # Assigning the user api token to the global variable
    global api_token
    api_token = args.t
    logging.info('API Key:' + str(api_token))

    # Checking whether the input files and folders are valid and exist
    # Creating a array of files and folders that needs to be uploaded
    if args.i and not args.I:
        for entity in args.i:
            if os.path.isfile(entity):
                global files
                files.append(entity)
                logging.info(
                    "Adding " + entity + " to the files to be uploaded list")
            if os.path.isdir(entity):
                global directories
                directories.append(entity)
                logging.info(
                    "Adding " + entity + " to the folders to be uploaded list")
    elif args.I and not args.i:
        isatab_folder = args.I
        import glob, zipfile
        global tmpdir
        tmpdir = tempfile.mkdtemp()
        if os.path.isdir(isatab_folder):
            isazip_path = os.path.join(tmpdir, "isa.zip")
            with zipfile.ZipFile(isazip_path, "w") as zip:
                for isa_file in glob.glob(
                        "{}/[isa]*.txt".format(isatab_folder)):
                    zip.write(isa_file)
            files.append(isazip_path)
            mafzip_path = os.path.join(tmpdir, "maf.zip")
            with zipfile.ZipFile(mafzip_path, "w") as zip:
                for maf_file in glob.glob("{}/m_*.tsv".format(isatab_folder)):
                    zip.write(maf_file)
            files.append(mafzip_path)
            raw_data_types = ("*.mzml", "*.mzML", "*.nmrml", "*.nmrML")
            datazip_path = os.path.join(tmpdir, "data.zip")
            with zipfile.ZipFile(datazip_path, "w") as zip:
                data_files = []
                for file_type in raw_data_types:
                    data_files.extend(
                        glob.glob(os.path.join(tmpdir, file_type)))
                for data_file in data_files:
                    zip.write(data_file)
            files.append(datazip_path)
    else:
        logging.warning("No input folder or files provided")
        return False

    # Assigning env to the global variable
    global env
    env = args.s
    logging.info("Setting env flag: " + str(env))

    # Assigning create new flag to the global variable
    global new_project_flag
    new_project_flag = str(args.n).lower()
    logging.info("Create new project flag provided: " + str(new_project_flag))

    # Assigning ML project id to the global variable
    global project_id
    # If create new project flag is not set, making sure the project id exist
    if not new_project_flag:
        project_id = args.p
        logging.warning("Project_id assigned: " + str(project_id))
        if not project_id:
            logging.warning(
                "Project_ID not assigned. Please provide -n flag if you would like to create a new project")
            return False
    else:
        project_id = args.p
        logging.info("Project_id assigned @Input : " + str(project_id))

    # Checking if no files or folders exist
    if (len(files) == 0 and len(directories) == 0):
        logging.warning("No valid files or directories provided")
        return False
    return True


if __name__ == '__main__':
    try:
        sys.exit(main(sys.argv[1:]))
    finally:
        if tmpdir != '':
            shutil.rmtree(tmpdir)