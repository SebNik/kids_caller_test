# this is a WhatsApp bot, which can send and get messages
# it is used to control devices which can call the kids upstairs
from flask import request, render_template, jsonify, flash, redirect, Flask
import requests
import json
from twilio.twiml.messaging_response import MessagingResponse
import datetime
from flask_sqlalchemy import SQLAlchemy
import os

# connecting to flask app
app = Flask(__name__)
# defining folder path for sqlite file
basedir = os.path.abspath(os.path.dirname(__file__))
# app config for SQLALCHEMY path and sqlite file
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# Status Kids Db model database
class StatusKidsDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rausgehen = db.Column(db.String(10), index=True)
    zahnspange = db.Column(db.String(10), index=True)
    essen = db.Column(db.String(10), index=True)
    runterkommen = db.Column(db.String(10), index=True)
    spuelmaschiene = db.Column(db.String(10), index=True)
    bett = db.Column(db.String(10), index=True)
    serie = db.Column(db.String(10), index=True)
    funktion1 = db.Column(db.String(20), index=True)
    funktion2 = db.Column(db.String(20), index=True)
    funktion3 = db.Column(db.String(20), index=True)
    created_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    timer = db.Column(db.String(30), index=True)

    def __repr__(self):
        return '<id: {}, rausgehen: {}, zahnspange: {}, essen: {}, runterkommen: {}, spuelmaschiene: {},bett: {}, ' \
               'serie: {}, funktion1: {}, funktion2: {}, funktion3: {}, created: {}, timer: {},>'.format(
            self.id, self.rausgehen, self.zahnspange, self.essen, self.runterkommen, self.spuelmaschiene, self.bett,
            self.serie, self.funktion1, self.funktion2, self.funktion3, self.created_time, self.timer)


global keywords
keywords = ['rausgehen', 'zahnspange', 'essen', 'runterkommen', 'spülmaschine', 'bett', 'serie', 'funktion1',
            'funktion2', 'funktion3', 'timer']


def update():
    last_row = StatusKidsDB.query.order_by(-StatusKidsDB.id).first()
    dic = last_row.__dict__
    new_row = []
    for i in dic:
        if dic[i] != '0' and i != 'timer':
            timer = dic['timer']
            pattern = '%a, %d %b %Y %H:%M:%S GMT'
            # "Sat, 11 Apr 2020 09:36:30 GMT"
            time_created = dic['created_time']
            time_end = datetime.datetime.utcnow() - datetime.timedelta(seconds=(int(timer) * 60))
            # time_stamp_old = datetime.datetime.strptime(time_created, pattern)
            latest = max((time_end, time_created))
            # is already happened
            if latest == time_end:
                new_row.append(str(i + '-' + str(0)))
    if new_row != []:
        for a in new_row:
            key, value = a.split('-')
            dic[key] = value
        new_line = StatusKidsDB(rausgehen=dic['rausgehen'], zahnspange=dic['zahnspange'], essen=dic['essen'],
                                runterkommen=dic['runterkommen'], spuelmaschiene=dic['spuelmaschiene'],
                                bett=dic['bett'], serie=dic['serie'], funktion1=dic['funktion1'],
                                funktion2=dic['funktion2'], funktion3=dic['funktion3'], timer='0')
        db.session.add(new_line)
        db.session.commit()


def write_value(key, value=1, timer=2):
    last_row = StatusKidsDB.query.order_by(-StatusKidsDB.id).first()
    dic = last_row.__dict__
    dic[key] = value
    new_line = StatusKidsDB(rausgehen=dic['rausgehen'], zahnspange=dic['zahnspange'], essen=dic['essen'],
                            runterkommen=dic['runterkommen'], spuelmaschiene=dic['spuelmaschiene'],
                            bett=dic['bett'], serie=dic['serie'], funktion1=dic['funktion1'],
                            funktion2=dic['funktion2'], funktion3=dic['funktion3'], timer=str(timer))
    db.session.add(new_line)
    db.session.commit()


@app.route('/')
def home():
    main = {
        'title': 'Main-Page',
        'time': str(datetime.datetime.utcnow())
    }
    return render_template("Main_Template.html", main=main)


@app.route('/write/<para>')
def write(para):
    key = para
    v = 1
    write_value(key, v)
    return str('Done-' + key)


