import sqlite3
from datetime import date
from database import init_db, seed_db
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import re
import os

app = Flask(__name__)

#Sercret key imported
app.secret_key = os.environ.get('SECRET_KEY', 'northumbria-secret-key')


BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, 'bookings.db')


def get_db():
    if '_database' not in g:
        g._database = sqlite3.connect(DATABASE)
        g._database.row_factory = sqlite3.Row   
    return g._database

@app.teardown_appcontext
def close_connection(exception):
    db = g.pop('_database', None)
    if db:
        db.close()

@app.route("/")
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('desk_booking'))

#Register new user account
@app.route("/register", methods=["GET", "POST"])
def register():

    
    if request.method == "POST":
        db = get_db()
        # Get form data from POST request

        email = request.form["email"]
        password = request.form["password"]
        username = request.form["username"]
        department = request.form["department"]
        full_name = request.form ["full_name"]

        # Validation checks - each tuple contains (condition, error message)
        errors = [
            (not username, "Username cannot be blank"),
            (not password, "Password cannot be blank"),
            (not email, "Email cannot be blank"),
            (not department, "Department cannot be blank"),
            (not full_name, "Name cannot be blank"),
            (len(password) <8, "Password must be at least 8 characters"),
            (not any(c.isupper() for c in password), "Password must contain at least one uppercase letter"),
            (not any(c.islower() for c in password), "Password must contain at least one lowercase letter"),
            (not any(c.isdigit() for c in password), "Password must contain at least one number"),   
        ]
        
        for condition, message in errors: 
            if condition: 
                return render_template ("register.html", error= message, username=username, department=department, email=email )
   
        if not re.search(r"^[a-zA-Z0-9.+]+@northumbria\.ac\.uk$", email,):
            return render_template("register.html", error="Email must be a Northumbria University email",  username=username, department=department, email=email)

        # Check for duplicate username/email in database
        db_checks = [
            (db.execute("SELECT * FROM users WHERE username = ?", 
                            (username,)).fetchone(), "Username is already taken"),
            (db.execute("SELECT * FROM users WHERE email = ?", 
                            (email,)).fetchone(), "Email is already registered"),
        ]

        for result, message in db_checks:
            if result:
                return render_template("register.html", error=message, username=username, department=department, email=email, full_name=full_name,)

        # Hash password before storing - OWASP A07 defence
        hash = generate_password_hash(password)
        db.execute('''INSERT INTO users (username, full_name, email, password, role, department)
        VALUES (?, ?, ?, ?, ?, ?)''',  (username, full_name, email, hash, 'staff', department))
        db.commit()
        flash("Account created successfully. Please log in")
        return redirect(url_for('login'))
                                
    else: 
        return render_template("register.html")
    
def get_user():
    if 'user_id' in session:
        return {
            'name': session['username'],
            'is_admin': session.get('role') =='admin'                
        }
    return None

@app.context_processor
def inject_user():
    return dict(user=get_user())

# Display the logged in user's account details                       
@app.route("/account")
def account():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    user_id = session['user_id'] 
    db = get_db()
    # Fetch the logged in user's details from the database
    account = db.execute ('SELECT * FROM users WHERE id =? ', (user_id,)).fetchone() 
    return render_template("account.html", account=account)
 

@app.route("/password_reset", methods=["GET", "POST"])
def password_reset(): 
    if request.method == "POST":        
        username = request.form["username"]
        email = request.form["email"]
        new_password = request.form["new_password"]

        errors = [
            (not username, "Username cannot be blank"),
            (not email, "Email cannot be blank"),
            (not new_password, "Password cannot be blank"),
            (len(new_password) < 8, "Password must be at least 8 characters"),
            (not any(c.isupper() for c in new_password), "Password must contain at least one uppercase letter"),
            (not any(c.islower() for c in new_password), "Password must contain at least one lowercase letter"),
            (not any(c.isdigit() for c in new_password), "Password must contain at least one number"),
        ]
        
        for condition, message in errors: 
            if condition: 
                return render_template("password_reset.html", error=message)       

        db = get_db()
        user = db.execute("SELECT * FROM users WHERE username =? AND email=?", (username, email)).fetchone()

        if not user: 
            return render_template ("password_reset.html", error="Username or email not found")
        
        if check_password_hash (user['password'], new_password):
            return render_template("password_reset.html", error="New password must be differenet from current password",)
        hashed_password = generate_password_hash(new_password)
        
        db.execute("UPDATE users SET password = ? WHERE id = ? ", 
                       (hashed_password, user['id']))
        db.commit()
        return redirect(url_for('login'))
                                
    else:
        return render_template("password_reset.html")

        
