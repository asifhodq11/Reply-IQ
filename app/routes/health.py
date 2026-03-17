from flask import Blueprint, jsonify, current_app
from app.extensions import supabase
import time

health_bp = Blueprint('health', __name__)

@health_bp.route('/health')
def health():
    # Crash fast if DEBUG=True sneaked into Production
    assert not current_app.config['DEBUG'], 'CRITICAL: DEBUG=True in production!'

    # Ping the real users table using the shared Supabase client from extensions.py
    start_time = time.time()
    db_status = 'ok'
    try:
        supabase.table('users').select('id').limit(1).execute()
    except Exception as e:
        db_status = f'error: {str(e)}'

    db_latency = int((time.time() - start_time) * 1000)

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
