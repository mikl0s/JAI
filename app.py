from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from ip_geolocation import get_ip_geolocation, format_geolocation_data

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = 'your_secret_key'  # Change this to a random secret key

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
    if is_ip_whitelisted(ip_address):
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
    confirmed = query_db('SELECT * FROM judges WHERE confirmed = 1')
    undecided = query_db('SELECT * FROM judges WHERE confirmed = 0')
    return jsonify({'confirmed': confirmed, 'undecided': undecided})

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
                    (SELECT country_name || '|' || country_code2
                     FROM ip_geolocation
                     WHERE ip_geolocation.ip_address = submissions.ip_address
                     LIMIT 1),
                    'Unknown|XX'
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
                INSERT INTO judges (name, job_position, ruling, link, x_link, confirmed)
                VALUES (?, ?, ?, ?, ?, 0)
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
        INSERT INTO judges (name, job_position, ruling, link, x_link, confirmed)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (name, job_position, ruling, link, x_link, 0))
    
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
    confirmed = request.form['confirmed']
    
    query_db('''
        UPDATE judges 
        SET name = ?, job_position = ?, ruling = ?, link = ?, x_link = ?, confirmed = ? 
        WHERE id = ?
    ''', (name, job_position, ruling, link, x_link, confirmed, judge_id))
    
    log_admin_action('update_judge', f'Updated judge {judge_id}')
    return redirect(url_for('admin'))

@app.route('/admin/disable/<int:judge_id>', methods=['POST'])
@admin_required
def disable_judge(judge_id):
    query_db('UPDATE judges SET displayed = 0 WHERE id = ?', (judge_id,))
    log_admin_action('disable_judge', f'Disabled judge {judge_id}')
    return redirect(url_for('admin'))

@app.route('/logout', methods=['POST'])
def logout():
    if session.get('logged_in'):
        log_admin_action('logout')
    session.clear()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)