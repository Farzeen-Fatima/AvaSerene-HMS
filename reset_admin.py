import sqlite3
import bcrypt
import os

db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "hospital.db")

new_password = "admin123"
pw_hash = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())

conn = sqlite3.connect(db_path)
cur = conn.cursor()
cur.execute("UPDATE users SET password=? WHERE username='admin'", (pw_hash,))
conn.commit()
print(f"Rows updated: {cur.rowcount}")
conn.close()

print("✅ Admin password has been reset to: admin123")