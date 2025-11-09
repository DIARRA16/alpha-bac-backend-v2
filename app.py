from flask import Flask, request, jsonify, session
from flask_cors import CORS
from werkzeug.security import check_password_hash
from config import SECRET_KEY
from models import get_user_by_email, create_user, update_user_status, get_resources_by_subject, create_resource, delete_resource
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY

CORS(app)

# --- Authentification ---

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    user = get_user_by_email(email)

    if user and check_password_hash(user['password'], password):
        session['user_id'] = user['id']
        session['role'] = user['role']
        session['status'] = user['status']

        return jsonify({
            'success': True,
            'token': 'fake-jwt-token',
            'role': user['role'],
            'status': user['status']
        })

    return jsonify({'success': False, 'message': 'Identifiants incorrects'}), 401

@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    existing_user = get_user_by_email(email)
    if existing_user:
        return jsonify({'success': False, 'message': 'Email déjà utilisé'}), 400

    user = create_user(email, password)
    return jsonify({'success': True, 'message': 'Inscription réussie'})

# --- Ressources ---

@app.route('/api/resources', methods=['GET'])
def get_resources():
    subject = request.args.get('subject', 'math')
    published = request.args.get('published', 'true') == 'true'

    resources = get_resources_by_subject(subject, published)
    return jsonify(resources)

# --- Admin ---

@app.route('/api/admin/users', methods=['GET'])
def admin_get_users():
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403

    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    response = supabase.table('users').select('*').execute()
    return jsonify(response.data)

@app.route('/api/admin/users/<user_id>/activate', methods=['POST'])
def admin_activate_user(user_id):
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403

    update_user_status(user_id, 'active')
    return jsonify({'success': True, 'message': 'Utilisateur activé'})

@app.route('/api/admin/users/<user_id>/deactivate', methods=['POST'])
def admin_deactivate_user(user_id):
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403

    update_user_status(user_id, 'inactive')
    return jsonify({'success': True, 'message': 'Utilisateur désactivé'})

@app.route('/api/admin/resources', methods=['GET'])
def admin_get_resources():
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403

    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    response = supabase.table('resources').select('*').execute()
    return jsonify(response.data)

@app.route('/api/admin/resources', methods=['POST'])
def admin_create_resource():
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403

    data = request.get_json()
    resource = create_resource(
        data.get('title'),
        data.get('description'),
        data.get('subject'),
        data.get('resource_type'),
        data.get('filename')
    )
    return jsonify({'success': True, 'resource': resource})

@app.route('/api/admin/resources/<resource_id>', methods=['DELETE'])
def admin_delete_resource(resource_id):
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403

    delete_resource(resource_id)
    return jsonify({'success': True, 'message': 'Ressource supprimée'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))