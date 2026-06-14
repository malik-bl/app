from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from flask_cors import CORS
import os
import json
import uuid
import base64
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename

# Load .env file automatically (works on Windows too)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Manually load .env if python-dotenv not installed
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, val = line.partition('=')
                    os.environ.setdefault(key.strip(), val.strip())

from groq_service import GroqService
from cv_analyzer import CVAnalyzer
from body_language import BodyLanguageAnalyzer

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ai-interview-secret-key-2024')
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Simple in-memory user store (replace with DB in production)
users_db = {}
sessions_db = {}

groq_service = GroqService()
cv_analyzer = CVAnalyzer(groq_service)
body_analyzer = BodyLanguageAnalyzer()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─── Auth Routes ─────────────────────────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/api/signup', methods=['POST'])
def signup():
    data = request.get_json()
    name = data.get('name', '').strip()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    if not all([name, email, password]):
        return jsonify({'error': 'All fields required'}), 400
    if email in users_db:
        return jsonify({'error': 'Email already registered'}), 409

    user_id = str(uuid.uuid4())
    users_db[email] = {
        'id': user_id,
        'name': name,
        'email': email,
        'password': password,  # Hash in production!
        'created_at': datetime.now().isoformat(),
        'interviews': []
    }
    session['user_id'] = user_id
    session['user_email'] = email
    session['user_name'] = name
    return jsonify({'success': True, 'name': name})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = users_db.get(email)
    if not user or user['password'] != password:
        return jsonify({'error': 'Invalid credentials'}), 401

    session['user_id'] = user['id']
    session['user_email'] = email
    session['user_name'] = user['name']
    return jsonify({'success': True, 'name': user['name']})

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'success': True})

@app.route('/api/auth/status')
def auth_status():
    if 'user_id' in session:
        return jsonify({'authenticated': True, 'name': session.get('user_name')})
    return jsonify({'authenticated': False})

# ─── Dashboard ────────────────────────────────────────────────────────────────

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('dashboard.html')

@app.route('/interview')
def interview():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('interview.html')

@app.route('/results')
def results():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    return render_template('results.html')

# ─── CV Upload & Analysis ─────────────────────────────────────────────────────

@app.route('/api/upload-cv', methods=['POST'])
def upload_cv():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    if 'cv' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400

    file = request.files['cv']
    field = request.form.get('field', 'Software Engineering')

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Use PDF, DOC, DOCX, or TXT'}), 400

    filename = secure_filename(f"{session['user_id']}_{file.filename}")
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)

    # Extract text from CV
    cv_text = cv_analyzer.extract_text(filepath)
    if not cv_text:
        return jsonify({'error': 'Could not extract text from CV'}), 400

    # Analyze CV with Groq
    analysis = cv_analyzer.analyze(cv_text, field)

    # Store in session
    session['cv_text'] = cv_text
    session['cv_analysis'] = analysis
    session['field'] = field
    session['interview_id'] = str(uuid.uuid4())

    return jsonify({
        'success': True,
        'analysis': analysis,
        'cv_preview': cv_text[:500] + '...' if len(cv_text) > 500 else cv_text
    })

# ─── Question Generation ──────────────────────────────────────────────────────

@app.route('/api/get-questions', methods=['GET'])
def get_questions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    questions = session.get('questions', [])
    field = session.get('field', '')
    return jsonify({'questions': questions, 'field': field})

@app.route('/api/generate-questions', methods=['POST'])
def generate_questions():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    cv_analysis = session.get('cv_analysis', {})
    field = session.get('field', 'Software Engineering')
    cv_text = session.get('cv_text', '')

    questions = groq_service.generate_questions(cv_text, cv_analysis, field)
    session['questions'] = questions
    session['current_question'] = 0
    session['answers'] = []

    return jsonify({'questions': questions})

# ─── Speech Processing ────────────────────────────────────────────────────────

@app.route('/api/process-answer', methods=['POST'])
def process_answer():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()
    transcript = data.get('transcript', '')
    question_index = data.get('question_index', 0)
    body_data = data.get('body_data', {})

    questions = session.get('questions', [])
    if question_index >= len(questions):
        return jsonify({'error': 'Invalid question index'}), 400

    question = questions[question_index]

    # Analyze answer quality
    answer_analysis = groq_service.analyze_answer(
        question=question,
        answer=transcript,
        field=session.get('field', ''),
        cv_analysis=session.get('cv_analysis', {})
    )

    # Analyze body language from frame data
    body_analysis = body_analyzer.analyze(body_data)

    # Store answer
    answers = session.get('answers', [])
    answers.append({
        'question': question,
        'transcript': transcript,
        'answer_analysis': answer_analysis,
        'body_analysis': body_analysis,
        'timestamp': datetime.now().isoformat()
    })
    session['answers'] = answers

    return jsonify({
        'answer_analysis': answer_analysis,
        'body_analysis': body_analysis
    })

# ─── Final Feedback & Courses ─────────────────────────────────────────────────

@app.route('/api/generate-feedback', methods=['POST'])
def generate_feedback():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    answers = session.get('answers', [])
    cv_analysis = session.get('cv_analysis', {})
    field = session.get('field', 'General')
    questions = session.get('questions', [])

    # If user skipped all questions without answering, build placeholder answers
    if not answers and questions:
        answers = [{
            'question': q,
            'transcript': '',
            'answer_analysis': {
                'score': 0, 'clarity': 0, 'relevance': 0, 'confidence': 0,
                'feedback': 'No answer was recorded for this question.',
                'missing_points': q.get('expected_keywords', []),
                'strengths': [], 'improvements': ['Please answer this question in your next attempt.']
            },
            'body_analysis': {},
            'timestamp': datetime.now().isoformat()
        } for q in questions]
        session['answers'] = answers

    # Generate comprehensive feedback
    feedback = groq_service.generate_final_feedback(answers, cv_analysis, field)

    # Generate course recommendations
    courses = groq_service.recommend_courses(feedback, field, cv_analysis)

    # Store results
    result = {
        'interview_id': session.get('interview_id'),
        'field': field,
        'cv_analysis': cv_analysis,
        'answers': answers,
        'feedback': feedback,
        'courses': courses,
        'completed_at': datetime.now().isoformat()
    }

    # Save to user's interview history
    email = session.get('user_email')
    if email and email in users_db:
        users_db[email]['interviews'].append(result)

    session['results'] = result
    return jsonify(result)

@app.route('/api/get-results')
def get_results():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    results = session.get('results', {})
    return jsonify(results)

@app.route('/api/analyze-frame', methods=['POST'])
def analyze_frame():
    """Real-time body language analysis from video frame"""
    data = request.get_json()
    frame_data = data.get('frame_data', {})
    analysis = body_analyzer.analyze(frame_data)
    return jsonify(analysis)

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    # Use 'stat' reloader to avoid watchdog scanning all of site-packages
    app.run(debug=True, port=5000, use_reloader=True, reloader_type='stat')