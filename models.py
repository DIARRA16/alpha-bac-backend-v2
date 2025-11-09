from supabase import create_client, Client
from config import SUPABASE_URL, SUPABASE_KEY

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_user_by_email(email: str):
    response = supabase.table('users').select('*').eq('email', email).execute()
    return response.data[0] if response.data else None

def create_user(email: str, password: str):
    from werkzeug.security import generate_password_hash
    hashed = generate_password_hash(password)
    response = supabase.table('users').insert({
        'email': email,
        'password': hashed,
        'role': 'user',
        'status': 'pending'
    }).execute()
    return response.data[0]

def update_user_status(user_id: str, status: str):
    response = supabase.table('users').update({'status': status}).eq('id', user_id).execute()
    return response.data[0]

def get_resources_by_subject(subject: str, published: bool = True):
    response = supabase.table('resources').select('*').eq('subject', subject).eq('is_published', published).execute()
    return response.data

def create_resource(title: str, description: str, subject: str, resource_type: str, filename: str):
    response = supabase.table('resources').insert({
        'title': title,
        'description': description,
        'subject': subject,
        'resource_type': resource_type,
        'filename': filename,
        'is_published': True
    }).execute()
    return response.data[0]

def delete_resource(resource_id: str):
    response = supabase.table('resources').delete().eq('id', resource_id).execute()
    return response.data
def upload_file_to_supabase_storage(file, folder: str, filename: str):
    """
    Upload un fichier dans Supabase Storage
    """
    from supabase import create_client
    from config import SUPABASE_URL, SUPABASE_KEY

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # Lire le contenu du fichier
    file_content = file.read()

    # Téléverser dans le bon dossier
    response = supabase.storage.from_('alpha-bac-storage').upload(
        f"{folder}/{filename}",
        file_content,
        file_options={"content-type": file.content_type}
    )

    if response:
        return True
    return False