@app.route("/login", methods=["GET", "POST"] )
def login():
        
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]    

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session['user_id'] = user["id"]
            session['username'] = user["username"]        
            session['role'] = user["role"] 
            session['department'] = user["department"]
            if session ['role'] == 'admin':
                return redirect (url_for('admin'))
            else:
                return redirect (url_for("desk_booking")) 
        else:
            return render_template("login.html", error="Invalid email or password")
    else:
        return render_template("login.html")

@app.route("/admin")
def admin():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    if session['role'] != 'admin':
        return redirect(url_for('desk_booking'))    
    db = get_db()
    desks = db.execute ('SELECT * FROM desks').fetchall()
    users = db.execute ('SELECT * FROM users').fetchall()
    booking = db.execute ('''SELECT bookings.*, users.username, desks.desk_number
                        FROM bookings
                        JOIN users ON bookings.user_id = users.id
                        JOIN desks ON bookings.desk_id = desks.id''').fetchall()
    return render_template ('admin.html', desks=desks, users=users, bookings=booking)
 
@app.route("/admin/edit_user/<int:user_id>", methods=["GET", "POST"] )

def admin_edit_user(user_id):
    if 'user_id' not in session:
        return redirect(url_for("login"))
    if session['role'] != 'admin':
        return redirect(url_for('desk_booking'))
    
    db = get_db()   
    if request.method == "POST":  

        username =  request.form ["username"]
        email = request.form ["email"]
        department = request.form ["department"]
        password = request.form ["password"]
        hashed_password = generate_password_hash(password)

        db.execute("UPDATE users  SET username =?, email =?,department =?, password =? WHERE id =?",
                       (username, email, department, hashed_password, user_id))
        db.commit()
        return redirect (url_for("admin"))
    
    else:
        user = db.execute("SELECT * FROM users WHERE id =?",  (user_id,)).fetchone()
        if user['role'] == 'admin':
            flash("Cannot delete an admin user")
            return redirect(url_for('admin'))
       
        return render_template ("edit_user.html", edit_user=user)
    
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/desks")
def desk_booking():    
    if 'user_id' not in session:
        return redirect(url_for('login')) 
       
    db = get_db()
    department = session ['department']
    selected_date = request.args.get('date', date.today().isoformat())
    desks = db.execute('SELECT * FROM desks WHERE department =?', (department,)).fetchall()
    booked_slots = db.execute('SELECT * FROM bookings WHERE date =? AND status =?', 
                              (selected_date, 'confirmed')).fetchall()
    #Creates a set so desks are not duplicated
    booked = set()
    for bookings in booked_slots:
        booked.add((bookings['desk_id'], bookings['time_slot']))

    # Full Day blocking logic
    extra = set()
    for desk_id, slot in booked:
        if slot == 'Fullday':
            extra.add((desk_id, 'Morning'))
            extra.add((desk_id, 'Afternoon'))
    for desk in desks:
        if (desk["id"], 'Morning') in booked and (desk["id"], 'Afternoon') in booked:
            extra.add((desk["id"], 'Fullday'))
    booked.update(extra)

    return render_template("desks.html", desks=desks, department=department, date=selected_date, booked=booked)


@app.route("/mybookings")
def my_bookings():
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    db = get_db()
    user_id = session['user_id'] 
    bookings = db.execute("SELECT bookings.*, desks.desk_number FROM bookings " 
    "JOIN desks ON bookings.desk_id= desks.id " 
    "WHERE bookings.user_id = ? " "AND bookings.status != 'cancelled'", 
    (user_id,)).fetchall()

    return render_template ("mybookings.html", bookings=bookings)

