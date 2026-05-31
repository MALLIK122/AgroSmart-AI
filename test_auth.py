from app import app, BASE_DIR
import json, os

client = app.test_client()

username='testuser_ai'
email='testuser@example.com'
password='TestPass123'

users_file = os.path.join(BASE_DIR,'data','users.json')
# Ensure users file exists and remove any existing test user
if os.path.exists(users_file):
    try:
        with open(users_file,'r',encoding='utf-8') as f:
            users = json.load(f)
    except Exception:
        users = []
else:
    users = []

users = [u for u in users if u.get('username') != username]
with open(users_file,'w',encoding='utf-8') as f:
    json.dump(users, f, ensure_ascii=False, indent=2)

# Signup
resp = client.post('/signup', data={'username': username, 'email': email, 'password': password}, follow_redirects=False)
print('signup_status', resp.status_code)

# Logout (clears session)
resp = client.get('/logout', follow_redirects=False)
print('logout_status', resp.status_code)

# Login
resp = client.post('/login', data={'username': username, 'password': password}, follow_redirects=False)
print('login_status', resp.status_code)

# Access profile
resp2 = client.get('/profile')
print('profile_status', resp2.status_code)
print('profile_contains', username in resp2.get_data(as_text=True))

# Show users file info
with open(users_file,'r',encoding='utf-8') as f:
    users = json.load(f)
print('users_count', len(users))
print('last_user', users[-1] if users else None)
