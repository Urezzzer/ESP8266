from utilities import _round, query_metrics_with_borders, object_as_dict
from datetime import datetime, timedelta, timezone
from flask import request, jsonify, render_template, redirect, url_for

from flask_app import db, Metrics, Delay, app

timezone_offset = +10.0  # Vlavivostok
tzinfo = timezone(timedelta(hours=timezone_offset))

temperatures = []
humidities = []
all_data = []
_format = 'avg'


@app.route('/load_data/', methods=['POST'])
def load_data():
    """Метод внесения данных с устройства в БД"""
    success = False
    if request.method == 'POST':
        temperature = request.form['temperature']
        humidity = request.form['humidity']
        dt = datetime.now(tzinfo).replace(microsecond=0)
        db.session.add(Metrics(time=dt, t=temperature, h=humidity))
        db.session.commit()
        value = object_as_dict(Metrics.query.filter_by(time=dt).first())
        success = bool(value)
    return jsonify({
        'success': success
    })

@app.route('/config/', methods=['GET'])
def config():
    """Метод получения config (сейчас доступно управление частотой снятия показаний)"""
    try:
        delay = db.session.query(Delay).first().delay
    except:
        delay = '30000'
    return delay


@app.route('/date/', methods=['POST'])
def date():
    """Метод изменения истории измерений"""
    global temperatures, humidities, _format

    lower_border = request.form['lower-datetime']
    upper_border = request.form['upper-datetime']
    _format = request.form['format']

    if lower_border and upper_border:
        rows = query_metrics_with_borders(lower_border, upper_border, format=_format)
    elif lower_border:
        rows = query_metrics_with_borders(lower_border=lower_border, format=_format)
        upper_border = datetime.now(tzinfo).replace(second=0, microsecond=0).isoformat()
    elif upper_border:
        rows = query_metrics_with_borders(upper_border=upper_border, format=_format)
        lower_border = datetime(2021, 12, 20).isoformat()
    else:
        return redirect(url_for('index'))

    upper_border = datetime.fromisoformat(upper_border).strftime("%m.%d.%Y, %H:%M")

    lower_border = datetime.fromisoformat(lower_border).strftime("%m.%d.%Y, %H:%M")

    temperatures.insert(0, {'time': lower_border + ' - ' + upper_border, 't_mean': _round(rows[0])})
    humidities.insert(0, {'time': lower_border + ' - ' + upper_border, 'h_mean': _round(rows[1])})
    return redirect(url_for('index'))


@app.route('/clear/', methods=['GET', 'POST'])
def clear():
    """Метод очищения истории измерений"""
    global temperatures, humidities
    temperatures = []
    humidities = []
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    """[GET]:
            Метод выводящий главную страницу и получающий всю информацию для нее
       [POST]:
            Изменение частоты снятия показаний"""

    if request.method == 'POST':
        if request.form['delay']:
            if 20 <= int(request.form['delay']) <= 120:
                delay = str(int(request.form['delay']) * 1000)
                Delay.query.delete()
                db.session.commit()
                db.session.add(Delay(delay=delay))
                db.session.commit()

    global all_data
    # Получаю средние показатели за последние 24 часа
    lower_border = (datetime.now(tzinfo).replace(microsecond=0) - timedelta(days=1)).strftime('%Y-%m-%dT%H:%M')
    day_means = query_metrics_with_borders(lower_border=lower_border)

    day_means = {'t_mean': _round(day_means[0]),
                 'h_mean': _round(day_means[1])}
    # Получаю средние показатели за прошлую неделю
    lower_border = (datetime.now(tzinfo).replace(hour=0, minute=0, second=0, microsecond=0) -
                    timedelta(days=7 + datetime.now(tzinfo).weekday())).strftime('%Y-%m-%dT%H:%M')
    upper_border = (datetime.now(tzinfo).replace(hour=23, minute=59, second=59, microsecond=0) -
                    timedelta(days=datetime.now(tzinfo).weekday() + 1)).strftime('%Y-%m-%dT%H:%M')

    week_means = query_metrics_with_borders(lower_border, upper_border)
    week_means = {'t_mean': _round(week_means[0]),
                  'h_mean': _round(week_means[1])}

    # Получаю средние показатели за прошлый месяц
    upper_border = datetime.now(tzinfo).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    lower_border = (upper_border - timedelta(days=upper_border.day) + timedelta(seconds=1)).strftime('%Y-%m-%dT%H:%M')
    upper_border = upper_border.strftime('%Y-%m-%dT%H:%M')
    month_means = query_metrics_with_borders(lower_border, upper_border)
    month_means = {'t_mean': _round(month_means[0]),
                   'h_mean': _round(month_means[1])}

    if not all_data:
        # Получаю все данные за месяц
        lower_border = datetime.now(tzinfo).replace(microsecond=0) - timedelta(days=7)
        rows = db.session.query(Metrics). \
            filter(Metrics.time >= lower_border).all()
        db.session.commit()
        all_data = [object_as_dict(row) for row in rows][::-1]

    return render_template('base.html', day_means=day_means, week_means=week_means,
                           month_means=month_means, delay=int(config()) // 1000,
                           temperatures=temperatures, humidities=humidities, all_data=all_data)


@app.route('/cur_values', methods=['GET'])
def get_cur_values():
    """Метод получения текущих значений"""
    lower_border = (
            datetime.now(tzinfo).replace(microsecond=0) - timedelta(seconds=(int(config()) // 1000) + 5)).strftime(
        '%Y-%m-%dT%H:%M')
    cur_means = query_metrics_with_borders(lower_border=lower_border)
    cur_means = {'t_mean': cur_means[0],
                 'h_mean': cur_means[1]}
    return cur_means


@app.route('/get_format', methods=['GET'])
def get_format():
    """Метод получения формата запрошенных измерений"""
    global _format
    return {'format': _format}


@app.route('/delete_values', methods=['POST'])
def delete_cur_values():
    """Удаление текущего значения"""
    dt = request.args['dt']
    Metrics.query.filter(Metrics.time == datetime.strptime(dt, '%Y-%m-%dT%H:%M')).delete()
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/date_index/', methods=['POST'])
def date_index():
    """Метод вывода всех данных за определенный день"""
    global all_data

    date = request.form['datetime']

    if date:
        date += 'T00:00'
        lower_border = datetime.strptime(date, '%Y-%m-%dT%H:%M')
        upper_border = datetime.strptime(date, '%Y-%m-%dT%H:%M') + timedelta(hours=23, minutes=59, seconds=59)
        rows = db.session.query(Metrics). \
            filter(Metrics.time >= lower_border).filter(Metrics.time <= upper_border).all()
        all_data = [object_as_dict(row) for row in rows][::-1]
    else:
        lower_border = datetime.now(tzinfo).replace(microsecond=0) - timedelta(days=7)
        rows = db.session.query(Metrics). \
            filter(Metrics.time >= lower_border).all()
        db.session.commit()
        all_data = [object_as_dict(row) for row in rows][::-1]

    return redirect(url_for('index'))
