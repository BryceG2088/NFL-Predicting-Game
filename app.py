from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from flask_wtf.csrf import CSRFProtect
from werkzeug.security import generate_password_hash, check_password_hash
import requests
from dotenv import load_dotenv
import os
import re
import logging
from functools import wraps

load_dotenv()

app = Flask(__name__)
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

# Security configurations
app.config['WTF_CSRF_ENABLED'] = True
app.config['WTF_CSRF_TIME_LIMIT'] = 3600
app.config['SESSION_COOKIE_SECURE'] = True if not app.debug else False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Initialize extensions
mysql = MySQL(app)
csrf = CSRFProtect(app)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Input validation functions
def validate_username(username):
    """Validate username format"""
    if not username or len(username.strip()) < 3 or len(username.strip()) > 50:
        return False, "Username must be between 3 and 50 characters"
    if not re.match(r'^[a-zA-Z0-9_]+$', username.strip()):
        return False, "Username can only contain letters, numbers, and underscores"
    return True, ""

def validate_password(password):
    """Validate password strength"""
    if not password or len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"
    return True, ""

def validate_league_code(code):
    """Validate league code format"""
    if not code or len(code.strip()) < 3 or len(code.strip()) > 20:
        return False, "League code must be between 3 and 20 characters"
    if not re.match(r'^[a-zA-Z0-9]+$', code.strip()):
        return False, "League code can only contain letters and numbers"
    return True, ""

def validate_league_name(name):
    """Validate league name format"""
    if not name or len(name.strip()) < 2 or len(name.strip()) > 100:
        return False, "League name must be between 2 and 100 characters"
    return True, ""

def validate_score(score):
    """Validate score input"""
    try:
        score_int = int(score)
        if score_int < 0 or score_int > 999:
            return False, "Score must be between 0 and 999"
        return True, ""
    except (ValueError, TypeError):
        return False, "Score must be a valid number"

# Login required decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('brycegayan_username'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('enterLogin'))
        return f(*args, **kwargs)
    return decorated_function

# Error handling decorator
def handle_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {f.__name__}: {str(e)}")
            flash('An error occurred. Please try again.', 'error')
            return redirect(url_for('index'))
    return decorated_function

@app.route('/test_db')
def test_db():
    try:
        cur = mysql.connection.cursor()
        cur.execute('SHOW TABLES;')
        tables = cur.fetchall()
        cur.close()
        return f"Tables: {tables}"
    except Exception as e:
        logger.error(f"Database test failed: {str(e)}")
        return "Database connection failed", 500

@app.route('/')
@handle_errors
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
    session.clear()
    flash('You have been logged out successfully', 'success')
    return redirect(url_for('enterLogin'))

# Check if username and password are valid. If valid, log user in with their new credentials.


@app.route('/sign-up-verification', methods=['POST'])
@handle_errors
def signupVerification():
    user = request.values.get('username')
    pwd = request.values.get('password')
    
    # Input validation
    username_valid, username_error = validate_username(user)
    if not username_valid:
        flash(username_error, 'error')
        return redirect(url_for('signup'))
    
    password_valid, password_error = validate_password(pwd)
    if not password_valid:
        flash(password_error, 'error')
        return redirect(url_for('signup'))

    cursor = mysql.connection.cursor()

    data = select(
        cursor, "SELECT * FROM brycegayan_users WHERE username=%s", (user.strip(),))
    if len(data) > 0:  # if this username already exists
        flash('Username already taken', 'error')
        return redirect(url_for('signup'))

    insert(cursor, "INSERT INTO brycegayan_users(username, password) VALUES (%s, %s)",
           (user.strip(), generate_password_hash(pwd)))
    flash('Account created successfully!', 'success')
    return login(user.strip())


@app.route('/log-in-verification', methods=['POST'])
@handle_errors
def loginVerification():
    user = request.values.get('username')
    pwd = request.values.get('password')

    if not user or not pwd:
        flash('Please enter both username and password', 'error')
        return redirect(url_for('enterLogin'))

    cursor = mysql.connection.cursor()
    data = select(
        cursor, "SELECT password FROM brycegayan_users WHERE username=%s", (user.strip(),))
    if len(data) == 0:  # if there are no matching usernames
        flash('Invalid username or password', 'error')
        return redirect(url_for('enterLogin'))

    # if passwords don't match
    if not check_password_hash(data[0]['password'], pwd):
        flash('Invalid username or password', 'error')
        return redirect(url_for('enterLogin'))

    flash('Login successful!', 'success')
    return login(user.strip())


@app.route('/create-league')
@login_required
@handle_errors
def createLeague():
    name = request.values.get('name')
    code = request.values.get('code')
    
    # Input validation
    name_valid, name_error = validate_league_name(name)
    if not name_valid:
        flash(name_error, 'error')
        return redirect(url_for('index'))
    
    code_valid, code_error = validate_league_code(code)
    if not code_valid:
        flash(code_error, 'error')
        return redirect(url_for('index'))

    # check that code is unique
    cursor = mysql.connection.cursor()
    data = select(
        cursor, "SELECT * FROM brycegayan_leagues WHERE join_code=%s", (code.strip().upper(),))
    if len(data) > 0:
        flash('League code already taken', 'error')
        return redirect(url_for('index'))

    # insert league into leagues
    insert(cursor, "INSERT INTO brycegayan_leagues(name, join_code) VALUES (%s,%s)", (name.strip(), code.strip().upper()))
    flash('League created successfully!', 'success')
    # add user to league
    return redirect(url_for('joinLeague') + '?leagueCode=' + code.strip().upper())