@app.route('/api_caller_kids_full', methods=['GET'])
def api_full():
    json_data = {}
    for row in StatusKidsDB.query.all():
        dic = row.__dict__
        formated = row.__dict__
        del formated['_sa_instance_state']
        json_data[dic['id']] = formated

    return jsonify(json_data)


@app.route('/api_caller_kids_last', methods=['GET'])
def api_last():
    update()
    last_row = StatusKidsDB.query.order_by(-StatusKidsDB.id).first()
    dic = last_row.__dict__
    del dic['_sa_instance_state']
    del dic['id']

    return jsonify(dic)


@app.route('/status_caller_kids')
def status_caller_index():
    for row in StatusKidsDB.query.all():
        formated = row.__dict__
        del formated['_sa_instance_state']
        del formated['id']

    return render_template("Status_Caller_Template.html", status=formated)


@app.route('/bot', methods=['POST'])
def bot():
    keyword = 'None'
    incoming_msg = request.values.get('Body', '').lower()
    resp = MessagingResponse()
    msg = resp.message()
    responded = False
    # checking all the keywords
    for i in keywords:
        if i in incoming_msg:
            keyword = i
    if 'donald' in incoming_msg or 'trump' in incoming_msg:
        url = 'https://api.whatdoestrumpthink.com/api/v1/quotes/random'
        response = requests.request("GET", url)
        res = json.loads(response.text)
        msg.body(res['message'])
        responded = True
    if 'joke' in incoming_msg:
        msg_list = incoming_msg.split(':')
        if msg_list[1] == 'any':
            extra = 'any'
        if msg_list[1] == 'dark':
            extra = 'dark'
        if msg_list[1] == 'different':
            extra = 'miscellaneous'
        if msg_list[1] == 'programming':
            extra = 'programming'
        url = 'https://sv443.net/jokeapi/v2/joke/' + extra
        response = requests.request("GET", url)
        res = json.loads(response.text)
        joke = None
        for a in res:
            if a == 'category':
                cat = res[a]
            if a == 'joke':
                joke = res[a]
            if a == 'setup':
                setup = res[a]
            if a == 'delivery':
                delivery = res[a]
        if joke == None:
            msg.body('Setup: ' + str(setup) + ' Delivery: ' + str(delivery))
            responded = True
        else:
            msg.body('Joke: ' + str(joke))
            responded = True
    if 'quote' in incoming_msg:
        # return a quote
        r = requests.get('https://api.quotable.io/random')
        if r.status_code == 200:
            data = r.json()
            quote = f'{data["content"]} ({data["author"]})'
        else:
            quote = 'I could not retrieve a quote at this time, sorry.'
        msg.body(quote)
        responded = True
    if 'number' in incoming_msg:
        list_msg = incoming_msg.split(':')
        url = 'http://numbersapi.com/' + str(list_msg[1])
        response = requests.request("GET", url)
        msg.body(response.text)
        responded = True
    if 'advice' in incoming_msg:
        url = 'https://api.adviceslip.com/advice'
        response = requests.request("GET", url)
        res = json.loads(response.text)
        msg.body(res['slip']["advice"])
        responded = True
    if 'nation' in incoming_msg:
        list_msg = incoming_msg.split(':')
        if list_msg[1] == 'all':
            url = 'https://restcountries.eu/rest/v2/all'
            response = requests.request("GET", url)
            res = json.loads(response.text)
            list_nations = [a['name'] for a in res]
            msg.body(str(list_nations))
            responded = True
        if list_msg[1] == 'name':
            url = 'https://restcountries.eu/rest/v2/name/' + str(list_msg[2]) + '?fullText=true'
            response = requests.request("GET", url)
            res = json.loads(response.text)
            msg.body(res[0])
            responded = True
        if list_msg[1] == 'flag':
            url = 'https://restcountries.eu/rest/v2/name/' + str(list_msg[2]) + '?fullText=true'
            response = requests.request("GET", url)
            res = json.loads(response.text)
            code = res[0]['alpha3Code'].lower()
            link = 'https://restcountries.eu/data/' + str(code) + '.svg'
            msg.body(link)
            responded = True
    if 'date' in incoming_msg:
        list_msg = incoming_msg.split(':')
        url = 'http://numbersapi.com/' + str(list_msg[1]) + '/' + str(list_msg[2]) + '/date'
        response = requests.request("GET", url)
        msg.body(response.text)
        responded = True
    if 'cat' in incoming_msg:
        # return a cat pic
        msg.media('https://cataas.com/cat')
        responded = True
    if 'dog' in incoming_msg:
        url = 'https://dog.ceo/api/breeds/image/random'
        response = requests.request("GET", url)
        res = json.loads(response.text)
        msg.media(res['message'])
        responded = True
    if 'help-fun' in incoming_msg:
        msg.body('Hi,\nIch führe dich nun durch die Funktionen des Bots.\n 1) mit dem Wort Quote kann ein random Zitat '
                 'einer berühmten Person abgerufen werden \n2)/3) mit cat oder dog können Katzten und Hunde Bilder '
                 'empfangen werden\n4) mit trump kann ein random Zitat von Donald Trump empfangen werden\n5) mit advice'
                 'kann ein Lebensratschlag erteilt werden\n 6) mit date:tag des monats:monat nummer kann ein fact zu '
                 'einem Datum gefunden werden Bsp. date:07:07->7.July \n7) mit nation:flag:land kann eine Flagge '
                 'gefunden werden \n8) mit nation:name:land können informationen über ein Land ermittelt werden\n9) mit'
                 ' number:zahl kann ein fact über eine Nummer erscheinen -> number:4\n10) mit joke:any kann irgendein '
                 'Witz gefunden werden\n11) mit joke:Katergorie kann ein Witz der folgenden Katgorien empfangen '
                 'werden: drak, different, any, programming')
        responded = True
    elif 'help-kids' in incoming_msg:
        msg.body(
            'Hi, \nich werde dir helfen einen Überblick über meine Funktionen zu bekommen. Fangen wir an zunächst '
            'einmal ist es wichtig zu wissen welche Schlüsselwörter du hast: \n' + str(
                keywords) + '.\nNachdem das nun geklärt ist '
                            'kommen wir zu persönlichen '
                            'Konfiguration der '
                            'Kids-Caller-Optionen diese '
                            'sind zum einen die '
                            'Dringlichkeit und der Timer. \n'
                            'Sie werden mit -p oder '
                            'priority (Dringlichkeit) oder '
                            '-t oder timer abgekürzt. \nDer '
                            'Wert der jeweiligen '
                            'Konfiguration ist anschließend '
                            'mit einem Doppelpunkt '
                            'anzugeben. \nZwei Parameter '
                            'hintereinader müssen auch von '
                            'einem Doppelpunkt getrennt '
                            'werden. \nBsp. 1) essen -> p=1 '
                            't=1 \n2) rausgehen -p:5 -> t=1 '
                            'p=5 \n3) bett -p:5-t:20 -> p=5 '
                            't=20.')
        responded = True
    elif 'help' in incoming_msg:
        msg.body('Es gibt zwei Optionen Hilfe zu bekommen. \n1) help-kids für die Kids_Caller Funktionen \n2)'
                 'help-fun um mehr über meine coolen APIs zu erfahren.')
        responded = True
    if keyword in incoming_msg:
        check_parameters = incoming_msg
        timer = 1
        value = 1
        kids = 'Kinder'
        if '-n' in incoming_msg or 'niklas' in incoming_msg:
            write_value('funktion3', 1, timer)
            kids = 'Niklas'
        if '-l' in incoming_msg or 'laura' in incoming_msg:
            kids = 'Laura'
            write_value('funktion3', 2, timer)
        if '-t' in incoming_msg or 'timer' in incoming_msg or '-v' in incoming_msg or 'value' in incoming_msg:
            check_parameters = check_parameters.split(':')
            for i in range(0, len(check_parameters)):
                if '-t' in check_parameters[i] or 'timer' in check_parameters[i]:
                    timer = int(check_parameters[i + 1])
                if '-p' in check_parameters[i] or 'priority' in check_parameters[i]:
                    value = int(check_parameters[i + 1])
        write_value(keyword, value, timer)
        msg.body("Wird erledigt," + kids + " wurden gerufen-" + keyword + '  V:  ' + str(value) + '  T:  ' + str(timer))
        responded = True
    if not responded:
        msg.body('Es tut uns leid aber dieser Antrag konnte nicht bearbeitet werden!')
    return str(resp)


if __name__ == '__main__':
    app.jinja_env.auto_reload = True
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.run(debug=True)
