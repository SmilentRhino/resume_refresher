#!/usr/bin/env python3
#coding=utf-8

'''
This is a simple script to refresh my resume on 51job.com.
It simulate what we do from a real web browser, kind of like a spider.
'''

import time
import random
import re
import json
import hashlib
import logging
import logging.config
import logging.handlers
from multiprocessing import Process
from bs4 import BeautifulSoup
import requests

def main():
    '''
    The main function, start one process to refresh resume on each job hunting
    website.
    '''
    with open('logging_config.json', 'r') as logging_config_file:
        logging_config = json.load(logging_config_file)
    logging.config.dictConfig(logging_config)
    logging.getLogger(__name__)
    with open('user_profiles.json', 'r') as config_file:
        user_profiles = json.load(config_file)
    if not user_profiles:
        exit()
    if user_profiles['51jobs']['isOn']:
        jobs_process = Process(target=fiveone_jobs_refresh, args=(
            user_profiles['51jobs']['user_name'],
            user_profiles['51jobs']['user_password'],))
        jobs_process.start()
    if user_profiles['zhaopin']['isOn']:
        zhaopin_process = Process(target=zhaopin_refresh, args=(
            user_profiles['zhaopin']['user_name'],
            user_profiles['zhaopin']['user_password'],))
        zhaopin_process.start()
    if user_profiles['liepin']['isOn']:
        zhaopin_process = Process(target=liepin_refresh, args=(
            user_profiles['liepin']['user_name'],
            user_profiles['liepin']['user_password'],))
        zhaopin_process.start()


def fiveone_jobs_refresh(login_name, password):
    '''
    refresh resume on 51jobs, and log the company who has view your message.
    '''
    #initialize request session
    logging.debug('51jobs initialize session')
    session = requests.Session()
    user_agent = "Mozilla/5.0 (X11;Ubuntu;Linux x86_64;rv:50.0) Gecko/20100101 Firefox/50.0"
    session.headers.update({"User-Agent" : user_agent})

    #get index page, and then login
    response = session.get("https://www.51job.com")
    logging.debug(response.text)
    response = session.get("https://login.51job.com/login.php")
    logging.debug("Go to 51jobs login page")
    logging.debug(response.text)
    payload = {"lang" : "c",
               "action" : "save",
               "from_domain" : "i",
               "loginname" : login_name,
               "password" : password,
               "verifycode": "",
               "isread" : "on"}
    response = session.post("https://login.51job.com/login.php", data=payload)
    logging.debug("Loging 51jobs and get personal home page")
    logging.debug(response.text)

    ##get resumeid
    match = re.search(r"resumeid=(?P<resumeid>\d+)", response.text)
    if match:
        resume_id = match.group('resumeid')

    last_view = '' #the last company viewed my resume

    while True:
        #simulate ajax request to refresh the resume
        random_str = str(random.random())
        refresh_url = "http://i.51job.com/resume/ajax/refresh_resume.php?" +\
            random_str + \
            '&jsoncallback=1' +\
            "&ReSumeID=" + resume_id +\
            "&Lang=c" + \
            "&all=all" + \
            "&_="+ str(int(time.time()*1000))
        logging.debug('refresh 51jobs resume payload')
        logging.debug(payload)
        response = session.get(refresh_url, data=payload)
        logging.info('51job resume refresh result')
        logging.info(response.text)

        # get resume view history
        response = session.get(
            "http://my.51job.com/cv/CResume/CV_CResumeViewMonth.php")
        logging.debug('51job resume view history')
        logging.debug(response.text)

        # paser view history, if viewed by new company, record it
        resume_viewed_page = response.content.decode("GBK")
        parsed_history = BeautifulSoup(resume_viewed_page, 'html.parser')
        read_view_box = parsed_history.find("div", class_="read_box_main")
        current_view = read_view_box.a.text
        if current_view != last_view:
            logging.info('51job new company view my resume')
            logging.info(current_view)
        last_view = current_view
        time.sleep(180)

