## http://jinja.pocoo.org/docs/dev/templates/
## http://flask.pocoo.org/docs/0.10/templating/
## https://developer.mozilla.org/en-US/docs/Web/API/Web_Storage_API/Using_the_Web_Storage_API

import json
from flask import Flask, jsonify, request, render_template
import os, time, datetime
from report import analyze_log
import simplejson
import ast

PATH = os.path.dirname(os.path.realpath(__file__))

app = Flask(__name__, static_folder='static')

NUM_HOSTS = 5

LOGS_DICT = {}

def string_unix_timestamp(s):
    return time.mktime(datetime.datetime.strptime(s, "%Y/%m/%d").timetuple())
def parse_timeseries(ts, idx=1):
    _day_wise = {}
    for each in ts.split("\n"):
        _ts = each.replace('[',"").replace(']',"").split('\t')
        _date = string_unix_timestamp(_ts[0].split()[0])
        if _day_wise.get(_date, None) is None:
            _day_wise[_date] = 0
        _day_wise[_date] += int(_ts[idx])
    return  [[k,v] for k,v in _day_wise.iteritems()]

if False:
    VALID_HOSTS = ["site{}.com".format(i) for i in range(1,NUM_HOSTS+1)]
    VALID_HOSTS[len(VALID_HOSTS)-1] = 'kite5.com'
    TRACKER_HOST = "green-tracker.com"
    ACCELERATE = 1
    LOGFILE = '{}/{}'.format(PATH,'logs/collect.jl')

else:
    VALID_HOSTS = ["site{}.test.cliqz.com".format(i) for i in range(1,NUM_HOSTS+1)]
    TRACKER_HOST = "green-tracker.fbt.co"
    ACCELERATE = 1
    LOGFILE = '/mnt/logs/collect.jl'

logf = open(LOGFILE,'a')

start_time = int(round(time.time() * 1000))

@app.route('/', defaults={'path': ''}, methods=['GET', 'POST'])
@app.route('/<path:path>', methods=['GET', 'POST'])
def any(path):

    ##if path == '/favicon.ico':
    ##    return 'ok'
    pretty_host = request.host.split(':')[0]
    if pretty_host.startswith('www.'):
        pretty_host = pretty_host[4:]

    #if pretty_host == TRACKER_HOST and path == '/greetracker.js':
        ## serve the tracker.js
    #    a=1

    elif pretty_host == 'subdomain.'+TRACKER_HOST:
        return render_template('/template_introspect_localstorage.html')

    elif pretty_host == TRACKER_HOST:
        if path == 'collect':
            try:
                oo = request.json
                logf.write(json.dumps(oo)+'\n')
                logf.flush()
            except:
                print "Error on collect! {}".format(request.json)
            return jsonify({'ok': True})
        if path == 'frame':
            context = {}
            context['tracker_host'] = TRACKER_HOST
            for v, i in zip(VALID_HOSTS, range(0, len(VALID_HOSTS))):
                context['site{}'.format(i+1)] = v
            if ACCELERATE > 1:
                context['accelerate'] = {'speed': ACCELERATE, 'start_time': start_time}
            return render_template('/template_frame.html', context=context)
        elif path == 'introspect/messages':
            context = {'tracker_host': TRACKER_HOST}
            return render_template('/template_introspect_messages.html', context=context)
        elif path == 'introspect/localstorage':
            context = {'tracker_host': TRACKER_HOST}
            context['site1'] = VALID_HOSTS[0]
            return render_template('/template_introspect_localstorage.html', context=context)
        elif path == 'logfile':
            ## 'http://green-tracker.com/logfile?name=logs/collect.jl.bkp1'
            qs = dict([request.query_string.split('=')])
            context = analyze_log('{}/{}'.format(PATH,qs.get('name', None)))
            context['site1'] = VALID_HOSTS[0]
            context['canned_report'] = True
            return render_template('/template_log.html', context=context)
        elif path == 'dashboard':
            context = analyze_log(LOGFILE)
            context['site1'] = VALID_HOSTS[0]
            print context
            global LOGS_DICT
            LOGS_DICT = context
            return render_template('/dashboard.html', context=context)
        elif path == 'metric_details':
            _n = dict([request.query_string.split('=')]).get('name').split("|")
            n = _n[0]
            if len(_n) > 1:
                idx = int(_n[1]) - 1
            doc = {}
            slug = []
            # slug = [[1460930400, 1], [1456700400, 1], [1460066400, 2], [1457564400, 2], [1457391600, 2], [1461189600, 1], [1460325600, 2], [1461276000, 3], [1460412000, 15], [1461016800, 4], [1460498400, 19], [1460584800, 6], [1461535200, 2], [1460671200, 14], [1459375200, 3], [1456441200, 4], [1460757600, 14], [1461708000, 2], [1456527600, 1], [1454713200, 1], [1460844000, 2], [1456614000, 1], [1459980000, 1], [1458082800, 1]]
            if n == "site_uv":
                slug = parse_timeseries(LOGS_DICT["sites"][idx]['timeseries'])
                 #[[1460930400, 1], [1456700400, 1], [1460066400, 2], [1457564400, 2], [1457391600, 2], [1461189600, 1], [1460325600, 2], [1461276000, 3], [1460412000, 15], [1461016800, 4], [1460498400, 19], [1460584800, 6], [1461535200, 2], [1460671200, 14], [1459375200, 3], [1456441200, 4], [1460757600, 14], [1461708000, 2], [1456527600, 1], [1454713200, 1], [1460844000, 2], [1456614000, 1], [1459980000, 1], [1458082800, 1]]
            elif n == "signup":
                slug = parse_timeseries(LOGS_DICT["goals"][0]['timeseries'])
            elif n == "site_loads":
                slug = parse_timeseries(LOGS_DICT["sites"][idx]['timeseries'], 2)
            elif n == "x_y":
                slug = parse_timeseries(LOGS_DICT["correlations"][idx]['timeseries'], 1)
            doc['data'] =  slug
            return simplejson.dumps(doc)
        else:
            context = analyze_log(LOGFILE)
            context['site1'] = VALID_HOSTS[0]
            return render_template('/template_log.html', context=context)

    elif pretty_host in VALID_HOSTS:

        context = {}

        if ACCELERATE > 1:
            context['accelerate'] = {'speed': ACCELERATE, 'start_time': start_time}

        context['tracker_host'] = TRACKER_HOST
        context['bg'] = 'bg-color-site-{}'.format(VALID_HOSTS.index(pretty_host)+1)
        context['path'] = request.path
        context['host'] = pretty_host
        if context['path'] == '/':
            context['title'] = pretty_host
        else:
            context['title'] = '{}{}'.format(pretty_host, context['path'])

        context['other_sites'] = [('http://{}/'.format(h), 'Visit site #{}'.format(i))
                                    for h, i in zip(VALID_HOSTS, range(1, NUM_HOSTS+1))]

        context['other_sites'] = context['other_sites'] + [('http://{}/page-10.html'.format(h), 'Page 10 on site #{}'.format(i))
                                    for h, i in zip(VALID_HOSTS, range(1, NUM_HOSTS+1))]

        context['other_pages'] = [('/page-{}.html'.format(i), 'Page {}'.format(i))
                                    for i in range(1,11)]


        return render_template('/template_sites.html', context=context)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, processes=8, debug=False)
