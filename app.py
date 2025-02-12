from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from ip_geolocation import get_ip_geolocation, format_geolocation_data

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key')
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                             'favicon.ico', mimetype='image/vnd.microsoft.icon')

def query_db(query, args=(), one=False, commit=True):
    conn = sqlite3.connect('judges.db')
    cur = conn.cursor()
    cur.execute(query, args)
    if commit:
        conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def log_admin_action(action, details=None):
    admin_username = session.get('username', 'unknown')
    ip_address = request.remote_addr
    query_db('''
        INSERT INTO admin_logs (admin_username, action, details, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (admin_username, action, details, ip_address))

def is_ip_whitelisted(ip_address):
    result = query_db('''
        SELECT * FROM ip_whitelist 
        WHERE ip_address = ? AND expiry > ?
    ''', (ip_address, datetime.now().isoformat()), one=True)
    return bool(result)

def add_ip_to_whitelist(ip_address, reason, hours=24):
    expiry = (datetime.now() + timedelta(hours=hours)).isoformat()
    query_db('''
        INSERT OR REPLACE INTO ip_whitelist (ip_address, reason, expiry)
        VALUES (?, ?, ?)
    ''', (ip_address, reason, expiry))

def check_rate_limit(ip_address):
    # Always allow localhost for testing
    if ip_address == '127.0.0.1' or is_ip_whitelisted(ip_address):
        return True
    
    # Check submissions in last 10 minutes
    ten_mins_ago = (datetime.now() - timedelta(minutes=10)).isoformat()
    recent_submissions = query_db('''
        SELECT COUNT(*) FROM submissions 
        WHERE ip_address = ? AND submitted_at > ?
    ''', (ip_address, ten_mins_ago), one=True)[0]
    
    return recent_submissions == 0

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/judges')
def get_judges():
    # Get judges with vote counts
    judges = query_db('''
        SELECT j.*,
            COALESCE(SUM(CASE WHEN v.vote_type = 'corrupt' THEN 1 ELSE 0 END), 0) AS corrupt_votes,
            COALESCE(SUM(CASE WHEN v.vote_type = 'not_corrupt' THEN 1 ELSE 0 END), 0) AS not_corrupt_votes
        FROM judges j
        LEFT JOIN votes v ON j.id = v.judge_id
        WHERE j.displayed = 1
        GROUP BY j.id
    ''')
    
    # Determine status based on vote ratios
    judges_with_status = []
    for judge in judges:
        total_votes = judge[-2] + judge[-1]
        status = 'undecided'
        if total_votes >= 5:
            ratio = judge[-2] / total_votes
            if ratio >= 0.6:
                status = 'corrupt'
            elif ratio <= 0.4:
                status = 'not_corrupt'
        
        judges_with_status.append({
            **dict(zip(['id', 'name', 'job_position', 'ruling', 'link', 'x_link', 'displayed'], judge[:-2])),
            'corrupt_votes': judge[-2],
            'not_corrupt_votes': judge[-1],
            'status': status
        })
    
    return jsonify({'judges': judges_with_status})

@app.route('/vote/<int:judge_id>', methods=['POST'])
def submit_vote(judge_id):
    ip_address = request.remote_addr
    data = request.json
    
    # Check if judge exists
    judge = query_db('SELECT * FROM judges WHERE id = ? AND displayed = 1', (judge_id,), one=True)
    if not judge:
        return jsonify({'success': False, 'error': 'Judge not found'}), 404
    
    # Check rate limit (1 vote per judge per day)
    last_vote = query_db('''
        SELECT created_at FROM votes
        WHERE ip_address = ? AND judge_id = ?
        ORDER BY created_at DESC
        LIMIT 1
    ''', (ip_address, judge_id), one=True)
    
    if last_vote and (datetime.now() - datetime.fromisoformat(last_vote[0])) < timedelta(days=1):
        return jsonify({
            'success': False,
            'error': 'You can only vote once per judge every 24 hours'
        }), 429
    
    # Validate vote type
    vote_type = data.get('vote_type')
    if vote_type not in ['corrupt', 'not_corrupt']:
        return jsonify({'success': False, 'error': 'Invalid vote type'}), 400
    
    # Insert vote
    try:
        query_db('''
            INSERT INTO votes (judge_id, ip_address, vote_type, browser_fingerprint)
            VALUES (?, ?, ?, ?)
        ''', (judge_id, ip_address, vote_type, data.get('fingerprint', '')))
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            # Whitelist admin IP
            add_ip_to_whitelist(request.remote_addr, 'admin login')
            log_admin_action('login')
            return redirect(url_for('admin'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/submit-judge', methods=['POST'])
def submit_judge():
    ip_address = request.remote_addr
    
    if not check_rate_limit(ip_address):
        return jsonify({
            'success': False, 
            'error': 'Rate limit exceeded. Please wait 10 minutes between submissions.'
        })

    data = request.json
    try:
        # Cache IP geolocation data immediately
        get_ip_geolocation(ip_address)
        
        query_db('''
            INSERT INTO submissions (name, position, ruling, link, x_link, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['position'],
              data['ruling'], data['link'], data['x_link'], ip_address))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/admin')
@admin_required
def admin():
    judges = query_db('SELECT * FROM judges')
    
    # Get submission stats
    stats = query_db('''
        SELECT 
            status,
            COUNT(*) as count
        FROM submissions
        GROUP BY status
    ''')
    
    stats_dict = {
        'pending': 0,
        'approved': 0,
        'rejected': 0
    }
    for status, count in stats:
        stats_dict[status] = count
    
    return render_template('admin.html', 
                         judges=judges,
                         stats=stats_dict,
                         active_page='dashboard')

