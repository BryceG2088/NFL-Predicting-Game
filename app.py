from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
mysql = MySQL(app)


@app.route('/')
def index():
    error = getErrorMessage(request.values.get('error'))
    scorePredictions()
    if not session.get('brycegayan_username'):
        return redirect(url_for('enterLogin'))

    cursor = mysql.connection.cursor()
    data = loadData()
    id = getUserID()
    # get number of predictions made or if submitted
    submittedPredictions = select(
        cursor, 'SELECT * FROM brycegayan_predictions WHERE user_id=%s AND week=%s', (id, getWeek(data)))
    if len(submittedPredictions) > 0:
        status = 'Predictions Submitted'
    else:
        savedPredictions = select(
            cursor, 'SELECT * FROM brycegayan_savedpredictions WHERE user_id=%s AND week=%s', (id, getWeek(data)))
        status = str(len(savedPredictions)) + '/' + \
            str(len(data['sports'][0]['leagues'][0]['events']))

    # get leagues, places in leagues
    leagues = getLeagues()
    # leagueNames = [None]*len(leagues)
    places = [None] * len(leagues)
    for i in range(len(leagues)):
        places[i] = getPlace(cursor, id, leagues[i]['league_id'])

    return render_template('index.html.j2', status=status, leagues=getLeagues(), places=places, active={'home': ' active', 'predict': ''}, current={'home': 'aria-current="page"', 'predict': ''}, error=error)


@app.route('/log-in')
def enterLogin():
    error = getErrorMessage(request.values.get('error'))
    return render_template('login.html.j2',  active={'home': '', 'predict': ''}, current={'home': '', 'predict': ''}, error=error)


@app.route('/sign-up')
def signup():
    error = getErrorMessage(request.values.get('error'))
    return render_template('signup.html.j2',  active={'home': '', 'predict': ''}, current={'home': '', 'predict': ''}, error=error)


@app.route('/log-out')
def logout():
    session.pop('brycegayan_username', None)
    return redirect(url_for('enterLogin'))

# Check if username and password are valid. If valid, log user in with their new credentials.


@app.route('/sign-up-verification', methods=['POST'])
def signupVerification():
    user = request.values.get('username')
    pwd = request.values.get('password')
    if user.strip() == "" or pwd.strip() == "":
        return redirect(url_for('signup') + "?error=invalidSignup")

    cursor = mysql.connection.cursor()

    data = select(
        cursor, "SELECT * FROM brycegayan_users WHERE username=%s", (user,))
    if len(data) > 0:  # if this username already exists
        return redirect(url_for('signup') + "?error=usernameTaken")

    insert(cursor, "INSERT INTO brycegayan_users(username, password) VALUES (%s, %s)",
           (user, generate_password_hash(pwd)))
    return login(user)


@app.route('/log-in-verification', methods=['POST'])
def loginVerification():
    user = request.values.get('username')
    pwd = request.values.get('password')

    cursor = mysql.connection.cursor()
    data = select(
        cursor, "SELECT password FROM brycegayan_users WHERE username=%s", (user,))
    if len(data) == 0:  # if there are no matching usernames
        return redirect(url_for('enterLogin') + "?error=invalidLogin")

    # if passwords don't match
    if not check_password_hash(data[0]['password'], pwd):
        return redirect(url_for('enterLogin') + "?error=invalidLogin")

    return login(user)


@app.route('/create-league')
def createLeague():
    name = request.values.get('name')
    code = request.values.get('code')
    if name.strip() == "" or code.strip() == "":
        return redirect(url_for('index') + "?error=invalidLeague")

    # check that code is unique
    cursor = mysql.connection.cursor()
    data = select(
        cursor, "SELECT * FROM brycegayan_leagues WHERE join_code=%s", (code,))
    if len(data) > 0:
        return redirect(url_for('index') + '?error=leagueCodeTaken')

    # insert league into leagues
    insert(cursor, "INSERT INTO brycegayan_leagues(name, join_code) VALUES (%s,%s)", (name, code))
    # add user to league
    return redirect(url_for('joinLeague') + '?leagueCode=' + code)


