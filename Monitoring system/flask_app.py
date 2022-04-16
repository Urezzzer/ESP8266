"""Ерилов и Нечухаева"""
import json
import time

from flask import Flask, request, jsonify, render_template, redirect, url_for, Response
from database_manager import DataBaseManager
from datetime import datetime, timedelta
import random

temperatures = []
humidity = []
app = Flask(__name__)

DATABASE = 'data.db'
manager = DataBaseManager(DATABASE)
delay = '15000'


# DON'T TOUCH!!!
@app.route('/load_data/', methods=['POST'])
def load_data():
    if request.method == 'POST':
        temperature = request.form['temperature']
        humidity = request.form['humidity']
        dt = datetime.now().replace(microsecond=0)
        status = manager.add(temperature, humidity, dt)
        return jsonify({
            'success': status
        })
    return jsonify({
        'success': False
    })


# DON'T TOUCH!!!
@app.route('/config/', methods=['GET'])
def config():
    """Метод получения config (сейчас доступно управление частотой снятия показаний)"""
    global delay

    return delay


@app.route('/test/', methods=['GET', 'POST'])
def test():
    """Тестирование тут"""
    return manager.get()


@app.route('/date/', methods=['POST'])
def date():
    global temperatures, humidity

    lower_border = request.form['lower-datetime']
    upper_border = request.form['upper-datetime']
    if lower_border and upper_border:
        selected_mean = manager.get(lower_border=lower_border, upper_border=upper_border, mode="mean")
    elif lower_border:
        selected_mean = manager.get(lower_border=lower_border, mode="mean")
        upper_border = datetime.now().replace(second=0, microsecond=0).isoformat()
    elif upper_border:
        selected_mean = manager.get(upper_border=upper_border, mode="mean")
        lower_border = datetime(2021, 12, 20).isoformat()

    upper_border = datetime.fromisoformat(upper_border).strftime("%m/%d/%Y, %H:%M:%S")

    lower_border = datetime.fromisoformat(lower_border).strftime("%m/%d/%Y, %H:%M:%S")

    temperature = {'date': lower_border + ' - ' + upper_border, 'mean': selected_mean['temperature']['mean']}
    temperatures.insert(0, temperature)
    humidity1 = {'date': lower_border + ' - ' + upper_border, 'mean': selected_mean['humidity']['mean']}
    humidity.insert(0, humidity1)
    return redirect(url_for('index'))


@app.route('/clear/', methods=['GET', 'POST'])
def clear():
    global temperatures, humidity
    temperatures = []
    humidity = []
    return redirect(url_for('index'))


@app.route('/', methods=['GET', 'POST'])
def index():
    global delay

    # Обработка POST
    if request.method == 'POST':
        if request.form['delay']:
            if 10 <= int(request.form['delay']) <= 100:
                # Здесь бы еще сделать вывод ошибки пользователю, что ввел слишком маленькое
                # или слишком большое количество секунд
                delay = str(int(request.form['delay']) * 1000)

    # Получаю средние показатели за последние 24 часа
    lower_border = datetime.now().replace(microsecond=0) - timedelta(days=1)
    day_means = manager.get(lower_border=lower_border, mode="mean")

    # Получаю средние показатели за прошлую неделю
    lower_border = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0) - \
                   timedelta(days=7 + datetime.now().weekday())
    upper_border = datetime.now().replace(hour=23, minute=59, second=59, microsecond=0) - \
                   timedelta(days=datetime.now().weekday() + 1)
    week_means = manager.get(lower_border=lower_border, upper_border=upper_border, mode="mean")

    # Получаю все данные за прошлую неделю
    week_data = manager.get(lower_border=lower_border, mode="data")
    list_week_data = []

    for i, objects in enumerate(week_data['temperature'].values()):
        list_week_data.append({
            't': objects['t'],
            'val_t': objects['value'],
            'val_h': week_data['humidity'][i]['value'],
        })

    # Получаю средние показатели за прошлый месяц
    upper_border = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
    lower_border = upper_border - timedelta(days=upper_border.day) + timedelta(seconds=1)
    month_means = manager.get(lower_border=lower_border, upper_border=upper_border, mode="mean")

    # Получаю текущие данные
    lower_border = datetime.now().replace(microsecond=0) - timedelta(seconds=int(config()) // 1000)
    cur_means = manager.get(lower_border=lower_border, mode="mean")

    return render_template('base.html', day_means=day_means, week_means=week_means,
                           month_means=month_means, cur_means=cur_means, delay=int(config()) // 1000,
                           temperatures=temperatures, humidity=humidity, all_data=list_week_data)


@app.route('/cur_values', methods=['GET'])
def get_cur_values():
    # Получаю текущие данные
    lower_border = datetime.now().replace(microsecond=0) - timedelta(seconds=int(config()) // 1000)
    cur_means = manager.get(lower_border=lower_border, mode="mean")
    return cur_means


@app.route('/delete_values', methods=['POST'])
def delete_cur_values():
    # Получаю текущие данные
    dt = request.args['dt']
    manager.delete(dt)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(threaded=True)
