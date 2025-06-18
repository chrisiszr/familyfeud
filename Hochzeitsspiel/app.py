from flask import Flask, render_template, redirect, session, url_for, request
import json
import os
from flask import jsonify


app = Flask(__name__)
app.secret_key = 'ein-geheimes-schluesselchen'

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_PATH = os.path.join(BASE_DIR, 'questions.json')

with open(QUESTIONS_PATH, 'r', encoding='utf-8') as f:
    questions = json.load(f)

def init_session():
    """
    Initialisiert alle Session-Variablen, falls sie noch nicht existieren.
    """
    if 'current_index' not in session:
        session['current_index'] = 0

    if 'revealed_flags' not in session:
        idx = session['current_index']
        session['revealed_flags'] = [False] * len(questions[idx]['answers'])

    if 'neutral_points' not in session:
        session['neutral_points'] = 0

    if 'score_team_a' not in session:
        session['score_team_a'] = 0
    if 'score_team_b' not in session:
        session['score_team_b'] = 0

    # Neuer Fehler-Counter für Team A und Team B (0 bis 3)
    if 'error_count_a' not in session:
        session['error_count_a'] = 0
    if 'error_count_b' not in session:
        session['error_count_b'] = 0


@app.route('/')
def index():
    init_session()
    idx = session['current_index']
    question_obj = questions[idx]
    return render_template(
        'index.html',
        question_text=question_obj['text'],
        answers=question_obj['answers'],
        revealed_flags=session['revealed_flags'],
        neutral_points=session['neutral_points'],
        score_team_a=session['score_team_a'],
        score_team_b=session['score_team_b'],
        error_count_a=session['error_count_a'],
        error_count_b=session['error_count_b']
    )

@app.route('/reveal', methods=['POST'])
def reveal():
    init_session()
    idx = session['current_index']
    flags = session['revealed_flags']
    answer_list = questions[idx]['answers']

    try:
        i = int(request.form.get('index', -1))
    except (ValueError, TypeError):
        return redirect(url_for('index'))

    if 0 <= i < len(flags) and not flags[i]:
        flags[i] = True
        session['revealed_flags'] = flags
        points = answer_list[i]['points']
        session['neutral_points'] += points

    return redirect(url_for('index'))

# --- Fehler Counter Team A ---
@app.route('/add_error_a', methods=['POST'])
def add_error_a():
    """
    Fügt bei Team A einen Fehler hinzu (bis max. 3).
    """
    init_session()
    if session['error_count_a'] < 3:
        session['error_count_a'] += 1
    return redirect(url_for('index'))

@app.route('/reset_error_a', methods=['POST'])
def reset_error_a():
    """
    Setzt den Fehler-Counter für Team A auf 0.
    """
    init_session()
    session['error_count_a'] = 0
    return redirect(url_for('index'))

# --- Fehler Counter Team B ---
@app.route('/add_error_b', methods=['POST'])
def add_error_b():
    """
    Fügt bei Team B einen Fehler hinzu (bis max. 3).
    """
    init_session()
    if session['error_count_b'] < 3:
        session['error_count_b'] += 1
    return redirect(url_for('index'))

@app.route('/reset_error_b', methods=['POST'])
def reset_error_b():
    """
    Setzt den Fehler-Counter für Team B auf 0.
    """
    init_session()
    session['error_count_b'] = 0
    return redirect(url_for('index'))

@app.route('/assign_a', methods=['POST'])
def assign_a():
    init_session()
    session['score_team_a'] += session['neutral_points']
    session['neutral_points'] = 0
    return redirect(url_for('index'))

@app.route('/assign_b', methods=['POST'])
def assign_b():
    init_session()
    session['score_team_b'] += session['neutral_points']
    session['neutral_points'] = 0
    return redirect(url_for('index'))

@app.route('/next_question', methods=['POST'])
def next_question():
    init_session()
    # Nächste Frage laden
    session['current_index'] = (session['current_index'] + 1) % len(questions)
    idx = session['current_index']
    # Alle Antworten wieder verdeckt
    session['revealed_flags'] = [False] * len(questions[idx]['answers'])
    # Neutraler Zähler zurücksetzen
    session['neutral_points'] = 0
    # Fehler-Counter für beide Teams zurücksetzen
    session['error_count_a'] = 0
    session['error_count_b'] = 0
    return redirect(url_for('index'))


@app.route('/adjust_score', methods=['POST'])
def adjust_score():
    init_session()
    team = request.form.get('team')
    try:
        delta = int(request.form.get('delta', '0'))
    except ValueError:
        delta = 0

    if team == 'A':
        session['score_team_a'] += delta
        if session['score_team_a'] < 0:
            session['score_team_a'] = 0
    elif team == 'B':
        session['score_team_b'] += delta
        if session['score_team_b'] < 0:
            session['score_team_b'] = 0

    return redirect(url_for('index'))

@app.route('/reset_score', methods=['POST'])
def reset_score():
    init_session()
    team = request.form.get('team')
    if team == 'A':
        session['score_team_a'] = 0
    elif team == 'B':
        session['score_team_b'] = 0
    return redirect(url_for('index'))

@app.route('/reset_all', methods=['POST'])
def reset_all():
    session.clear()
    return redirect(url_for('index'))

@app.route('/spectator_state')
def spectator_state():
    init_session()
    idx = session['current_index']

    # Aktueller Fragentext
    question_text = questions[idx]['text']

    # Komplette Liste aller Antworten mit Flag "revealed"
    full_answers = []
    for answer_obj, flag in zip(questions[idx]['answers'], session['revealed_flags']):
        full_answers.append({
            'text': answer_obj['text'],
            'points': answer_obj['points'],
            'revealed': flag
        })

    # Scores, neutraler Zähler und neu: Fehler‐Zähler A/B
    data = {
        'question_text': question_text,
        'answers': full_answers,
        'score_a': session['score_team_a'],
        'score_b': session['score_team_b'],
        'neutral_points': session['neutral_points'],
        'error_count_a': session['error_count_a'],
        'error_count_b': session['error_count_b']
    }
    return jsonify(data)

@app.route('/spectator')
def spectator_view():
    init_session()  # Damit die Session-Variablen sicher existieren
    return render_template('spectator.html')


if __name__ == '__main__':
    app.run(host='::', port=5000, debug=True)