@app.route('/join-league')
def joinLeague():
    leagueCode = request.values.get('leagueCode')

    # checks if there is a league with this code
    cursor = mysql.connection.cursor()
    data = select(
        cursor, "SELECT * FROM brycegayan_leagues WHERE join_code=%s", (leagueCode,))
    if len(data) == 0:
        return redirect(url_for('index') + '?error=leagueCodeNotFound')

    # checks if user is already in league
    # data[0]['id'] is the league_id from above
    results = select(
        cursor, "SELECT * FROM brycegayan_users_leagues WHERE user_id=%s AND league_id=%s", (getUserID(), data[0]['id']))
    if len(results) > 0:
        return redirect(url_for('index') + '?error=alreadyInLeague')

    # inserts relationship into users_leagues
    insert(cursor, "INSERT INTO brycegayan_users_leagues(user_id, league_id) VALUES (%s,%s)",
           (getUserID(), data[0]['id']))

    # redirects back to homepage
    return redirect(url_for('league') + '?id=' + str(data[0]['id']))


@app.route('/predict')
def makePredictions():
    error = getErrorMessage(request.values.get('error'))
    # Checks that there is a user logged in
    if not session.get('brycegayan_username'):
        return redirect(url_for('enterLogin'))

    data = loadData()
    if weekStarted(data):
        return redirect(url_for('index') + '?error=weekStarted')

    query = 'SELECT team1, score1, team2, score2 FROM brycegayan_savedpredictions WHERE user_id=%s'
    predictions = select(mysql.connection.cursor(), query, (getUserID(),))
    matchups = getMatchups(data)
    indexedPredictions = [['' for i in range(4)] for j in range(len(matchups))]
    # This part is necessary for autocompleting saved predictions in the form
    for prediction in predictions:
        if [prediction['team1'], prediction['team2']] in matchups:
            indexedPredictions[matchups.index(
                [prediction['team1'], prediction['team2']])] = list(prediction.values())

    return render_template('predictions.html.j2', matchups=getMatchups(loadData()), savedPredictions=indexedPredictions, leagues=getLeagues(), active={'home': '', 'predict': ' active'}, current={'home': '', 'predict': 'aria-current="page"'}, error=error)


@app.route('/enter-predictions')
def enterPredictions():
    data = loadData()
    if weekStarted(data):
        return redirect(url_for('index') + '?weekStarted=true')

    teams = getMatchups(data)
    predictions = [['' for i in range(2)] for j in range(len(teams))]
    submit = request.values.get('submit')
    cursor = mysql.connection.cursor()

    # Check if trying to submit over previous submission
    if submit:
        results = select(
            cursor, 'SELECT * FROM brycegayan_predictions WHERE user_id=%s AND week=%s', (getUserID(), getWeek(data)))
        if len(results) > 0:
            return redirect(url_for('index') + '?alreadySubmitted=true')

    # Add predictions to list
    for i in range(len(teams)):
        predictions[i][0] = request.values.get(teams[i][0])
        predictions[i][1] = request.values.get(teams[i][1])
        # enter to database
        # input checking
        if predictions[i][0].isdecimal() and predictions[i][1].isdecimal():
            if not submit:  # save
                # remove any prior saved predictions for this game
                query = 'DELETE FROM brycegayan_savedpredictions WHERE user_id=%s AND team1=%s AND week=%s'
                cursor.execute(
                    query, (getUserID(), teams[i][0], getWeek(data)))
                mysql.connection.commit()
                # insert prediction
                query = "INSERT INTO brycegayan_savedpredictions(user_ID, team1, score1, team2, score2, week) VALUES (%s,%s,%s,%s,%s,%s)"
                queryVars = (getUserID(
                ), teams[i][0], predictions[i][0], teams[i][1], predictions[i][1], getWeek(data))
                insert(cursor, query, queryVars)
        elif submit:  # invalid input, go back and try again
            return redirect(url_for('makePredictions') + '?error=invalidPredictions')

    if submit:
        for i in range(len(teams)):
            # insert prediction
            query = "INSERT INTO brycegayan_predictions(user_ID, team1, score1, team2, score2, week) VALUES (%s,%s,%s,%s,%s,%s)"
            queryVars = (getUserID(), teams[i][0], predictions[i]
                         [0], teams[i][1], predictions[i][1], getWeek(data))
            insert(cursor, query, queryVars)

    return redirect(url_for('index'))


