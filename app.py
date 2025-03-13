from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, jsonify, render_template, request, redirect, url_for, send_from_directory
import sqlite3
import os
from datetime import datetime, timedelta
from functools import wraps
from flask_cors import CORS
import secrets
import hmac
import hashlib
import time
from flask_caching import Cache  # Import Flask-Caching

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
# !!! IMPORTANT !!!  Move this to an environment variable in production.
app.config['HMAC_SECRET_KEY'] = secrets.token_hex(32)  # Generate a 64-character hex key
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'your_secret_key') # TODO consider removing, not used in main app

# Flask-Caching configuration
# Use SimpleCache for development, switch to Redis/Memcached in production
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})  # TODO: Configure for Redis in production

# Removed session config: not needed for the main app
# app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)
# app.config['SESSION_COOKIE_SECURE'] = True
# app.config['SESSION_COOKIE_HTTPONLY'] = True
# app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

CORS(app)  # Enable CORS for all routes.  TODO: Configure for specific origin in production.

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

def get_client_ip():
    """Retrieves the client's IP address, accounting for Cloudflare proxy."""
    if 'CF-Connecting-IP' in request.headers:
        return request.headers.get('CF-Connecting-IP')
    else:
        return request.remote_addr

def is_ip_whitelisted(ip_address):
    result = query_db('''
        SELECT * FROM ip_whitelist 
        WHERE ip_address = ? AND expiry > ?
    ''', (ip_address, datetime.now().isoformat()), one=True)
    return bool(result)

def check_rate_limit(ip_address):
    # Always allow localhost for testing and whitelisted IPs
    if ip_address == '127.0.0.1' or is_ip_whitelisted(ip_address):
        return True

    # Check submissions in last 10 minutes
    ten_mins_ago = (datetime.now() - timedelta(minutes=10)).isoformat()
    recent_submissions = query_db('''
        SELECT COUNT(*) FROM submissions 
        WHERE ip_address = ? AND submitted_at > ?
    ''', (ip_address, ten_mins_ago), one=True)[0]
    
    return recent_submissions == 0

def verify_proof_of_work(nonce, hash, difficulty):
    target_prefix = '0' * difficulty
    data = f'nonce:{nonce}'
    message_data = data.encode('utf-8')
    calculated_hash = hashlib.sha256(message_data).hexdigest()
    return calculated_hash == hash and calculated_hash.startswith(target_prefix)

def hmac_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Get timestamp and signature from headers
        timestamp = request.headers.get('X-HMAC-Timestamp')
        received_signature = request.headers.get('X-HMAC-Signature')

        if not timestamp or not received_signature:
            return jsonify({'success': False, 'error': 'Missing HMAC headers'}), 401

        # Check timestamp validity (within 5 minutes)
        try:
            timestamp = int(timestamp)
            if time.time() - timestamp > 300:  # 300 seconds = 5 minutes
                return jsonify({'success': False, 'error': 'Timestamp expired'}), 401
        except ValueError:
            return jsonify({'success': False, 'error': 'Invalid timestamp format'}), 401

        # Reconstruct the message for signature verification
        message = request.method + request.path
        if request.get_data():
            message += request.get_data().decode('utf-8')  # Important: Decode for consistent hashing
        message += str(timestamp)

        # Calculate the expected signature
        secret_key_bytes = app.config['HMAC_SECRET_KEY'].encode('utf-8')
        message_bytes = message.encode('utf-8')
        expected_signature = hmac.new(secret_key_bytes, message_bytes, hashlib.sha256).hexdigest()

        # Compare signatures
        if not hmac.compare_digest(expected_signature, received_signature):
            return jsonify({'success': False, 'error': 'Invalid HMAC signature'}), 401

        return f(*args, **kwargs)

    return decorated_function

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/judges')
@cache.cached(timeout=60)  # Cache this view for 60 seconds
def get_judges():
    # Get the USA filter parameter
    usa_only = request.args.get('usa_only', 'false').lower() == 'true'

    # Get judges with vote counts
    judges = query_db('''
        SELECT j.*,
            COALESCE(SUM(CASE WHEN v.vote_type = 'corrupt' THEN 1 ELSE 0 END), 0) AS corrupt_votes,
            COALESCE(SUM(CASE WHEN v.vote_type = 'not_corrupt' THEN 1 ELSE 0 END), 0) AS not_corrupt_votes
            , v.ip_address
        FROM judges j
        LEFT JOIN votes v ON j.id = v.judge_id
        LEFT JOIN ip_geolocation geo ON v.ip_address = geo.ip_address
        WHERE j.displayed = 1
        GROUP BY j.id, geo.country_code2
        HAVING (NOT ?1) OR (geo.country_code2 = 'US')
    ''', (usa_only,))

   # Determine status based on vote ratios
    judges_with_status = []
    for judge in judges:
        total_votes = judge[-3] + judge[-2]
        status = 'undecided'
        if total_votes >= 5:
            corrupt_ratio = judge[-3] / total_votes
            not_corrupt_ratio = judge[-2] / total_votes
            if corrupt_ratio >= 0.8333:
                status = 'corrupt'
            elif not_corrupt_ratio >= 0.8333:
                status = 'not_corrupt'

        judges_with_status.append({
            **dict(zip(['id', 'name', 'job_position', 'ruling', 'link', 'x_link', 'displayed'], judge[:-3])),
            'corrupt_votes': judge[-3],
            'not_corrupt_votes': judge[-2],
            'status': status
        })

    return jsonify({'judges': judges_with_status})

