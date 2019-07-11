from __future__ import division
import requests
import time
import core
import configparser
from models import getsess


# function to retrieve the specific error message between two sites and with the event type
def get_details(dst_site, src_site, event_type, size=1):
    end_time = int(time.time() * 1000)
    event = event_type + '-failed'
    start_time = end_time - 1 * 3600 * 1000
    data = '{"search_type":"query_then_fetch","ignore_unavailable":true,"index":["monit_prod_ddm_enr_transfer_*"]}\n{"size":0,"query":{"bool":{"filter":[{"range":{"metadata.timestamp":{"gte":"%i","lte":"%i","format":"epoch_millis"}}},{"query_string":{"analyze_wildcard":true,"query":"data.event_type: %s AND data.dst_experiment_site:(\\"%s\\") AND data.src_experiment_site:(\\"%s\\")"}}]}},"aggs":{"2":{"terms":{"field":"data.reason","size":%i,"order":{"_count":"desc"},"min_doc_count":1},"aggs":{}}}}\n' % (start_time, end_time, event,  dst_site, src_site, size)
    return data


# this probably needs to be more secure
config = configparser.ConfigParser()
config.read('opint.cfg')
token = config['errorpopulator']['token']
HEADERS = {'Authorization': 'Bearer %s' % token}


# function to retrieve inefficient transfers between sites, or ineffecient deletion on a destination site.
def read_efficiency(activity, headers=HEADERS):
    URL = 'https://monit-grafana.cern.ch/api/datasources/proxy/7730/query?db=monit_production_ddm_transfers&q=SELECT%20sum(files_done),sum(files_total)%20FROM%20%22raw%22.%2F%5Eddm_transfer%24%2F%20WHERE%20%22state%22%20%3D%20%27{}%27%20AND%20time%20%3E%3D%20now()%20-%201h%20GROUP%20BY%20%22src_experiment_site%22%2C%20%22dst_experiment_site%22&epoch=ms'.format(activity)
    r = requests.get(URL, headers=HEADERS)
    result = []
    if r.status_code == 200:
        response = r.json()
        for link in response['results'][0]['series']:
            if link['values'][0][2] > 200:
                if (100 * (link['values'][0][1] / link['values'][0][2])) < 20:
                    result.append(list(link.items()))
        return result
    else:
        print('could not read efficiency')


# function that populates the error table with errors that cause a significant inefficiency between certain sites, this function should be run as a cron job and should run once every hour
def populate():
    session = getsess('sqlite:///robi.db')
    rows = session.execute('SELECT message, dst_site, src_site, amount FROM error').fetchall()
    if rows == []:
        print('its null')
    for row in rows:
        print (row.message, row.dst_site, row.src_site, row.amount)
        print('\n')
    for activity in ['transfer', 'deletion']:
        r = read_efficiency(activity, HEADERS)
        print('### %s-failures ### \n' % activity)
        for link in r:

            # following condition is a quick fix for when the read efficiency response is unordered.
            try:
                print(link)
                isinstance(link[1][1][0][1], int)
                sites = 3
                numbers = 1
            except KeyError:
                sites = 1
                numbers = 3

            data = get_details(link[sites][1]['dst_experiment_site'], link[sites][1]['src_experiment_site'], activity)
            try:
                r = requests.post('https://monit-grafana.cern.ch/api/datasources/proxy/8736/_msearch', headers=HEADERS, data=data)
            except Exception as e:
                print(e)
            resp = r.json()
            if resp['responses'][0]['aggregations']['2']['buckets'] == []:
                continue

            error_message = resp['responses'][0]['aggregations']['2']['buckets'][0]['key']
            count = resp['responses'][0]['aggregations']['2']['buckets'][0]['doc_count']
            dst_site = link[1][1]['dst_experiment_site']
            src_site = link[1][1]['src_experiment_site']
            exists_in_db = False
            # this needs to be reimplemented since the same error should exist multiple times in the error table
            # they will be tracked every hour
            for row in rows:
                if row.message == error_message and row.dst_site == dst_site and row.src_site == src_site:
                    print('existing error message with same sites detected, performing remapping')
                    exists_in_db = True
                    break
            if not exists_in_db:
                print('adding new error to the database')
                core.add_error(message=error_message, dst_site=dst_site, src_site=src_site, amount=count, failure_type=activity + '-failure')
            print('dst_site: %s,  src_site: %s' % (dst_site, src_site))
            print('Efficiency:  ' + str(100 * (link[numbers][1][0][1] / link[numbers][1][0][2])))
            print(resp)
            print('\n')