@app.route("/edit_bookings/<int:booking_id>", methods=["GET", "POST"])
def edit_bookings(booking_id):
    if 'user_id' not in session: 
        return redirect(url_for('login'))
    
    db = get_db()
    if request.method == "POST":
    
        date = request.form ["date"]
        time_slot = request.form ["time_slot"]
        desk = request.form ["desk_id"]

        db.execute("UPDATE bookings SET date=?, time_slot=?, desk_id=? WHERE id = ? AND user_id = ?", 
                       (date, time_slot, desk, booking_id, session['user_id']))
        db.commit()
        flash ("Booking updated successfully")
        return redirect (url_for ('my_bookings'))
    # GETS the infomation if the data is not in present in the datbase
    else: 

        booking = db.execute('''SELECT bookings.*, desks.desk_number 
                             FROM bookings
                             JOIN desks on bookings.desk_id = desks.id
                             WHERE bookings.id =? AND bookings.user_id =?
                             ''',
                       (booking_id, session['user_id'])).fetchone()
        
        selected_date = request.args.get('date', booking["date"])
        desks = db.execute("SELECT * FROM desks WHERE department =?", (session['department'],)).fetchall()

        booked_slots = db.execute('SELECT * FROM bookings WHERE date =? AND status =? AND id != ?', 
                       (selected_date, 'confirmed', booking_id)).fetchall()
        booked = set()
        for bookings in booked_slots:
            booked.add((bookings["desk_id"], bookings["time_slot"]))

        # Full Day blocking logic
        extra = set()
        for desk_id, slot in booked:
            if slot == 'Fullday':
                extra.add((desk_id, 'Morning'))
                extra.add((desk_id, 'Afternoon'))
        for desk in desks:
            if (desk["id"], 'Morning') in booked and (desk["id"], 'Afternoon') in booked:
                extra.add((desk["id"], 'Fullday'))
        booked.update(extra)

        return render_template("edit_bookings.html", booking=booking, desks=desks, booked=booked, date=selected_date)


@app.route("/rebook/<int:booking_id>/<int:desk_id>/<time_slot>/<date>")
def rebook(booking_id, desk_id, time_slot, date):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    # Cancel old booking
    db.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?", (booking_id,))
    # Create new booking
    db.execute('''INSERT INTO bookings (user_id, desk_id, date, time_slot, status)
        VALUES (?, ?, ?, ?, ?)''', 
        (session['user_id'], desk_id, date, time_slot, 'confirmed'))
    db.commit()
    flash("Booking updated successfully")
    return redirect(url_for('my_bookings'))

