from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory
import psycopg2
import psycopg2.extras
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime, timedelta
from functools import wraps
from ip_geolocation import get_ip_geolocation, format_geolocation_data
from flask_caching import Cache
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_admin_secret_key')
# Configure other settings as needed, potentially different from the main app

# Flask-Caching configuration
# Use SimpleCache for development, switch to Redis/Memcached in production.
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})  # TODO: Configure for Redis in production.


# Database connection function (adjust as needed if using a different db setup)
def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        port=os.environ.get('DB_PORT', '5432'),
        dbname=os.environ.get('DB_NAME', 'jai_db'),
        user=os.environ.get('DB_USER', 'jai'),
        password=os.environ.get('DB_PASSWORD', '')
    )
    conn.autocommit = True
    return conn

def query_db(query, args=(), one=False, commit=True):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor if one else None)
    cur.execute(query, args)
    if commit:
        conn.commit()
    rv = cur.fetchall()
    cur.close()
    conn.close()
    return (dict(rv[0]) if rv else None) if one else rv

def get_client_ip():
    """Retrieves the client's IP address, accounting for Cloudflare proxy."""
    if 'CF-Connecting-IP' in request.headers:
        return request.headers.get('CF-Connecting-IP')
    else:
        return request.remote_addr

def log_admin_action(action, details=None):
    admin_username = session.get('username', 'unknown')
    ip_address = get_client_ip()
    try:
        query_db('''
            INSERT INTO admin_logs (admin_username, action, details, ip_address)
            VALUES (%s, %s, %s, %s)
        ''', (admin_username, action, details, ip_address))
    except Exception as e:
        print(f"Error logging admin action: {e}")
        # Continue execution even if logging fails
        pass

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

    # Define thresholds for suspicious activity
    ip_vote_threshold = 5  # Votes per IP per hour
    fingerprint_vote_threshold = 5  # Votes per fingerprint per hour
    ratio_change_threshold = 0.15  # 15% change in ratio within an hour

    # Get suspicious votes based on IP frequency
    suspicious_ips = query_db('''
        SELECT 
            v.judge_id, 
            v.ip_address, 
            COUNT(*) as vote_count,
            (SELECT name FROM judges WHERE id = v.judge_id) as judge_name,
            (SELECT country_name FROM ip_geolocation WHERE ip_address = v.ip_address LIMIT 1) as country_name,
            MAX(v.created_at) as latest_vote
        FROM votes v
        WHERE v.created_at > NOW() - INTERVAL '1 hour'
        GROUP BY v.judge_id, v.ip_address
        HAVING COUNT(*) >= %s
        ORDER BY vote_count DESC, latest_vote DESC
    ''', (ip_vote_threshold,))

    # Get suspicious votes based on fingerprint frequency
    suspicious_fingerprints = query_db('''
        SELECT 
            v.judge_id, 
            v.browser_fingerprint, 
            COUNT(*) as vote_count,
            (SELECT name FROM judges WHERE id = v.judge_id) as judge_name,
            MAX(v.created_at) as latest_vote
        FROM votes v
        WHERE v.created_at > NOW() - INTERVAL '1 hour'
        GROUP BY v.judge_id, v.browser_fingerprint
        HAVING COUNT(*) >= %s
        ORDER BY vote_count DESC, latest_vote DESC
    ''', (fingerprint_vote_threshold,))

    # Detect rapid ratio changes
    # First, get vote counts from an hour ago
    judges_data = query_db('''
        SELECT 
            j.id as judge_id,
            j.name as judge_name,
            (SELECT COUNT(*) FROM votes 
             WHERE judge_id = j.id AND vote_type = 'corrupt' AND created_at <= NOW() - INTERVAL '1 hour') as corrupt_votes_before,
            (SELECT COUNT(*) FROM votes 
             WHERE judge_id = j.id AND vote_type = 'not_corrupt' AND created_at <= NOW() - INTERVAL '1 hour') as not_corrupt_votes_before,
            (SELECT COUNT(*) FROM votes 
             WHERE judge_id = j.id AND vote_type = 'corrupt') as corrupt_votes_now,
            (SELECT COUNT(*) FROM votes 
             WHERE judge_id = j.id AND vote_type = 'not_corrupt') as not_corrupt_votes_now
        FROM judges j
        WHERE j.displayed = 1
    ''')
    
    ratio_changes = []
    for judge in judges_data:
        judge_id, judge_name, corrupt_before, not_corrupt_before, corrupt_now, not_corrupt_now = judge
        
        # Calculate ratios
        total_before = corrupt_before + not_corrupt_before
        total_now = corrupt_now + not_corrupt_now
        
        # Skip judges with too few votes
        if total_before < 10 or total_now < 10:
            continue
            
        corrupt_ratio_before = corrupt_before / total_before if total_before > 0 else 0
        corrupt_ratio_now = corrupt_now / total_now if total_now > 0 else 0
        
        ratio_change = abs(corrupt_ratio_now - corrupt_ratio_before)
        
        if ratio_change >= ratio_change_threshold:
            ratio_changes.append({
                'judge_id': judge_id,
                'judge_name': judge_name,
                'corrupt_ratio_before': round(corrupt_ratio_before * 100, 1),
                'corrupt_ratio_now': round(corrupt_ratio_now * 100, 1),
                'ratio_change': round(ratio_change * 100, 1),
                'votes_before': total_before,
                'votes_now': total_now,
                'new_votes': total_now - total_before
            })
    
    # Sort by ratio change (descending)
    ratio_changes.sort(key=lambda x: x['ratio_change'], reverse=True)

    # Get recent voting patterns (last 24 hours)
    recent_votes = query_db('''
        SELECT 
            EXTRACT(HOUR FROM created_at) as hour,
            COUNT(*) as vote_count
        FROM votes
        WHERE created_at > NOW() - INTERVAL '24 hours'
        GROUP BY hour
        ORDER BY hour
    ''')
    
    hourly_votes = [0] * 24
    for hour, count in recent_votes:
        hourly_votes[int(hour)] = count

    return render_template('suspicious_votes.html', 
                           active_page='suspicious_votes',
                           suspicious_ips=suspicious_ips,
                           suspicious_fingerprints=suspicious_fingerprints,
                           ratio_changes=ratio_changes,
                           hourly_votes=hourly_votes)

