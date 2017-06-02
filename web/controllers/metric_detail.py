from flask import request, render_template
from models.message import Message
from models.site import Site
from index import db, app
from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker, scoped_session
from operator import itemgetter
import json

def get_response_string(data):
    obj = {
        'data': data,
        'sum': sum(map(itemgetter(1), data))
    }
    return json.dumps(obj)


class MetricData():

    Session = scoped_session(sessionmaker(bind=db.engine))

    def respond(self):
        metric = request.args['name']
        token = request.args['token']
        metric_fn = getattr(self, 'report_' + metric, None)
        if callable(metric_fn):
            return get_response_string(metric_fn(token, **request.args))
        return get_response_string([])

    def report_uv_all(self, token, **kwargs):
        return self.messages_per_interval(token, message_type='new_all', interval_size='day')

    def report_uv_month(self, token, **kwargs):
        return self.messages_per_interval(token, message_type='new_month', interval_size='day')

    def report_uv_day(self, token, **kwargs):
        return self.messages_per_interval(token, message_type='new_day', interval_size='day')

    def messages_per_interval(self, token, message_type,
            interval_size='day',
            since=datetime.utcnow() - timedelta(30), 
            until=datetime.utcnow()):
        s = self.Session()

        options = {
            'site_key': token,
            'msg_type': message_type,
            'since': since,
            'until': until,
            'interval_size': interval_size
        }

        grouped_counts = s.execute('''
            SELECT extract(epoch from day) as ts, COUNT(*) AS uniques
            FROM (SELECT date_trunc(:interval_size, ts) AS day
                FROM messages
                WHERE site_id = (SELECT site_id FROM sites WHERE site_key = :site_key)
                AND message->>'type' = :msg_type
                AND ts >= :since
                AND ts < :until) uniques
            GROUP BY day
            ORDER BY day ASC
        ''', options).fetchall()

        return [[int(ts), count] for ts, count in grouped_counts]
