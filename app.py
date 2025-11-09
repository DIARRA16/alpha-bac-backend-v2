from flask import Flask, request, jsonify, session
from werkzeug.security import check_password_hash
from config import SECRET_KEY
from werkzeug.utils import secure_filename
from models import get_user_by_email, create_user, update_user_status, get_resources_by_subject, create_resource, delete_resource
import os

app = Flask(__name__)
app.secret_key = SECRET_KEY

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
            'token': 'fake-jwt-token',  # Vous pouvez utiliser JWT ici si vous le souhaitez
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
@app.route('/api/admin/upload', methods=['POST'])
def admin_upload_file():
    if not session.get('user_id') or session.get('role') != 'admin':
        return jsonify({'success': False, 'message': 'Accès refusé'}), 403

    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'Aucun fichier envoyé'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'message': 'Fichier vide'}), 400

    # Récupérer les métadonnées
    resource_type = request.form.get('resource_type')  # 'enonce', 'correction', 'video', 'audio'
    subject = request.form.get('subject')  # 'math', 'pc', 'svt'
    title = request.form.get('title')
    description = request.form.get('description', '')

    # Déterminer le dossier dans Supabase Storage
    folder_map = {
        'enonce': 'enonces',
        'correction': 'corrections',
        'video': 'videos',
        'audio': 'audios'
    }

    folder = folder_map.get(resource_type)
    if not folder:
        return jsonify({'success': False, 'message': 'Type de fichier invalide'}), 400

    filename = secure_filename(file.filename)

    # Upload dans Supabase Storage
    from models import upload_file_to_supabase_storage
    success = upload_file_to_supabase_storage(file, folder, filename)

    if not success:
        return jsonify({'success': False, 'message': 'Échec de l’upload'}), 500

    # Sauvegarder les métadonnées dans la base
    create_resource(title, description, subject, resource_type, filename)

    return jsonify({'success': True, 'message': 'Fichier ajouté avec succès'})

# --- Démarrage du serveur ---

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))