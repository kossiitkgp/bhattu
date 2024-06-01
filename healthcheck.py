# write a healthcheck script that checks the status of the app for docker

import requests
import sys

def healthcheck(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            print('App is healthy')
        else:
            print('App is not healthy')
    except requests.exceptions.RequestException as e:
        print('App is not healthy')
        sys.exit(1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python healthcheck.py <url>')
        sys.exit(1)
    healthcheck(sys.argv[1])