@app.route('/admin/geo_votes')
@admin_required
def geo_votes():
    # Get vote distribution by country
    country_distribution = query_db('''
        SELECT
            COALESCE(geo.country_code2, 'Unknown') as country_code,
            COALESCE(geo.country_name, 'Unknown') as country_name,
            COUNT(*) as vote_count
        FROM votes v
        LEFT JOIN ip_geolocation geo ON v.ip_address = geo.ip_address
        GROUP BY country_code, country_name
        ORDER BY vote_count DESC
    ''')
    
    # Get vote distribution by region (for top 5 countries)
    top_countries = [row[0] for row in country_distribution[:5] if row[0] != 'Unknown']
    
    region_distribution = []
    if top_countries:
        placeholders = ','.join(['%s'] * len(top_countries))
        region_distribution = query_db(f'''
            SELECT
                geo.country_code2 as country_code,
                geo.country_name as country_name,
                COALESCE(geo.continent_name, 'Unknown') as region,
                COUNT(*) as vote_count
            FROM votes v
            JOIN ip_geolocation geo ON v.ip_address = geo.ip_address
            WHERE geo.country_code2 IN ({placeholders})
            GROUP BY country_code, country_name, continent_name
            ORDER BY country_name, vote_count DESC
        ''', top_countries)
    
    # Get vote distribution by time of day (hourly)
    hourly_distribution = query_db('''
        SELECT 
            EXTRACT(HOUR FROM created_at) as hour,
            COUNT(*) as vote_count
        FROM votes
        WHERE created_at > NOW() - INTERVAL '7 days'
        GROUP BY hour
        ORDER BY hour
    ''')
    
    hourly_data = [0] * 24
    for hour, count in hourly_distribution:
        hourly_data[int(hour)] = count
    
    # Get vote distribution by day of week
    daily_distribution = query_db('''
        SELECT 
            EXTRACT(DOW FROM created_at) as day_of_week,
            COUNT(*) as vote_count
        FROM votes
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY day_of_week
        ORDER BY day_of_week
    ''')
    
    daily_data = [0] * 7
    for day, count in daily_distribution:
        daily_data[int(day)] = count
    
    # Format data for template
    data = {
        'countries': [{'country_code': row[0], 'country_name': row[1], 'vote_count': row[2]} for row in country_distribution],
        'regions': [{'country_code': row[0], 'country_name': row[1], 'region': row[2], 'vote_count': row[3]} for row in region_distribution],
        'hourly': hourly_data,
        'daily': daily_data
    }

    return render_template('geo_votes.html', active_page='geo_votes', data=data)

