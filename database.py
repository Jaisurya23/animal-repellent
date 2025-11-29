import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional

# Path for the SQLite database file
DB_PATH = 'data.db'


def get_conn():
	conn = sqlite3.connect(DB_PATH, check_same_thread=False)
	conn.row_factory = sqlite3.Row
	return conn


def init_db():
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'''
		CREATE TABLE IF NOT EXISTS users (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			name TEXT NOT NULL,
			email TEXT NOT NULL UNIQUE,
			password TEXT NOT NULL,
			location TEXT,
			created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
		)
		'''
	)
	cur.execute(
		'''
		CREATE TABLE IF NOT EXISTS detections (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			animal_type TEXT NOT NULL,
			location TEXT,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
		'''
	)
	cur.execute(
		'''
		CREATE TABLE IF NOT EXISTS alerts (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			message TEXT NOT NULL,
			alert_type TEXT DEFAULT 'warning',
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
		'''
	)
	cur.execute(
		'''
		CREATE TABLE IF NOT EXISTS uploads (
			id INTEGER PRIMARY KEY AUTOINCREMENT,
			user_id INTEGER NOT NULL,
			filename TEXT NOT NULL,
			original_name TEXT,
			timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
			FOREIGN KEY (user_id) REFERENCES users (id)
		)
		'''
	)
	conn.commit()
	
	# Seed dummy data if no detections exist
	cur.execute('SELECT COUNT(*) as cnt FROM detections')
	if cur.fetchone()[0] == 0:
		cur.execute('SELECT id FROM users LIMIT 1')
		user_row = cur.fetchone()
		if user_row:
			user_id = user_row[0]
			for animal_type, location, timestamp in [
				('Wild Dog', 'North Field', '2025-11-26 10:30:00'),
				('Deer', 'Barn Area', '2025-11-26 08:15:00'),
				('Boar', 'East Boundary', '2025-11-25 22:45:00'),
				('Rabbit', 'Vegetable Garden', '2025-11-25 18:20:00'),
			]:
				cur.execute(
					'INSERT INTO detections (user_id, animal_type, location, timestamp) VALUES (?, ?, ?, ?)',
					(user_id, animal_type, location, timestamp)
				)
			conn.commit()
	
	# Seed dummy alerts if none exist
	cur.execute('SELECT COUNT(*) as cnt FROM alerts')
	if cur.fetchone()[0] == 0:
		cur.execute('SELECT id FROM users LIMIT 1')
		user_row = cur.fetchone()
		if user_row:
			user_id = user_row[0]
			for message, alert_type, timestamp in [
				('Wild Dog detected near North Field - Sound alert activated', 'danger', '2025-11-26 10:30:15'),
				('High activity detected - Recommended to check cameras', 'warning', '2025-11-26 09:15:00'),
			]:
				cur.execute(
					'INSERT INTO alerts (user_id, message, alert_type, timestamp) VALUES (?, ?, ?, ?)',
					(user_id, message, alert_type, timestamp)
				)
			conn.commit()
	
	conn.close()


def create_user(name: str, email: str, password: str, location: Optional[str] = None):
	"""Create a new user. Returns the created user row as a dict, or None on failure."""
	pw_hash = generate_password_hash(password)
	try:
		conn = get_conn()
		cur = conn.cursor()
		cur.execute('INSERT INTO users (name, email, password, location) VALUES (?, ?, ?, ?)',
					(name, email, pw_hash, location))
		conn.commit()
		user_id = cur.lastrowid
		cur.execute('SELECT id, name, email, location, created_at FROM users WHERE id = ?', (user_id,))
		row = cur.fetchone()
		conn.close()
		return dict(row) if row else None
	except sqlite3.IntegrityError:
		# likely duplicate email
		return None


def get_user_by_email(email: str):
	conn = get_conn()
	cur = conn.cursor()
	cur.execute('SELECT * FROM users WHERE email = ?', (email,))
	row = cur.fetchone()
	conn.close()
	return dict(row) if row else None


def authenticate_user(email: str, password: str):
	"""Return user dict if credentials are valid, otherwise None."""
	row = get_user_by_email(email)
	if not row:
		return None
	if check_password_hash(row['password'], password):
		# don't return password hash
		return {k: row[k] for k in row.keys() if k != 'password'}
	return None


def get_user_detections(user_id: int):
	"""Get all detections for a user, ordered by most recent first."""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'SELECT id, animal_type, location, timestamp FROM detections WHERE user_id = ? ORDER BY timestamp DESC',
		(user_id,)
	)
	rows = cur.fetchall()
	conn.close()
	return [dict(row) for row in rows]


def add_detection(user_id: int, animal_type: str, location: Optional[str] = None):
	"""Insert a new detection record."""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'INSERT INTO detections (user_id, animal_type, location) VALUES (?, ?, ?)',
		(user_id, animal_type, location)
	)
	conn.commit()
	conn.close()


def get_user_alerts(user_id: int):
	"""Get all alerts for a user, ordered by most recent first."""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'SELECT id, message, alert_type, timestamp FROM alerts WHERE user_id = ? ORDER BY timestamp DESC',
		(user_id,)
	)
	rows = cur.fetchall()
	conn.close()
	return [dict(row) for row in rows]


def add_alert(user_id: int, message: str, alert_type: str = 'warning'):
	"""Insert a new alert record."""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'INSERT INTO alerts (user_id, message, alert_type) VALUES (?, ?, ?)',
		(user_id, message, alert_type)
	)
	conn.commit()
	conn.close()


def get_all_users():
	"""Get all users from the database with their details."""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'SELECT id, name, email, location, created_at FROM users ORDER BY created_at DESC'
	)
	rows = cur.fetchall()
	conn.close()
	return [dict(row) for row in rows]


def add_upload(user_id: int, filename: str, original_name: str                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                    ):
	"""Insert a new upload record."""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'INSERT INTO uploads (user_id, filename, original_name) VALUES (?, ?, ?)',
		(user_id, filename, original_name)
	)
	conn.commit()
	conn.close()


def get_user_uploads(user_id: int):
	"""Get all uploads for a user, ordered by most recent first."""
	conn = get_conn()
	cur = conn.cursor()
	cur.execute(
		'SELECT id, filename, original_name, timestamp FROM uploads WHERE user_id = ? ORDER BY timestamp DESC',
		(user_id,)
	)
	rows = cur.fetchall()
	conn.close()
	return [dict(row) for row in rows]


# Initialize DB on import
init_db()