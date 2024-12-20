#!/usr/bin/python3

import time
import urllib.request
import os
import schedule

temp_retries = 3
master_out = 'w1_bus_master1'
master_ice = 'w1_bus_master2'

pep_failed_file = os.path.expanduser("~") + "/displaylogger_pep_failed.txt"

sleep_min = 30

pep_url = "http://www.example.com?"


def getsensorpath(master):
    with open(os.path.join('/sys/bus/w1/devices', master, 'w1_master_slaves'), 'r') as f:
        return f.readline().strip()


def gettemp(id):
    for i in range(temp_retries):
        try:
            w1path = os.path.join('/sys/bus/w1/devices', id, 'w1_slave')
            with open(w1path, 'r') as file:
                line = file.readline()
                crc = line.rsplit(' ', 1)
                crc = crc[1].replace('\n', '')
                if crc == 'YES':
                    line = file.readline()
                    return float(line.rsplit('t=', 1)[1]) / 1000

        except Exception:
            pass

    return None


def gethum():
    try:
        with open('/sys/bus/iio/devices/iio:device0/in_humidityrelative_input', 'r') as f:
            value_str = f.readline()

        return int(value_str) / 1000
    except Exception:
        return 0


def set_heater(enable):
    with open('/sys/bus/iio/devices/iio:device0/heater_enable', 'w') as f:
        f.write("1" if enable else "0")


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
        print('Unknown error while sending {}{}: {}'.format(url, request, error))

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


def measure_and_send():
    id_out = getsensorpath(master_out)
    id_ice = getsensorpath(master_ice)
    temp_out = gettemp(id_out)
    temp_ice = gettemp(id_ice)

    if temp_out is not None and temp_ice is not None:
        new_request = time.strftime("year=%Y&month=%m&day=%d&hour=%H&minute=%M&") + \
                                    "temp_out={}&temp_ice={}&humidity={}".format(str(temp_out), str(temp_ice), gethum())

        send_data(pep_url, new_request, pep_failed_file)

    else:
        print("Failed to get temperature data, skipping")


if __name__ == '__main__':

    schedule.every().hour.at(":20").do(lambda: set_heater(True))
    schedule.every().hour.at(":29").do(lambda: set_heater(False))
    schedule.every().hour.at(":30").do(measure_and_send)

    schedule.every().hour.at(":50").do(lambda: set_heater(True))
    schedule.every().hour.at(":59").do(lambda: set_heater(False))
    schedule.every().hour.at(":00").do(measure_and_send)

    while True:
        schedule.run_pending()
        time.sleep(1)
