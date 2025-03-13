from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from ip_geolocation import get_ip_geolocation, format_geolocation_data
from flask_caching import Cache

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_admin_secret_key')
# Configure other settings as needed, potentially different from the main app

# Flask-Caching configuration
# Use SimpleCache for development, switch to Redis/Memcached in production.
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})  # TODO: Configure for Redis in production.


# Database connection function (adjust as needed if using a different db setup)
def get_db_connection():
    conn = sqlite3.connect('../judges.db')  # Correct relative path
    conn.row_factory = sqlite3.Row
    return conn

def query_db(query, args=(), one=False, commit=True):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(query, args)
    if commit:
        conn.commit()
    rv = cur.fetchall()
    conn.close()
    return (rv[0] if rv else None) if one else rv

def get_client_ip():
    """Retrieves the client's IP address, accounting for Cloudflare proxy."""
    if 'CF-Connecting-IP' in request.headers:
        return request.headers.get('CF-Connecting-IP')
    else:
        return request.remote_addr

def log_admin_action(action, details=None):
    admin_username = session.get('username', 'unknown')
    ip_address = get_client_ip()
    query_db('''
        INSERT INTO admin_logs (admin_username, action, details, ip_address)
        VALUES (?, ?, ?, ?)
    ''', (admin_username, action, details, ip_address))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- New Routes for v0.7.0 ---

@app.route('/admin/suspicious_votes')
@admin_required
def suspicious_votes():
    # --- Criteria for Suspicious Activity ---
    # 1. High vote frequency from a single IP within a short time period.
    # 2. High vote frequency from a single fingerprint within a short time period.
    # 3. Rapid changes in vote ratio for a judge.

    # TODO: Define thresholds (these are just examples)
    ip_vote_threshold = 10  # Votes per IP per hour
    fingerprint_vote_threshold = 10  # Votes per fingerprint per hour
    ratio_change_threshold = 0.2  # 20% change in ratio within an hour

    # Get suspicious votes based on IP frequency
    suspicious_ips = query_db('''
        SELECT judge_id, ip_address, COUNT(*) as vote_count,
        (SELECT country_name FROM ip_geolocation WHERE ip_address = v.ip_address LIMIT 1) as country_name
        FROM votes v
        WHERE created_at > DATETIME('now', '-1 hour')
        GROUP BY judge_id, ip_address
        HAVING COUNT(*) > ?
    ''', (ip_vote_threshold,))

    # Get suspicious votes based on fingerprint frequency
    suspicious_fingerprints = query_db('''
        SELECT judge_id, browser_fingerprint, COUNT(*) as vote_count
        FROM votes
        WHERE created_at > DATETIME('now', '-1 hour')
        GROUP BY judge_id, browser_fingerprint
        HAVING COUNT(*) > ?
    ''', (fingerprint_vote_threshold,))

    # TODO: Implement logic for detecting rapid ratio changes

    return render_template('suspicious_votes.html', active_page='suspicious_votes',
                           suspicious_ips=suspicious_ips,
                           suspicious_fingerprints=suspicious_fingerprints)

@app.route('/admin/geo_votes')
@admin_required
def geo_votes():
    vote_distribution = query_db('''
        SELECT
            COALESCE(geo.country_code2, 'Unknown') as country_code,
            COUNT(*) as vote_count
        FROM votes v
        LEFT JOIN ip_geolocation geo ON v.ip_address = geo.ip_address
        GROUP BY country_code
    ''')

    # Transform to list of dicts for easy JSON serialization
    data = [{'country_code': row[0], 'vote_count': row[1]} for row in vote_distribution]

    return jsonify(data)

@app.route('/admin/vote_analysis')
@admin_required
def vote_analysis():
    # Placeholder data for now
    data = {
        'labels': ['Corrupt', 'Not Corrupt', 'Undecided'],
        'datasets': [{
            'label': 'Vote Distribution',
            'data': [120, 50, 30],  # Example data
            'backgroundColor': ['rgba(255, 99, 132, 0.5)', 'rgba(75, 192, 192, 0.5)', 'rgba(255, 205, 86, 0.5)'],
            'borderColor': ['rgba(255, 99, 132, 1)', 'rgba(75, 192, 192, 1)', 'rgba(255, 205, 86, 1)'],
            'borderWidth': 1
        }]
    }
    return render_template('vote_analysis.html', active_page='vote_analysis', data=data)

@app.route('/admin/submission_analysis')
@admin_required
def submission_analysis():
    # Placeholder data for now
    data = {
        'labels': ['Pending', 'Approved', 'Rejected'],
        'datasets': [{
            'label': 'Submission Status',
            'data': [20, 150, 10],  # Example data
            'backgroundColor': ['rgba(255, 205, 86, 0.5)', 'rgba(75, 192, 192, 0.5)', 'rgba(255, 99, 132, 0.5)'],
            'borderColor': ['rgba(255, 205, 86, 1)', 'rgba(75, 192, 192, 1)', 'rgba(255, 99, 132, 1)'],
            'borderWidth': 1
        }]
    }
    return render_template('submission_analysis.html', active_page='submission_analysis', data=data)

# --- Existing Admin Routes ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            session['username'] = username
            log_admin_action('login')
            return redirect(url_for('admin'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

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

@app.route('/admin/recalculate_status', methods=['POST']) # This will be removed later
@admin_required
def recalculate_status():
    # Get all judges with vote counts
    judges = query_db('''
        SELECT j.*,
            COALESCE(SUM(CASE WHEN v.vote_type = 'corrupt' THEN 1 ELSE 0 END), 0) AS corrupt_votes,
            COALESCE(SUM(CASE WHEN v.vote_type = 'not_corrupt' THEN 1 ELSE 0 END), 0) AS not_corrupt_votes
        FROM judges j
        LEFT JOIN votes v ON j.id = v.judge_id
        GROUP BY j.id
    ''')

    # Recalculate status and update database
    for judge in judges:
        judge_id = judge[0]
        total_votes = judge[-2] + judge[-1]
        status = 'undecided'
        if total_votes >= 5:
            corrupt_ratio = judge[-2] / total_votes if total_votes > 0 else 0
            not_corrupt_ratio = judge[-1] / total_votes if total_votes > 0 else 0
            if corrupt_ratio >= 0.8333:
                status = 'corrupt'
            elif not_corrupt_ratio >= 0.8333:
                status = 'not_corrupt'

        query_db('UPDATE judges SET status = ? WHERE id = ?', (status, judge_id))

    log_admin_action('recalculate_status', 'Recalculated judge statuses based on vote counts')
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=True, port=port)