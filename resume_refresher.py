#!/usr/bin/env python3

import requests
import getpass

def jobs_refresh():
    password = getpass.getpass()
    r = requests.get("https://www.51job.com")
    print(r.text)
    r = requests.get("https://login.51job.com/login.php")
    print(r.text)
    pass

if __name__ == "__main__":
    jobs_refresh()