@app.route("/book/<int:desk_id>", methods=["GET", "POST"])
def booking(desk_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == "POST":
        date = request.form["date"]
        time_slot = request.form["time_slot"]
        user_id = session['user_id']
        conflict = db.execute("""SELECT * FROM bookings 
            WHERE desk_id =? AND date =? AND time_slot =? AND status = 'confirmed'""", 
            (desk_id, date, time_slot,)).fetchone()
        desk = db.execute("SELECT * FROM desks WHERE id = ?", (desk_id,)).fetchone()
      

        if conflict: 
            return render_template('book.html', desk_id=desk_id, desk_number=desk["desk_number"], 
                                error="This desk is already booked for that date and time slot.",
                                date=date, time_slot=time_slot)
        else:
                  
            db.execute('''INSERT INTO bookings (user_id, desk_id, date, time_slot, status)
                VALUES (?, ?, ?, ?, ?)''', 
                (user_id, desk_id, date, time_slot, 'confirmed'))
            db.commit()
            flash("Bookings Confirmed")
            return render_template('book.html', desk_id=desk_id, desk_number=desk["desk_number"], success="Booking confirmed!", date=date ,time_slot=time_slot)
    
    else:
        desk = db.execute('SELECT * FROM desks WHERE id = ?', (desk_id,)).fetchone()
        date = request.args.get('date')
        time_slot = request.args.get('time_slot')
        return render_template('book.html', desk_id=desk_id, desk_number=desk["desk_number"], date=date, time_slot=time_slot)
        

@app.route("/cancel/<int:booking_id>")
def cancel(booking_id):

    if 'user_id' not in session: 
        return redirect(url_for('desk_booking'))
    db = get_db()

    booking = db.execute('SELECT * FROM bookings WHERE id = ?',
                    (booking_id,)).fetchone() 
    desk_id = booking["desk_id"]
    db.execute("UPDATE bookings SET status = 'cancelled' WHERE id = ?",
                    (booking_id,))
    db.execute("UPDATE desks SET status = 'Available' WHERE id = ?", 
                   (desk_id,) )
    db.commit()
    flash("Booking cancelled successfully")
    return redirect(url_for("my_bookings"))

@app.route("/admin/delete_desk/<int:desk_id>")
def admin_delete_desk(desk_id):

    if 'user_id' not in session:
        return redirect (url_for('login'))
    if session['role'] != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    db.execute("DELETE FROM desks WHERE id = ?", 
                   (desk_id,))
    db.commit()
    flash ("Desk has been deleted")
    return redirect(url_for('admin'))


@app.route("/admin/delete_user/<int:user_id>")
def admin_delete_user(user_id):

    if 'user_id' not in session:
        return redirect (url_for('login'))
    if session['role'] != 'admin':
        return redirect(url_for('login'))
    
    db = get_db()
    user = db.execute("SELECT * FROM users WHERE id = ?", 
                   (user_id,)).fetchone()
    if user["role"] == 'admin':
        flash("Cannot delete an admin user")
        return redirect(url_for('admin'))
    db.execute("DELETE FROM users WHERE id = ?", 
                   (user_id,))
    db.commit()
    flash ("User has been deleted")
    return redirect(url_for('admin'))

@app.route("/admin/delete_booking/<int:booking_id>")
def admin_delete_booking(booking_id):
    if 'user_id' not in session:
        return redirect (url_for('login'))
    if session['role'] != 'admin':
        return redirect (url_for('login'))
    db = get_db()
    db.execute ("DELETE FROM bookings WHERE id = ?", 
                    (booking_id,))
    db.commit()

    flash ("Bookings has been deleted")
    return redirect (url_for('admin'))

@app.route("/admin/add_desk", methods=["GET", "POST"])
def admin_add_desk():
    if 'user_id' not in session:
        return redirect (url_for('login'))
    if session ['role'] != 'admin':
        return redirect (url_for('login'))
    db = get_db()
    if request.method == "POST":
        desk_number = request.form['desk_number']
        department = request.form['department']
        floor = request.form ['floor']

        if not desk_number or not floor: 
            return render_template ('add_desk.html', error ="All fields are required")

        existing = db.execute ('SELECT * FROM desks WHERE desk_number = ?',
                               (desk_number,)).fetchone()
        if existing:
            return render_template ('add_desk.html', error="A desk with that number already exists")
        
       
        db.execute('''INSERT INTO desks (desk_number, department, status,  floor)
        VALUES (?,?,?,?)''', (desk_number, department, 'Available',  floor))
        db.commit()
        flash ("Desk created")
        return redirect (url_for('admin'))

    else:
        return render_template ("add_desk.html")
    
@app.route("/admin/add_user", methods=["GET", "POST"])
def admin_add_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if session['role'] != 'admin':
        return redirect(url_for('login'))
    db = get_db()
    if request.method == "POST":
        username = request.form['username']
        full_name = request.form['full_name']
        email = request.form['email']
        department = request.form['department']
        password = request.form['password']
        role = request.form['role']

        if not username or not full_name or not email or not department or not password:
            return render_template('add_user.html', error="All fields are required.")

        existing = db.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
        if existing:
            return render_template('add_user.html', error="A user with that email already exists.")

        hashed = generate_password_hash(password)
        db.execute('''INSERT INTO users (username, full_name, email, password, role, department)
        VALUES (?, ?, ?, ?, ?, ?)''', (username, full_name, email, hashed, role, department))
        db.commit()
        flash("User created successfully")
        return redirect(url_for('admin'))

    else:
        return render_template("add_user.html")    

@app.route("/admin/edit_desk/<int:desk_id>", methods=["GET", "POST"])
def admin_edit_desk(desk_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    if request.method == "POST":
        desk_number = request.form["desk_number"]
        department = request.form ["department"]
        floor = request.form ["floor"]

        desk = db.execute("SELECT * FROM desks WHERE id=?",
                          (desk_id,)).fetchone()
        if not desk_number or not floor: 
            return render_template ('edit_desk.html', desk=desk, error ="All fields are required")
                    
        db.execute("UPDATE desks SET desk_number=?, department=?, floor=? WHERE id=?", 
                       (desk_number, department, floor, desk_id)) 
        db.commit()
        flash ("Desk updated successfully")
        return redirect (url_for('admin'))

    else:   
        desk = db.execute("SELECT * FROM desks WHERE id = ?", 
                       (desk_id,)).fetchone()

        return render_template ("edit_desk.html", desk = desk)
   

if __name__ == "__main__":
    init_db()
    seed_db()
    app.run(debug=True)