@app.route('/admin/vote_analysis')
@admin_required
def vote_analysis():
    # Get overall vote distribution
    vote_types = query_db('''
        SELECT 
            vote_type, 
            COUNT(*) as count
        FROM votes
        GROUP BY vote_type
        ORDER BY count DESC
    ''')
    
    # Get vote trends over time (last 30 days by day)
    vote_trends = query_db('''
        SELECT 
            DATE(created_at) as vote_date,
            vote_type,
            COUNT(*) as count
        FROM votes
        WHERE created_at > NOW() - INTERVAL '30 days'
        GROUP BY vote_date, vote_type
        ORDER BY vote_date
    ''')
    
    # Process vote trends data for chart
    dates = []
    corrupt_counts = []
    not_corrupt_counts = []
    undecided_counts = []
    
    current_date = None
    corrupt = 0
    not_corrupt = 0
    undecided = 0
    
    for row in vote_trends:
        vote_date, vote_type, count = row
        
        if current_date != vote_date:
            if current_date is not None:
                dates.append(current_date)
                corrupt_counts.append(corrupt)
                not_corrupt_counts.append(not_corrupt)
                undecided_counts.append(undecided)
            
            current_date = vote_date
            corrupt = 0
            not_corrupt = 0
            undecided = 0
        
        if vote_type == 'corrupt':
            corrupt = count
        elif vote_type == 'not_corrupt':
            not_corrupt = count
        else:  # undecided
            undecided = count
    
    # Add the last date
    if current_date is not None:
        dates.append(current_date)
        corrupt_counts.append(corrupt)
        not_corrupt_counts.append(not_corrupt)
        undecided_counts.append(undecided)
    
    # Get top judges by vote count
    top_judges = query_db('''
        SELECT 
            j.id,
            j.name,
            COUNT(v.id) as vote_count
        FROM judges j
        JOIN votes v ON j.id = v.judge_id
        GROUP BY j.id
        ORDER BY vote_count DESC
        LIMIT 10
    ''')
    
    # Get vote distribution for top 5 judges
    top_judge_ids = [row[0] for row in top_judges[:5]]
    
    judge_vote_distribution = []
    if top_judge_ids:
        placeholders = ','.join(['%s'] * len(top_judge_ids))
        judge_vote_distribution = query_db(f'''
            SELECT 
                j.id,
                j.name,
                v.vote_type,
                COUNT(v.id) as vote_count
            FROM judges j
            JOIN votes v ON j.id = v.judge_id
            WHERE j.id IN ({placeholders})
            GROUP BY j.id, j.name, v.vote_type
            ORDER BY j.name, v.vote_type
        ''', top_judge_ids)
    
    # Process judge vote distribution data
    judge_data = {}
    for row in judge_vote_distribution:
        judge_id, judge_name, vote_type, vote_count = row
        
        if judge_name not in judge_data:
            judge_data[judge_name] = {'corrupt': 0, 'not_corrupt': 0, 'undecided': 0}
        
        judge_data[judge_name][vote_type] = vote_count
    
    # Prepare data for template
    data = {
        'vote_types': {
            'labels': [row[0].replace('_', ' ').title() for row in vote_types],
            'counts': [row[1] for row in vote_types]
        },
        'vote_trends': {
            'dates': dates,
            'corrupt': corrupt_counts,
            'not_corrupt': not_corrupt_counts,
            'undecided': undecided_counts
        },
        'top_judges': {
            'names': [row[1] for row in top_judges],
            'counts': [row[2] for row in top_judges]
        },
        'judge_vote_distribution': judge_data
    }
    
    return render_template('vote_analysis.html', active_page='vote_analysis', data=data)

@app.route('/admin/submission_analysis')
@admin_required
def submission_analysis():
    # Get submission statistics by status
    status_counts = query_db('''
        SELECT status, COUNT(*) as count
        FROM submissions
        GROUP BY status
    ''')
    
    # Get submission counts by date
    date_counts = query_db('''
        SELECT DATE(submitted_at) as date, COUNT(*) as count
        FROM submissions
        GROUP BY DATE(submitted_at)
        ORDER BY date ASC
    ''')
    
    # Get top submitters by IP
    top_submitters = query_db('''
        SELECT ip_address, COUNT(*) as count
        FROM submissions
        GROUP BY ip_address
        ORDER BY count DESC
        LIMIT 10
    ''')
    
    # Get all submissions for detailed analysis
    submissions = query_db('''
        SELECT id, name, position, ruling, status, ip_address, submitted_at
        FROM submissions
        ORDER BY submitted_at DESC
        LIMIT 100
    ''')
    
    # Process status counts
    pending_count = 0
    approved_count = 0
    rejected_count = 0
    
    for item in status_counts:
        if item[0] == 'pending':
            pending_count = item[1]
        elif item[0] == 'approved':
            approved_count = item[1]
        elif item[0] == 'rejected':
            rejected_count = item[1]
    
    total_count = pending_count + approved_count + rejected_count
    
    # Format data for charts
    data = {
        'status': {
            'labels': ['Pending', 'Approved', 'Rejected'],
            'counts': [pending_count, approved_count, rejected_count]
        },
        'dates': {
            'labels': [str(item[0]) for item in date_counts],
            'counts': [item[1] for item in date_counts]
        },
        'top_submitters': {
            'ips': [item[0] for item in top_submitters],
            'counts': [item[1] for item in top_submitters]
        },
        'submissions': submissions,
        'total_count': total_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count
    }
    
    return render_template('submission_analysis.html', active_page='submission_analysis', data=data)

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

        query_db('UPDATE judges SET status = %s WHERE id = %s', (status, judge_id))

    log_admin_action('recalculate_status', 'Recalculated judge statuses based on vote counts')
    return redirect(url_for('admin'))