@app.route('/league')
def league():
    # Checks that there is a user logged in
    if not session.get('brycegayan_username'):
        return redirect(url_for('enterLogin'))

    id = request.values.get('id')
    cursor = mysql.connection.cursor()
    data = loadData()
    info = None
    members = None
    numMatchups = None
    nameQuery = "SELECT name FROM brycegayan_leagues WHERE id=%s"

    # get info for table if week has already started (don't want users to be able to see each other's predictions until week starts for competitive integrity)
    if weekStarted(data):
        infoQuery = "SELECT u.username, p.team1, p.score1, p.team2, p.score2, u.score FROM brycegayan_users u JOIN brycegayan_predictions p JOIN brycegayan_users_leagues r ON r.league_id=%s AND u.id=r.user_id AND u.id=p.user_id AND p.week=%s ORDER BY u.username"
        memberQuery = "SELECT u.username FROM brycegayan_users u JOIN brycegayan_users_leagues r ON r.league_id=%s AND u.id=r.user_id ORDER BY u.username;"
        info = select(cursor,  infoQuery, (id, getWeek(data)))
        members = select(cursor, memberQuery, (id,))
        numMatchups = int(len(getMatchups(data)))

    # get standings
    standings = getStandings(cursor, id)

    return render_template('league.html.j2', name=select(cursor, nameQuery, (id,))[0]['name'], info=info, members=members, numMatchups=numMatchups, standings=standings, leagues=getLeagues(), active={'home': '', 'predict': ''}, current={'home': '', 'predict': ''})


def select(cursor, query, queryVars):
    cursor.execute(query, queryVars)
    mysql.connection.commit()
    return cursor.fetchall()


def insert(cursor, query, queryVars):
    cursor.execute(query, queryVars)
    mysql.connection.commit()


def loadData():
    response = requests.get(
        'https://site.web.api.espn.com/apis/v2/scoreboard/header?sport=football&league=nfl')
    return response.json()


def getMatchups(data):
    # set up a numGamesx2 array (from Geeks4Geeks)
    matchups = [['' for i in range(2)] for j in range(
        len(data['sports'][0]['leagues'][0]['events']))]
    for i in range(len(data['sports'][0]['leagues'][0]['events'])):
        matchups[i][0] = data['sports'][0]['leagues'][0]['events'][i]['competitors'][0]['abbreviation']
        matchups[i][1] = data['sports'][0]['leagues'][0]['events'][i]['competitors'][1]['abbreviation']
    return matchups


def getScores(data):
    # set up a numGamesx2 array (from Geeks4Geeks)
    scores = [['' for i in range(2)] for j in range(
        len(data['sports'][0]['leagues'][0]['events']))]
    for i in range(len(data['sports'][0]['leagues'][0]['events'])):
        scores[i][0] = int(data['sports'][0]['leagues'][0]
                           ['events'][i]['competitors'][0]['score'])
        scores[i][1] = int(data['sports'][0]['leagues'][0]
                           ['events'][i]['competitors'][1]['score'])
    return scores


def getWeek(data):
    return data['sports'][0]['leagues'][0]['events'][0]['week']


def getUserID():
    return select(mysql.connection.cursor(), 'SELECT id FROM brycegayan_users WHERE username=%s', (session['brycegayan_username'],))[0]['id']


def login(user):
    session['brycegayan_username'] = user
    return redirect(url_for('index'))


