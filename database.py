import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'bookings.db')


def init_db():


    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            full_name TEXT NOT NUll,
            email TEXT NOT NULL UNIQUE ,
            password TEXT,
            role TEXT,
            department TEXT         
        )               
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS desks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            desk_number TEXT NOT NULL UNIQUE,
            department TEXT NOT NULL, 
            status TEXT NOT NULL DEFAULT 'Available',
            floor INTEGER NOT NULL      
        )               
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL,
            desk_id INTEGER NOT NULL, 
            date TEXT NOT NULL,
            time_slot  TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'confirmed'          
        )               
    ''')    

    conn.commit()
    conn.close()

def seed_db(): 
    # NOTE: Hardcoded password for testing/seed data only.
    # In production, passwords would never be hardcoded in source code.
    hashed = generate_password_hash("Password123")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]

    if count == 0:
        users = [
            ('admin', 'Admin User', 'admin@northumbria.ac.uk', hashed, 'admin', 'IT'),
            ('jsmith', 'John Smith', 'john.smith@northumbria.ac.uk', hashed, 'staff', 'IT'),
            ('sjones', 'Sarah Jones', 'sarah.jones@northumbria.ac.uk', hashed, 'staff', 'IT'),
            ('mtaylor', 'Mike Taylor', 'mike.taylor@northumbria.ac.uk', hashed, 'staff', 'IT'),
            ('ebrown', 'Emma Brown', 'emma.brown@northumbria.ac.uk', hashed, 'staff', 'HR'),
            ('lwilson', 'Laura Wilson', 'laura.wilson@northumbria.ac.uk', hashed, 'staff', 'HR'),
            ('dwhite', 'David White', 'david.white@northumbria.ac.uk', hashed, 'staff', 'HR'),
            ('agreen', 'Alice Green', 'alice.green@northumbria.ac.uk', hashed, 'staff', 'Finance'),
            ('rblack', 'Robert Black', 'robert.black@northumbria.ac.uk', hashed, 'staff', 'Finance'),
            ('cmartin', 'Claire Martin', 'claire.martin@northumbria.ac.uk', hashed, 'staff', 'Finance'),
        ]
        for user in users:
            cursor.execute('''INSERT INTO users (username, full_name, email, password, role, department)
                VALUES (?, ?, ?, ?, ?, ?)''', user)

    cursor.execute('SELECT COUNT(*) FROM desks')
    desk_count = cursor.fetchone()[0]

    if desk_count == 0:
        desks = [
            ('A101', 'IT', 'Available', 1),
            ('A102', 'IT', 'Available', 1),
            ('A103', 'IT', 'Available', 1),
            ('A104', 'IT', 'Available', 1),
            ('A105', 'IT', 'Available', 1),
            ('A106', 'IT', 'Available', 1),
            ('A107', 'IT', 'Available', 1),
            ('A108', 'IT', 'Available', 1),
            ('A109', 'IT', 'Available', 1),
            ('A110', 'IT', 'Available', 1),
            ('B104', 'HR', 'Available', 2),
            ('B105', 'HR', 'Available', 2),
            ('B106', 'HR', 'Available', 2),
            ('B107', 'HR', 'Available', 2),
            ('B108', 'HR', 'Available', 2),
            ('B109', 'HR', 'Available', 2),
            ('B110', 'HR', 'Available', 2),
            ('C103', 'Finance', 'Available', 3),
            ('C104', 'Finance', 'Available', 3),
            ('C105', 'Finance', 'Available', 3),
            ('C106', 'Finance', 'Available', 3),
            ('C107', 'Finance', 'Available', 3),
            ('C108', 'Finance', 'Available', 3),
            ('C109', 'Finance', 'Available', 3),
            ('C110', 'Finance', 'Available', 3),
        ]
        for desk in desks:
            cursor.execute('''INSERT INTO desks (desk_number, department, status, floor)
                VALUES (?, ?, ?, ?)''', desk)
            
    cursor.execute('SELECT COUNT(*) FROM bookings')
    booking_count = cursor.fetchone()[0]

    if booking_count == 0:
        bookings = [
            (2, 1, '2026-06-25', 'Morning', 'confirmed'),
            (3, 2, '2026-06-25', 'Afternoon', 'confirmed'),
            (4, 3, '2026-06-26', 'Fullday', 'confirmed'),
            (2, 4, '2026-06-27', 'Morning', 'confirmed'),
            (3, 5, '2026-06-30', 'Afternoon', 'confirmed'),
            (4, 6, '2026-07-01', 'Morning', 'confirmed'),
            (5, 11, '2026-07-02', 'Fullday', 'confirmed'),
            (6, 12, '2026-07-03', 'Morning', 'confirmed'),
            (7, 13, '2026-07-07', 'Afternoon', 'confirmed'),
            (8, 14, '2026-07-08', 'Morning', 'confirmed'),
            (9, 15, '2026-07-09', 'Afternoon', 'confirmed'),
            (10, 16, '2026-07-10', 'Fullday', 'confirmed'),
            (2, 7, '2026-07-14', 'Morning', 'confirmed'),
            (3, 8, '2026-07-14', 'Afternoon', 'confirmed'),
            (4, 9, '2026-07-15', 'Morning', 'confirmed'),
        ]
        for booking in bookings:
            cursor.execute('''INSERT INTO bookings (user_id, desk_id, date, time_slot, status)
                VALUES (?, ?, ?, ?, ?)''', booking)

    conn.commit()
    conn.close()