@app.route('/vote/<int:judge_id>', methods=['POST'])
@hmac_required
def submit_vote(judge_id):
    ip_address = get_client_ip()
    data = request.json

    #Check if judge exists
    judge = query_db('SELECT * FROM judges WHERE id = ? AND displayed = 1', (judge_id,), one=True)
    if not judge:
        return jsonify({'success': False, 'error': 'Judge not found'}), 404
    
    # Check rate limit (1 vote per judge per day)
    if not is_ip_whitelisted(ip_address):
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

    # Verify proof of work
    proof_of_work = data.get('proofOfWork')
    if not proof_of_work:
        return jsonify({'success': False, 'error': 'Missing proof of work'}), 400
    if not verify_proof_of_work(proof_of_work.get('nonce'), proof_of_work.get('hash'), 4):  # Use difficulty 4
        return jsonify({'success': False, 'error': 'Invalid proof of work'}), 400

    # Insert vote
    try:
        query_db('''
            INSERT INTO votes (judge_id, ip_address, vote_type, browser_fingerprint)
            VALUES (?, ?, ?, ?)
        ''', (judge_id, ip_address, vote_type, data.get('fingerprint')))

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/submit-judge', methods=['POST'])
@hmac_required
def submit_judge():
    ip_address = get_client_ip()

    if not check_rate_limit(ip_address):
        return jsonify({
            'success': False, 
            'error': 'Rate limit exceeded. Please wait 10 minutes between submissions.'
        })

    data = request.json
    try:
        # Cache IP geolocation data immediately
        get_ip_geolocation_task.delay(ip_address)

        # Honeypot check
        if data.get('honeypot'):
            # log_admin_action('honeypot_triggered', f'IP: {ip_address}')  # Removed: log_admin_action is in admin app
            return jsonify({'success': False, 'error': 'Submission rejected'}), 400  # Reject submission
        
        # Verify proof of work
        proof_of_work = data.get('proofOfWork')
        if not proof_of_work:
            return jsonify({'success': False, 'error': 'Missing proof of work'}), 400
        if not verify_proof_of_work(proof_of_work.get('nonce'), proof_of_work.get('hash'), 4):  # Use difficulty 4
            return jsonify({'success': False, 'error': 'Invalid proof of work'}), 400


        query_db('''
            INSERT INTO submissions (name, position, ruling, link, x_link, ip_address)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (data['name'], data['position'],
              data['ruling'], data['link'], data['x_link'], ip_address))
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    app.run(debug=True, port=port)