@app.route('/join-league')
@login_required
@handle_errors
def joinLeague():
    leagueCode = request.values.get('leagueCode')
    
    if not leagueCode:
        flash('Please enter a league code', 'error')
        return redirect(url_for('index'))

    # checks if there is a league with this code
    cursor = mysql.connection.cursor()
    data = select(
        cursor, "SELECT * FROM brycegayan_leagues WHERE join_code=%s", (leagueCode.strip().upper(),))
    if len(data) == 0:
        flash('No league found with this code', 'error')
        return redirect(url_for('index'))

    # checks if user is already in league
    # data[0]['id'] is the league_id from above
    results = select(
        cursor, "SELECT * FROM brycegayan_users_leagues WHERE user_id=%s AND league_id=%s", (getUserID(), data[0]['id']))
    if len(results) > 0:
        flash('You are already in this league', 'error')
        return redirect(url_for('index'))

    # inserts relationship into users_leagues
    insert(cursor, "INSERT INTO brycegayan_users_leagues(user_id, league_id) VALUES (%s,%s)",
           (getUserID(), data[0]['id']))

    flash('Successfully joined the league!', 'success')
    # redirects back to homepage
    return redirect(url_for('league') + '?id=' + str(data[0]['id']))


@app.route('/predict')
@login_required
@handle_errors
def makePredictions():
    error = getErrorMessage(request.values.get('error'))
    # Checks that there is a user logged in
    if not session.get('brycegayan_username'):
        return redirect(url_for('enterLogin'))

    data = loadData()
    if weekStarted(data):
        flash('You may no longer make predictions for this week', 'error')
        return redirect(url_for('index'))

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
@login_required
@handle_errors
def enterPredictions():
    data = loadData()
    if weekStarted(data):
        flash('You may no longer make predictions for this week', 'error')
        return redirect(url_for('index'))

    teams = getMatchups(data)
    predictions = [['' for i in range(2)] for j in range(len(teams))]
    submit = request.values.get('submit')
    cursor = mysql.connection.cursor()

    # Check if trying to submit over previous submission
    if submit:
        results = select(
            cursor, 'SELECT * FROM brycegayan_predictions WHERE user_id=%s AND week=%s', (getUserID(), getWeek(data)))
        if len(results) > 0:
            flash('You have already submitted predictions for this week', 'error')
            return redirect(url_for('index'))

    # Add predictions to list and validate
    for i in range(len(teams)):
        predictions[i][0] = request.values.get(teams[i][0])
        predictions[i][1] = request.values.get(teams[i][1])
        
        # Validate scores
        score1_valid, score1_error = validate_score(predictions[i][0])
        score2_valid, score2_error = validate_score(predictions[i][1])
        
        if not score1_valid or not score2_valid:
            flash('Please enter valid scores (0-999) for all games', 'error')
            return redirect(url_for('makePredictions'))
        
        # enter to database
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

    if submit:
        for i in range(len(teams)):
            # insert prediction
            query = "INSERT INTO brycegayan_predictions(user_ID, team1, score1, team2, score2, week) VALUES (%s,%s,%s,%s,%s,%s)"
            queryVars = (getUserID(), teams[i][0], predictions[i]
                         [0], teams[i][1], predictions[i][1], getWeek(data))
            insert(cursor, query, queryVars)
        flash('Predictions submitted successfully!', 'success')

    return redirect(url_for('index'))


@app.route('/league')
@login_required
@handle_errors
def league():
    # Checks that there is a user logged in
    if not session.get('brycegayan_username'):
        return redirect(url_for('enterLogin'))

    id = request.values.get('id')
    if not id or not id.isdigit():
        flash('Invalid league ID', 'error')
        return redirect(url_for('index'))
    
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
    try:
        cursor.execute(query, queryVars)
        mysql.connection.commit()
        return cursor.fetchall()
    except Exception as e:
        logger.error(f"Database select error: {str(e)}")
        mysql.connection.rollback()
        raise


def insert(cursor, query, queryVars):
    try:
        cursor.execute(query, queryVars)
        mysql.connection.commit()
    except Exception as e:
        logger.error(f"Database insert error: {str(e)}")
        mysql.connection.rollback()
        raise


def loadData():
    try:
        response = requests.get(
            'https://site.web.api.espn.com/apis/v2/scoreboard/header?sport=football&league=nfl', timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"ESPN API error: {str(e)}")
        raise


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
    session.permanent = True
    return redirect(url_for('index'))


def scorePredictions():
    try:
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
    except Exception as e:
        logger.error(f"Error in scorePredictions: {str(e)}")


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
    return ''


if __name__ == '__main__':
    # Production-ready configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    host = '127.0.0.1' if not debug_mode else '0.0.0.0'
    port = int(os.getenv('PORT', 5000))
    
    app.run(debug=debug_mode, host=host, port=port)
