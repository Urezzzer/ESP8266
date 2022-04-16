from datetime import datetime
from sqlalchemy import func
from sqlalchemy import inspect

from flask_app import db
from tables import Metrics


def object_as_dict(obj):
    return {c.key: getattr(obj, c.key)
            for c in inspect(obj).mapper.column_attrs}


def query_metrics_with_borders(lower_border=None, upper_border=None, format='avg'):
    if format == 'avg':
        function = func.avg
    elif format == 'min':
        function = func.min
    elif format == 'max':
        function = func.max

    if lower_border and upper_border:
        rows = db.session.query(function(Metrics.t).label('t_mean'), function(Metrics.h).label('h_mean')). \
            filter(Metrics.time >= datetime.strptime(lower_border, '%Y-%m-%dT%H:%M')). \
            filter(Metrics.time <= datetime.strptime(upper_border, '%Y-%m-%dT%H:%M')).first()
    elif lower_border:
        rows = db.session.query(function(Metrics.t).label('t_mean'), function(Metrics.h).label('h_mean')). \
            filter(Metrics.time >= datetime.strptime(lower_border, '%Y-%m-%dT%H:%M')).first()
    elif upper_border:
        rows = db.session.query(function(Metrics.t).label('t_mean'), function(Metrics.h).label('h_mean')). \
            filter(Metrics.time <= datetime.strptime(upper_border, '%Y-%m-%dT%H:%M')).first()
    db.session.commit()

    return rows


def _round(value, decimal=2):
    if type(value) in [str, int, float]:
        return round(float(value), decimal)
    else:
        return value
