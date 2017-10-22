#!/usr/bin/python3

import time
import urllib.request
import os
from os.path import expanduser, isfile

id_out = '28-000003aa674d'
id_ice = '28-0000052ba923'

phant_host = 'data.sparkfun.com'
public_key = 'xxxxxxxxxxxxxxxxxxxx'
private_key = 'yyyyyyyyyyyyyyyyyyyy'
delete_key = 'zzzzzzzzzzzzzzzzzzzz'

phant_failed_file = expanduser("~") + "/displaylogger_phant_failed.txt"
pep_failed_file = expanduser("~") + "/displaylogger_pep_failed.txt"

sleep_min = 30

phant_url = "https://{}/input/{}?private_key={}&".format(phant_host, public_key, private_key)
pep_url = "http://www.example.com?"

def gettemp(id):
  try:  
    with open('/sys/bus/w1/devices/' + id + '/w1_slave', 'r') as file:
      line = file.readline()
      crc = line.rsplit(' ', 1)
      crc = crc[1].replace('\n', '')
      if crc == 'YES':
        line = file.readline()
        return float(line.rsplit('t=', 1)[1]) / 1000
      else:
        return 85

  except Exception:
    return 85


def send_data(url, new_request, failed_file):
    requests = []
    success = 0

    if os.path.isfile(failed_file):
      with open(failed_file, 'r') as file:
        requests = [line.rstrip('\n') for line in file]

    requests.append(new_request)

    try:
      for request in requests:
        urllib.request.urlopen(url + request)
        success += 1
        print('Successfully sent request {}{}'.format(url, request))
    except urllib.error.HTTPError as error:
      print('HTTP error while sending {}{}: {}'.format(url, request, error.read()))
    except urllib.error.URLError as error:
      print('URL error while sending {}{}: {}'.format(url, request, error))
    except Exception as error:
      print('Unknown error while sending {}{}'.format(url, request))

    still_failing = requests[success:]

    if still_failing:
      if success == 0:
        with open(failed_file, "a") as file:
          file.write(requests[-1] + '\n')
      else:
        with open(failed_file, "w") as file:
          for request in still_failing:
            file.write(request + '\n')
    else:
      if os.path.isfile(failed_file):
        os.remove(failed_file)


if __name__ == '__main__':
  while True:

    current_time = time.localtime()
    time.sleep((3600 - current_time.tm_min * 60 - current_time.tm_sec - 1) % (sleep_min * 60) + 1)

    new_request = time.strftime("year=%Y&month=%m&day=%d&hour=%H&minute=%M&") + \
                  "temp_out={}&temp_ice={}&humidity={}".format(str(gettemp(id_out)), str(gettemp(id_ice)), 0)

    send_data(pep_url, new_request, pep_failed_file)
    #send_data(phant_url, new_request, phant_failed_file)