def zhaopin_refresh(login_name, password):
    '''
    refresh resume on 51jobs, and log the company who has view your message.
    '''
    #initialize request session
    logging.debug('zhaopin initialize session')
    session = requests.Session()
    user_agent = "Mozilla/5.0 (X11;Ubuntu;Linux x86_64;rv:50.0) Gecko/20100101 Firefox/50.0"
    session.headers.update({"User-Agent" : user_agent})

    #get index page, and then login
    response = session.get("http://www.zhaopin.com")
    payload = {"int_count" : "999",
               "RememberMe" : "true",
               "errUrl" : "https://passport.zhaopin.com/account/login",
               "requestFrom" : "portal",
               "loginname" : login_name,
               "Password" : password}

    ##update freferer header to pass around nginx validation
    session.headers.update({"Referer":"http://www.zhaopin.com/"})
    response = session.post("https://passport.zhaopin.com/account/login", data=payload)
    logging.debug('zhaopin.com login result')
    logging.debug(response.text)

    ##get resumenum and version from home page
    response = session.get("http://i.zhaopin.com/")
    zhaopin_index = response.text
    soup = BeautifulSoup(zhaopin_index, "html.parser")
    refresh_url = soup.find('a', class_="myLinkA linkRefresh")
    match = re.search(
        r'resumeId=(?P<resumeId>.*?)&extId=(?P<resumenum>.*?)&version=(?P<version>.*?)&',
        refresh_url['url'])
    if not match:
        exit()

    ## refresh both chinese and english resume every 200s
    refresh_payload = {"resumeId" : match.group('resumeId'),
                       "resumenum" : match.group('resumenum'),
                       "version" : match.group('version'),
                       "language" : "1",
                       "t" : str(int(time.time()*1000))}
    session.headers.update({"Referer":"http://i.zhaopin.com/"})
    while True:
        refresh_payload['language'] = '1'
        response = session.get(
            "http://i.zhaopin.com/ResumeCenter/MyCenter/RefreshResume",
            data=refresh_payload)
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.info('zhaopin.com chinese resume refresh result')
        logging.info(soup.h3.text)
        logging.debug(response.text)
        time.sleep(30)
        refresh_payload['language'] = '2'
        response = session.get(
            "http://i.zhaopin.com/ResumeCenter/MyCenter/RefreshResume",
            data=refresh_payload)
        soup = BeautifulSoup(response.text, 'html.parser')
        logging.info('zhaopin.com english resume refresh result')
        logging.info(soup.h3.text)
        logging.debug(response.text)
        time.sleep(200)

def liepin_refresh(login_name, password):
    '''
    refresh resume on 51jobs, and log the company who has view your message.
    '''
    #initialize request session
    session = requests.Session()
    user_agent = "Mozilla/5.0 (X11;Ubuntu;Linux x86_64;rv:50.0) Gecko/20100101 Firefox/50.0"
    session.headers.update({"User-Agent" : user_agent})
    password = hashlib.md5(password.encode()).hexdigest()

    #get index page, and then login
    response = session.get("https://www.liepin.com")
    logging.debug(response.text)
    ##get randomcodenoise
    response = session.get("https://passport.liepin.com/captcha/randomcodenoise")
    logging.debug(response.text)
    payload = {"layer_from" : "wwwindex_rightbox_new",
               "user_pwd" : password,
               "user_login" : login_name,
               "chk_remember_pwd" : "on"}
    session.headers.update(
        {"Referer":"https://passport.liepin.com/ajaxproxy.html",
         "X-Alt-Referer" : "https://www.liepin.com/",
         "X-Requested-With" : "XMLHttpRequest"})

    ##set cookie before send ajax request
    ## original js code from www.liepin.com
    ##encryptMobile: function encryptMobile(name, value) {
    ##    var md5key, md5value;
    ##    return name && value && (value = value.split("").sort()
    ##        .join("") + name, md5key = this.md5(value).substring(
    ##            4, 12), value = value.split("").sort().join(
    ##            ""), md5value = this.md5(value), LT.Cookie
    ##        .set(md5key, md5value, !1, "/",
    ##            "liepin.com")), this
    ##}

    cookie_name = ''
    cookie_value = ""
    sorted_login_name = ''.join(sorted(login_name))
    temp_value = sorted_login_name + 'user_login'
    cookie_name = hashlib.md5(temp_value.encode()).hexdigest()[4:12]
    sorted_temp_value = ''.join(sorted(temp_value))
    logging.debug(sorted_temp_value)
    cookie_value = hashlib.md5(sorted_temp_value.encode()).hexdigest()
    session.cookies.set(cookie_name, cookie_value)
    logging.debug(session.cookies)

    ##log in
    response = session.post(
        "https://passport.liepin.com/c/login.json?__mn__=user_login",
        data=payload)
    logging.debug(response.text)

    ##get randomcode
    response = session.get(
        "https://passport.liepin.com/captcha/randomcode?0.2108040844835467")
    logging.debug(response.text)

    ##get personal home page
    home_url = "https://c.liepin.com/?time=" + str(int(time.time()*1000))
    response = session.get(home_url)
    logging.debug('liepin personal home page')
    logging.debug(response.text)

    ##get resume id
    soup = BeautifulSoup(response.text, 'html.parser')
    resume_id = soup.find('a', attrs={'data-selector' : 'resumeRefresh'})
    if resume_id:
        resume_id = resume_id['data-value']
    logging.debug("liepin resumeid:"+resume_id)

    ##refresh resume every 180s
    #payload = {'res_id_encode' : resume_id}
    refresh_url = "https://c.liepin.com/resume/refreshresume.json?"
    refresh_url += 'res_id_encode=' + resume_id
    while True:
        response = session.get(refresh_url)
        logging.info('liepin resume refresh result')
        logging.info(response.text)
        time.sleep(180)
if __name__ == "__main__":
    main()