@app.route('/admin/pending')
@admin_required
def admin_pending():
    # Get submissions grouped by judge name
    submissions = query_db('''
        SELECT
            name,
            position,
            ruling,
            link,
            x_link,
            COUNT(*) as submission_count,
            GROUP_CONCAT(id) as submission_ids,
            GROUP_CONCAT(ip_address) as ip_addresses,
            MIN(submitted_at) as first_submitted,
            GROUP_CONCAT(
                COALESCE(
                    (SELECT country_name || '|' || country_code2 || '|' || country_flag
                     FROM ip_geolocation
                     WHERE ip_geolocation.ip_address = submissions.ip_address
                     LIMIT 1),
                    'Unknown|XX|https://flagcdn.com/16x12/xx.png'
                )
            ) as locations
        FROM submissions
        WHERE status = "pending"
        GROUP BY name, position, ruling, link, x_link
        ORDER BY first_submitted ASC
    ''')
    
    return render_template('admin_pending.html',
                         submissions=submissions,
                         active_page='pending')
@app.route('/admin/logs')
@admin_required
def admin_logs():
    # Get all admin actions
    recent_actions = query_db('''
        SELECT admin_username, action, details, ip_address, timestamp
        FROM admin_logs
        ORDER BY timestamp DESC
        LIMIT 50
    ''')
    
    # Fetch geolocation data for each IP
    actions_with_location = []
    for action in recent_actions:
        admin_username, action_type, details, ip_address, timestamp = action
        geo_data = get_ip_geolocation(ip_address)
        location = format_geolocation_data(geo_data) if geo_data else "Location unknown"
        actions_with_location.append((
            admin_username, action_type, details, ip_address, timestamp, location
        ))
    
    return render_template('admin_logs.html',
                         recent_actions=actions_with_location,
                         active_page='logs')

@app.route('/admin/submission/<int:submission_id>/<action>', methods=['POST'])
@admin_required
def handle_submission(submission_id, action):
    if action == 'approve':
        # Get submission data
        submission = query_db('SELECT * FROM submissions WHERE id = ?', (submission_id,), one=True)
        if submission:
            # Add to judges table
            query_db('''
                INSERT INTO judges (name, job_position, ruling, link, x_link)
                VALUES (?, ?, ?, ?, ?)
            ''', (submission[1], submission[2], submission[3], submission[4], submission[5]))
            
            # Update submission status
            query_db('UPDATE submissions SET status = "approved" WHERE id = ?', (submission_id,))
            log_admin_action('approve_submission', f'Approved submission {submission_id}')
    
    elif action == 'reject':
        query_db('UPDATE submissions SET status = "rejected" WHERE id = ?', (submission_id,))
        log_admin_action('reject_submission', f'Rejected submission {submission_id}')
    
    elif action == 'delete':
        query_db('DELETE FROM submissions WHERE id = ?', (submission_id,))
        log_admin_action('delete_submission', f'Deleted submission {submission_id}')
    
    return redirect(url_for('admin_pending'))

@app.route('/admin/add', methods=['POST'])
@admin_required
def add_judge():
    name = request.form['name']
    job_position = request.form['job_position']
    ruling = request.form['ruling']
    link = request.form['ruling_link']
    x_link = request.form['relevant_link']
    
    query_db('''
        INSERT INTO judges (name, job_position, ruling, link, x_link)
        VALUES (?, ?, ?, ?, ?)
    ''', (name, job_position, ruling, link, x_link))
    
    log_admin_action('add_judge', f'Added judge {name}')
    return redirect(url_for('admin'))

@app.route('/admin/update/<int:judge_id>', methods=['POST'])
@admin_required
def update_judge(judge_id):
    name = request.form['name']
    job_position = request.form['job_position']
    ruling = request.form['ruling']
    link = request.form['ruling_link']
    x_link = request.form['relevant_link']
    
    query_db('''
        UPDATE judges
        SET name = ?, job_position = ?, ruling = ?, link = ?, x_link = ?
        WHERE id = ?
    ''', (name, job_position, ruling, link, x_link, judge_id))
    
    log_admin_action('update_judge', f'Updated judge {judge_id}')
    return redirect(url_for('admin'))

@app.route('/admin/disable/<int:judge_id>', methods=['POST'])
@admin_required
def disable_judge(judge_id):
    # Get current displayed state
    current_state = query_db('SELECT displayed FROM judges WHERE id = ?', (judge_id,), one=True)[0]
    # Set to 0 to disable, 1 to enable
    new_state = 0 if current_state == 1 else 1
    query_db('UPDATE judges SET displayed = ? WHERE id = ?', (new_state, judge_id))
    action = 'enable' if new_state == 1 else 'disable'
    log_admin_action(f'{action}_judge', f'{action.capitalize()}d judge {judge_id}')
    return redirect(url_for('admin'))

@app.route('/logout', methods=['POST'])
def logout():
    if session.get('logged_in'):
        log_admin_action('logout')
    session.clear()
    return redirect(url_for('admin'))

# Ensure localhost is whitelisted
try:
    add_ip_to_whitelist('127.0.0.1', 'localhost testing', hours=8760) # 1 year
except sqlite3.IntegrityError:
    pass  # Already exists

if __name__ == '__main__':
    app.run(debug=True)