from flask import Blueprint, jsonify, current_app
from app.extensions import supabase
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health():
    # Crash fast if somehow DEBUG=True sneaked into Production
    assert not current_app.config['DEBUG'], 'CRITICAL: DEBUG=True in production!'
    
    # Measure DB latency using the ONE shared client from extensions.py
    # We do a cheap healthcheck (rpc or a simple query) because tables don't exist yet
    start_time = time.time()
    db_status = 'ok'
    try:
        # A simple lightweight query to prove Supabase connection works
        # This queries the built-in postgres version just to prove network connectivity
        supabase.rpc("get_service_role_status").execute() 
        # Note: In Phase 2 when tables exist, we can change this to a simple
        # supabase.table('users').select('id', count='exact').limit(1).execute()
    except Exception as e:
        # We catch and log this instead of crashing the health endpoint
        # so UptimeRobot knows the APP is up but DB fails.
        db_status = f'error: {str(e)}'
        
    db_latency = int((time.time() - start_time) * 1000)

    # Required JSON shape from Chapter 12
    return jsonify({
        'status': 'healthy',
        'version': '1.0.0',
        'checks': {
            'database': {
                'status': db_status, 
                'latency_ms': db_latency
            },
            'environment': current_app.config.get('FLASK_ENV', 'unknown')
        }
    }), 200