def scorePredictions():
    data = loadData()
    cursor = mysql.connection.cursor()
    weekUpdated = select(
        cursor, "SELECT * FROM brycegayan_info", ())[0]['recentWeek']

    # conditions for scoring a week's predictions
    if weekUpdated != getWeek(data) and weekFinished(data):
        users = select(cursor, "SELECT * from brycegayan_users", ())
        scores = getScores(data)
        for user in users:  # scoring each user in each league.
            weekScore = 0
            predictions = select(
                cursor, 'SELECT * FROM brycegayan_predictions WHERE user_id = %s AND week = %s ORDER BY id', (user['id'], getWeek(data)))
            if len(predictions) > 0:  # ensuring the user submitted predictions for this week
                for i in range(len(scores)):  # Scoring each prediction for the user
                    # WINNER SCORING
                    # if user correctly predicted winner or tie
                    if (scores[i][0] > scores[i][1] and int(predictions[i]['score1']) > int(predictions[i]['score2'])) or (scores[i][0] < scores[i][1] and int(predictions[i]['score1']) < int(predictions[i]['score2'])) or (scores[i][0] == scores[i][1] and int(predictions[i]['score1']) == int(predictions[i]['score2'])):
                        weekScore += 10
                    # if game tied and user didn't predict a tie
                    elif scores[i][0] == scores[i][1]:
                        weekScore += 5
                    # else user incorrectly predicted winner and they get 0 points

                    # SPREAD SCORING
                    actual = abs(scores[i][0] - scores[i][1])
                    predicted = abs(
                        int(predictions[i]['score1']) - int(predictions[i]['score2']))
                    difference = abs(actual - predicted)
                    if (difference < 10):
                        weekScore += (10 - difference)
                    # else user gets 0 points for spread because their prediction wasn't very good

                    # POINTS SCORING
                    actual = scores[i][0] + scores[i][1]
                    predicted = int(
                        predictions[i]['score1']) + int(predictions[i]['score2'])
                    difference = abs(actual - predicted)
                    if (difference < 16):
                        weekScore += 8 - 0.5*difference
                    # else user gets 0 points for points because their prediction wasn't very good

                    # PERFECT GAME
                    if scores[i][0] == int(predictions[i]['score1']) and scores[i][1] == int(predictions[i]['score2']):
                        weekScore += 50

            # add weekscore to the score for each of the user's leagues
            query = 'UPDATE brycegayan_users_leagues SET score = score + %s WHERE user_id = %s'
            cursor.execute(query, (weekScore, user['id']))
            mysql.connection.commit()

        # update weekUpdated so that website knows not to score predictions again for this week
        query = 'UPDATE brycegayan_info SET recentWeek = %s WHERE 1'
        cursor.execute(query, (str(getWeek(data)),))
        mysql.connection.commit()
        # clears unneccessary memory from database
        cursor.execute('DELETE FROM brycegayan_savedpredictions WHERE 1')


def weekFinished(data):  # true if every game is completed
    for event in data['sports'][0]['leagues'][0]['events']:
        if not event['fullStatus']['type']['completed']:
            return False
    return True


def weekStarted(data):  # true if a game has begun
    for event in data['sports'][0]['leagues'][0]['events']:
        if event['status'] != "pre":
            return True
    return False


def getLeagues():
    query = 'SELECT ul.league_id, l.name FROM brycegayan_users_leagues ul JOIN brycegayan_leagues l ON ul.league_id=l.id WHERE ul.user_id=%s'
    return select(mysql.connection.cursor(), query, (getUserID(),))


def getStandings(cursor, leagueID):
    unorderedStandings = select(
        cursor, 'SELECT user_id, score FROM brycegayan_users_leagues WHERE league_id=%s', (leagueID,))
    standingsList = [[None for i in range(3)] for j in range(
        len(unorderedStandings))]
    for i in range(len(standingsList)):
        standingsList[i][0] = int(unorderedStandings[i]['score'])
        standingsList[i][1] = int(unorderedStandings[i]['user_id'])
        standingsList[i][2] = select(
            cursor, 'SELECT username FROM brycegayan_users WHERE id=%s', (unorderedStandings[i]['user_id'],))[0]['username']
    return sorted(standingsList, reverse=True)


def getPlace(cursor, userID, leagueID):
    standingsList = getStandings(cursor, leagueID)

    for place in standingsList:
        if place[1] == userID:
            return standingsList.index(place) + 1


def getErrorMessage(error):
    if error == 'invalidSignup':
        return 'Empty input: please enter a valid username and password'
    if error == 'usernameTaken':
        return 'Username taken, please choose a different username'
    if error == 'invalidLogin':
        return 'Incorrect username or password'
    if error == 'leagueCodeTaken':
        return 'League code taken, please choose a different league code'
    if error == 'invalidLeague':
        return 'Please enter a valid name and code to create a new league'
    if error == 'leagueCodeNotFound':
        return 'No league found with this code'
    if error == 'alreadyInLeague':
        return 'You are already in this league'
    if error == 'weekStarted':
        return 'You may no longer make predictions for this week'
    if error == 'invalidPredictions':
        return 'Please enter positive integers for scores'