# --- Existing Admin Routes ---

@app.route('/')
def index():
    if session.get('logged_in'):
        return redirect(url_for('admin'))
    else:
        return redirect(url_for('login'))

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
    # First, ensure Antarctica data is in the database for 127.0.0.1
    get_ip_geolocation('127.0.0.1')
    
    # Get submissions grouped by judge name
    submissions = query_db('''
        SELECT
            name,
            position,
            ruling,
            link,
            x_link,
            COUNT(*) as submission_count,
            STRING_AGG(id::text, ',') as submission_ids,
            STRING_AGG(ip_address, ',') as ip_addresses,
            MIN(submitted_at) as first_submitted,
            STRING_AGG(
                COALESCE(
                    (SELECT country_name || '|' || country_code2 || '|' || country_flag
                     FROM ip_geolocation
                     WHERE ip_geolocation.ip_address = submissions.ip_address
                     LIMIT 1),
                    'Unknown|XX|https://flagcdn.com/16x12/xx.png'
                ),
                ','
            ) as locations
        FROM submissions
        WHERE status = 'pending'
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
        geo_data = get_ip_geolocation(action[3])
        location = format_geolocation_data(geo_data) if geo_data else "Location unknown"
        actions_with_location.append({
            'admin_username': action[0],
            'action': action[1],
            'details': action[2],
            'ip_address': action[3],
            'timestamp': action[4],
            'location': location
        })
    
    return render_template('admin_logs.html',
                         recent_actions=actions_with_location,
                         active_page='logs')

@app.route('/admin/submission/<int:submission_id>/<action>', methods=['POST'])
@admin_required
def handle_submission(submission_id, action):
    if action == 'approve':
        # Get submission data
        submission = query_db('SELECT * FROM submissions WHERE id = %s', (submission_id,), one=True)
        if submission:
            # Add to judges table
            query_db('''
                INSERT INTO judges (name, job_position, ruling, link, x_link)
                VALUES (%s, %s, %s, %s, %s)
            ''', (submission[1], submission[2], submission[3], submission[4], submission[5]))
            
            # Update submission status
            query_db('UPDATE submissions SET status = "approved" WHERE id = %s', (submission_id,))
            log_admin_action('approve_submission', f'Approved submission {submission_id}')
    
    elif action == 'reject':
        query_db('UPDATE submissions SET status = "rejected" WHERE id = %s', (submission_id,))
        log_admin_action('reject_submission', f'Rejected submission {submission_id}')
    
    elif action == 'delete':
        query_db('DELETE FROM submissions WHERE id = %s', (submission_id,))
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
        VALUES (%s, %s, %s, %s, %s)
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
        SET name = %s, job_position = %s, ruling = %s, link = %s, x_link = %s
        WHERE id = %s
    ''', (name, job_position, ruling, link, x_link, judge_id))
    
    log_admin_action('update_judge', f'Updated judge {judge_id}')
    return redirect(url_for('admin'))

@app.route('/admin/disable/<int:judge_id>', methods=['POST'])
@admin_required
def disable_judge(judge_id):
    # Get current displayed state
    current_state = query_db('SELECT displayed FROM judges WHERE id = %s', (judge_id,), one=True)[0]
    # Set to 0 to disable, 1 to enable
    new_state = 0 if current_state == 1 else 1
    query_db('UPDATE judges SET displayed = %s WHERE id = %s', (new_state, judge_id))
    action = 'enable' if new_state == 1 else 'disable'
    log_admin_action(f'{action}_judge', f'Judge ID: {judge_id}')
    return redirect(url_for('admin'))

@app.route('/logout', methods=['GET', 'POST'])
@app.route('/admin/logout', methods=['GET', 'POST'])
def logout():
    if session.get('logged_in'):
        log_admin_action('logout')
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5001))
    app.run(debug=True, port=port)