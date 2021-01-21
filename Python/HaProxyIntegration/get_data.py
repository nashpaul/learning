from requests import Session
from bs4 import BeautifulSoup as bs
import csv
from sqlalchemy import  create_engine, text as sa_text
from sqlalchemy.orm import sessionmaker
from classes import *
from time import sleep
import logging
import os
import json



def load_settings_fJSON(fJSON):
    if os.path.exists(fJSON):
        try:
            with open(fJSON, 'r') as file:
                data = json.load(file)
                return data
        except:
            return {'settings': ''}
    return {'settings':''}

def write_settings_fJSON(fJSON, jsondata):
    with open(fJSON, 'w') as file:
        json.dump(jsondata, file, indent=3)

def bs_fetch_data():
    def get_url_login_from_link(link):
        str_to_cut=link.split('/',3)
        ready_login_link=link.replace('/'+str_to_cut[3],'')
        return ready_login_link

    def get_data_from_csv(page_decoded):
        data_dict = []
        if not page_decoded.startswith('# '):
            raise Exception(f'Can\'t get data from {SETTINGS["HAproxy"]["URL"]}')
        page_fixed_names = page_decoded[2:]
        page_in_list = page_fixed_names.splitlines()
        csvreader = csv.DictReader(page_in_list)
        for line in csvreader:
            data_dict.append(line)
        logging.info(f'Returned {len(data_dict)} from HA')
        return data_dict


    with Session() as s:
        url_login=get_url_login_from_link(SETTINGS['HAproxy']['URL'])
        site = s.get(url_login)
        bs_content = bs(site.content, "html.parser")
        token = bs_content.find("input", {"name": "__csrf_magic"})["value"]
        login_data = {"__csrf_magic": token, "usernamefld": SETTINGS['HAproxy']['username'], 'passwordfld': SETTINGS['HAproxy']['password'],  'login': 'Sign In'}
        s.post(url_login, login_data)
        ha_page = s.get(SETTINGS['HAproxy']['URL'])
        page_decoded=ha_page.content.decode('utf-8')
        data_dict=get_data_from_csv(page_decoded)
        return data_dict

def push_data(data_in_dict):
    if not data_in_dict or len(data_in_dict)==0:
        raise Exception('Empty_data_from_HA')
    connection_str=f'mysql+pymysql://{SETTINGS["Database"]["username"]}:{SETTINGS["Database"]["password"]}@{SETTINGS["Database"]["ip"]}:{SETTINGS["Database"]["port"]}/{SETTINGS["Database"]["base"]}'
    engine = create_engine(connection_str, echo=SETTINGS['Database']['echo_debug'])
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine, autocommit=False)
    session = Session()
    session.execute(sa_text('''Truncate table HAhosts'''))
    counter_insert=0
    for h in data_in_dict:
        if h['svname'] in ('BACKEND', 'FRONTEND'):
            continue
        if h['pxname'] not in SETTINGS['HAproxy']['pxname_filter']:
            continue
        host1 = Host()
        host1.pxname = h['pxname']
        host1.svname = h['svname']
        host1.status = h['status']
        host1.scur = h['scur']
        host1.addr,host1.port = h['addr'].split(':')
        host1.algo = h['algo']
        session.add(host1)
        counter_insert+=1
    session.commit()
    logging.info(f'Inserted {counter_insert} lines')
    session.close()

def init_all():
    def logger1():
        logfile = os.path.join(log_path, "application1.log")
        logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', filename=logfile)
        root = logging.getLogger()
        root.setLevel(os.environ.get("LOGLEVEL", SETTINGS["LogDebugLevel"]))
    def pathes():
        global start_path,log_path,settings_path
        start_path = os.path.dirname(os.path.realpath(__file__))
        log_path = os.path.join(start_path, 'logs')
        settings_path = os.path.join(start_path, 'settings.json')
    def set_settings():
        global SETTINGS
        SETTINGS = load_settings_fJSON(settings_path)



    pathes()
    set_settings()
    logger1()

init_all()

while True:
    try:
        logging.info('Starting')
        data_in_dict = bs_fetch_data()
        push_data(data_in_dict)
        logging.info('Finishing')
        logging.info(f'Slepping for {SETTINGS["PullTimeout"]} sec.')
        sleep(SETTINGS['PullTimeout'])
    except Exception as e:
        logging.error(e)
        print(e)
        logging.info(f'Slepping for {SETTINGS["PullTimeout"]} sec.')
        sleep(SETTINGS['PullTimeout'])


