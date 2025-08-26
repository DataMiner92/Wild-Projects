import sqlite3
from datetime import datetime
import random
import string
import secrets
import re
from tkinter import *
from tkinter import ttk, messagebox, filedialog
from tkcalendar import DateEntry
import os
import json
import time
import uuid
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import csv


import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# --- Splash Screen and Main Start Functions ---



try:
    import pandas as pd
except ImportError:
    pd = None  # Excel export will be disabled if pandas is not installed

def show_welcome_and_start():
    welcome = Tk()
    welcome.title("Welcome to HMS Pro 2025")
    welcome.geometry("500x500")
    welcome.configure(bg="#3E3F33")
    welcome.resizable(True, True)

    # Animated welcome text
    welcome_text = "Welcome to HMS Pro 2025\n\nThe Management Software.\n\n Created For You..."
    animated_label = Label(
        welcome,
        text="",
        font=("Garamond", 16, "bold"),
        bg="#3E3F33",
        fg="white",
        justify="center"
    )
    animated_label.pack(expand=True, pady=40)

    def animate_text(idx=0):
        animated_label.config(text=welcome_text[:idx])
        if idx < len(welcome_text):
            welcome.after(40, animate_text, idx + 1)

    animate_text()

    Label(
        welcome,
        text="© 2025 J-FirstHand Software Ltd\n \n Contact Us: jf-software@gmail.com \n All rights reserved.",
        font=("Garamond", 10, "italic"),
        bg="#3E3F33",
        fg="white"
    ).pack(side="bottom", pady=10)

    def proceed():
        welcome.destroy()
        # Do NOT create another Tk() here, just continue to main()
        

    Button(
        welcome,
        text="Continue",
        font=("Garamond", 14),
        bg="powderblue",
        fg="navy",
        command=proceed,
        width=15
    ).pack(pady=10)

    # Optionally auto-continue after 3 seconds:
    # welcome.after(3000, proceed)

    welcome.mainloop()


class HospitalManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Hospital Management System")
        self.root.geometry("1200x700")
        self.root.resizable(TRUE, TRUE)
        self.root.configure(bg="white")

        self.sidebar_expanded = True
        self.sidebar_width = 200

       

        self.session_token = None
        self.session_expiry = None
        self.session_timeout_minutes = 30  # Session expires after 30 minutes of inactivity
        self.current_user = None
       
        self.apply_theme()
        # Initialize database
        self.initialize_database()
        
        # Create login frame
        self.create_login_frame()
        
        # Initialize main application (will be created after login)
        self.main_frame = None

        # Initialize status variable
        # Status bar at the bottom
        self.status_var = StringVar()
        self.status_var.set("Ready")
        self.status_bar = Label(self.root, textvariable=self.status_var, bd=1, relief=SUNKEN, anchor=W, font=("Arial", 10), bg="#f0f0f0")
        self.status_bar.pack(side=BOTTOM, fill=X)
    
    def start_session(self, username):
        self.session_token = str(uuid.uuid4())
        self.session_expiry = time.time() + self.session_timeout_minutes * 60
        self.current_user = username

    def is_session_active(self):
        return self.session_token is not None and time.time() < self.session_expiry

    def refresh_session(self):
        if self.session_token:
            self.session_expiry = time.time() + self.session_timeout_minutes * 60

    def end_session(self):
        self.session_token = None
        self.session_expiry = None
        self.current_user = None
    

    def apply_theme(self):
    # Apply a modern theme
        style = ttk.Style()
        style.theme_use("clam")  # Use the 'clam' theme for a modern look

        # Customize button styles
        style.configure("TButton", font=("Arial", 12), padding=5)
        style.configure("TLabel", font=("Arial", 12))
        style.configure("TEntry", font=("Arial", 12))
        style.configure("TCombobox", font=("Arial", 12))
        style.configure("Treeview", background="#C1F30E", fieldbackground="#F7D0D0", foreground="navy")
        style.map("Treeview", background=[("selected", "#494040")])
    
    def initialize_database(self):
        try:
            # Initialize database connection and cursor
            self.conn = sqlite3.connect("afya.db")
            self.cursor = self.conn.cursor()
        except sqlite3.Error as e:
            print(f"An error occurred while connecting to the database: {e}")

        try:
            self.cursor.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Already exists
        # Always create tables if not exist
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                age INTEGER CHECK(age > 0 AND age < 120),
                gender TEXT CHECK(gender IN ('M', 'F', 'Other')),
                contact TEXT NOT NULL UNIQUE,
                department TEXT NOT NULL,
                doctor_id INTEGER,
                admission_date TEXT NOT NULL,
                discharge_date TEXT,
                payment_method TEXT,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_journey (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                action TEXT NOT NULL,
                details TEXT,
                timestamp TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Admin', 'Doctor', 'Receptionist', 'Pharmacist'))
            )
        """)

        # Add a default admin user if no users exist
        self.cursor.execute("SELECT COUNT(*) FROM users")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("""
                INSERT INTO users (username, password, role, must_change_password)
                VALUES ('Admin', 'admin123', 'Admin', 1)
            """)
            self.conn.commit()

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                specialization TEXT NOT NULL,
                contact TEXT NOT NULL UNIQUE,
                email TEXT UNIQUE,
                availability TEXT NOT NULL,
                department TEXT NOT NULL
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS departments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                head_doctor_id INTEGER,
                description TEXT,
                FOREIGN KEY (head_doctor_id) REFERENCES doctors(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS pharmacy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_name TEXT NOT NULL UNIQUE,
                stock INTEGER NOT NULL CHECK(stock >= 0),
                price REAL NOT NULL CHECK(price > 0),
                expiry_date TEXT,
                supplier TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_date TEXT NOT NULL,
                status TEXT DEFAULT 'Scheduled',
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS issued_medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                medicine_id INTEGER NOT NULL,
                issue_date TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (medicine_id) REFERENCES pharmacy(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS admissions_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                admission_date TEXT NOT NULL,
                discharge_date TEXT,
                department TEXT NOT NULL,
                doctor_id INTEGER,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (doctor_id) REFERENCES doctors(id)
            )
        """)

        # Create billing table with the description column
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS billing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                date TEXT NOT NULL,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS medical_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                diagnosis TEXT,
                allergies TEXT,
                visit_date TEXT NOT NULL,
                notes TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id)
            )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Available',
                location TEXT,
                assigned_to TEXT,
                notes TEXT
            )
        """)

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS beds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ward TEXT NOT NULL,
            bed_number TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Available', -- Available, Occupied, Maintenance
            patient_id INTEGER,
            admission_date TEXT,
            discharge_date TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)
        
        self.cursor.execute("""
                CREATE TABLE IF NOT EXISTS staff_schedule (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    staff_id INTEGER NOT NULL,
                    staff_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    shift_date TEXT NOT NULL,
                    shift_type TEXT NOT NULL,
                    leave INTEGER DEFAULT 0,
                    notes TEXT
                )
            """)
        
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS laboratory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                test_type TEXT NOT NULL,
                request_date TEXT NOT NULL,
                result_date TEXT,
                result TEXT,
                notes TEXT,
                status TEXT DEFAULT 'Pending',
                FOREIGN KEY (patient_id) REFERENCES patients(id)
                )
            """)
        
        # Insurance Providers
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance_providers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                contact TEXT,
                email TEXT,
                address TEXT
            )
        """)
        # Insurance Claims
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS insurance_claims (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                provider_id INTEGER NOT NULL,
                claim_date TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Pending',
                description TEXT,
                response TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients(id),
                FOREIGN KEY (provider_id) REFERENCES insurance_providers(id)
            )
        """)

        # Add patient_type to patients table if not exists
        try:
            self.cursor.execute("ALTER TABLE patients ADD COLUMN patient_type TEXT DEFAULT 'Outpatient'")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Already exists

        self.conn.commit()

        def ensure_billing_date_column(self):
            try:
                self.cursor.execute("ALTER TABLE billing ADD COLUMN date TEXT")
                self.conn.commit()
            except sqlite3.OperationalError:
                # Column already exists
                pass

             

    def create_login_frame(self):
        # Destroy any existing login frame
        if hasattr(self, "login_frame") and self.login_frame.winfo_exists():
            self.login_frame.destroy()

        # Use a larger frame to accommodate all buttons and widgets
        self.login_frame = Frame(self.root, bg="#F5C9C9")
        self.login_frame.place(relx=0.5, rely=0.5, anchor=CENTER, width=500, height=500)

        # Optionally, make the frame expand with the window
        self.login_frame.pack_propagate(False)

        header_frame = Frame(self.login_frame, bg="orange")
        header_frame.pack(fill=X)
        Label(header_frame, text="HMS Pro 2025", font=("Arial", 24, "bold"), bg="orange").pack(pady=10)

        # Load background image
        bg_image = PhotoImage(file="C:/Users/user/Desktop/afya.png")
        bg_label = Label(self.login_frame, image=bg_image)
        # Make the image fill the frame
        bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        bg_label.image = bg_image  # Keep a reference to avoid garbage collection

        # Expand the login container height to accommodate all buttons and widgets
        # Add a header label on top
        

        login_container = Frame(self.login_frame, highlightbackground="orange", highlightthickness=1)
        # Set rounded corners for the container (requires ttkbootstrap or custom styling)
        Label(self.login_frame, text="Welcome..", font=("Garamond", 25, "bold"), fg="navy").grid(row=0, column=1, padx=10, pady=10, sticky=W)
        login_container.config(borderwidth=2, relief="ridge")
        # Set a fixed width and increased height (e.g., width=350, height=320)
        login_container.place(relx=0.5, rely=0.5, anchor=CENTER, width=400, height=300)

        Label(login_container, text="Username:", font=("Arial", 12)).grid(row=0, column=0, padx=10, pady=10, sticky=W)
        
        # Fetch usernames from the database
        self.cursor.execute("SELECT username FROM users")
        usernames = [row[0] for row in self.cursor.fetchall()]
        self.username_var = StringVar()
        self.username_dropdown = ttk.Combobox(login_container, textvariable=self.username_var, values=usernames, state="readonly", font=("Arial", 12))
        self.username_dropdown.grid(row=0, column=1, padx=10, pady=10)
        self.username_dropdown.set("Select Username")  # Inline text for username dropdown
        if usernames:
            self.username_dropdown.current(0)

        Label(login_container, text="Password:", font=("Arial", 12)).grid(row=1, column=0, padx=10, pady=10, sticky=W)
        self.password_entry = Entry(login_container, font=("Arial", 12), show="*")
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        self.password_entry.insert(0, "Enter Password")  # Inline text for password entry
        self.password_entry.bind("<FocusIn>", lambda event: self.password_entry.delete(0, END))  # Clear inline text on focus

        self.captcha_num1 = random.randint(1, 10)
        self.captcha_num2 = random.randint(1, 10)
        self.captcha_answer = self.captcha_num1 + self.captcha_num2

        Label(login_container, text=f"Captcha: {self.captcha_num1} + {self.captcha_num2} = ?", font=("Arial", 12), bg="#f1f1f1").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        self.captcha_entry = Entry(login_container, font=("Arial", 12))
        self.captcha_entry.grid(row=2, column=1, padx=10, pady=10)

        # Add "Remember Me" checkbox
        self.remember_me_var = BooleanVar()
        remember_me_checkbox = Checkbutton(login_container, text="Remember Me", variable=self.remember_me_var, bg="#f1f1f1", font=("Arial", 10))
        remember_me_checkbox.grid(row=3, column=0, columnspan=2, pady=5)

        Button(login_container, text="Login", bg="orange", font=("Arial", 12), command=self.login, width=15).grid(row=4, column=0, columnspan=2, pady=20)

        

    def login(self):
        username = self.username_var.get()
        password = self.password_entry.get()
        captcha_input = self.captcha_entry.get()

        # Validate CAPTCHA
        try:
            captcha_input = int(captcha_input)
        except ValueError:
            messagebox.showerror("CAPTCHA Error", "CAPTCHA must be a number")
            return

        if captcha_input != self.captcha_answer:
            if not hasattr(self, 'captcha_attempts'):
                self.captcha_attempts = 0
            self.captcha_attempts += 1

            # Log failed CAPTCHA attempt
            self.log_action("Failed CAPTCHA", f"Username: {username}, Attempt: {self.captcha_attempts}")

            if self.captcha_attempts >= 2:
                self.log_action("Account Lockout", f"Username: {username} locked out after failed CAPTCHA")
                messagebox.showerror("CAPTCHA Error", "Too many failed CAPTCHA attempts. Please try again later.")
                self.notify_admins(f"Account lockout for username: {username} due to repeated failed CAPTCHA.")
                self.login_frame.destroy()
                self.create_login_frame()  # Reset login frame
                return

            messagebox.showerror("CAPTCHA Error", f"Incorrect CAPTCHA. You have {2 - self.captcha_attempts} attempt(s) left.")
            return

        try:
            self.cursor.execute("SELECT role, must_change_password FROM users WHERE username = ? AND password = ?", (username, password))
            result = self.cursor.fetchone()

            if result:
                self.user_role = result[0]
                must_change = result[1]
                self.start_session(username)
                self.log_action("Login Success", f"Username: {username}")
                self.login_frame.destroy()
                if must_change:
                    self.force_password_change(username)
                else:
                    # Show flagged login attempts if admin
                    if self.user_role == "Admin":
                        self.show_flagged_login_alerts()
                    self.create_main_application()
            else:
                # Log failed login attempt
                if not hasattr(self, 'failed_login_attempts'):
                    self.failed_login_attempts = {}
                self.failed_login_attempts[username] = self.failed_login_attempts.get(username, 0) + 1
                self.log_action("Failed Login", f"Username: {username}, Attempt: {self.failed_login_attempts[username]}")

                # If more than 3 failed attempts, notify admin
                if self.failed_login_attempts[username] >= 3:
                    self.notify_admins(f"Suspicious activity: 3+ failed login attempts for username: {username}")
                    messagebox.showerror("Login Failed", "Too many failed login attempts. Admin has been notified.")
                else:
                    messagebox.showerror("Login Failed", "Invalid username or password")

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")

    def force_password_change(self, username):
        dialog = Toplevel(self.root)
        dialog.title("Change Password (First Login)")
        dialog.geometry("400x250")
        dialog.resizable(False, False)

        Label(dialog, text="Set New Password:", font=("Arial", 12)).pack(pady=10)
        new_pass_entry = Entry(dialog, show="*")
        new_pass_entry.pack(pady=5)
        Label(dialog, text="Confirm New Password:", font=("Arial", 12)).pack(pady=10)
        confirm_pass_entry = Entry(dialog, show="*")
        confirm_pass_entry.pack(pady=5)

        def save_new_password():
            new_pass = new_pass_entry.get()
            confirm_pass = confirm_pass_entry.get()
            if not new_pass or not confirm_pass:
                messagebox.showerror("Error", "All fields are required")
                return
            if new_pass != confirm_pass:
                messagebox.showerror("Error", "Passwords do not match")
                return
            if len(new_pass) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return
            # Update password and clear must_change_password
            self.cursor.execute("UPDATE users SET password=?, must_change_password=0 WHERE username=?", (new_pass, username))
            self.conn.commit()
            messagebox.showinfo("Success", "Password changed successfully. Please log in again.")
            dialog.destroy()
            self.create_login_frame()

        # Add some padding to the dialog to ensure the button is visible
        dialog.update_idletasks()
        dialog.geometry(f"{dialog.winfo_width()}x{dialog.winfo_height()+40}")

        Button(dialog, text="Save", command=save_new_password).pack(pady=20)
        
    def notify_admins(self, message):
    # Log the notification in audit logs
            self.log_action("Security Alert", message)
            # Optionally, show a popup if an admin is logged in
            if hasattr(self, "user_role") and self.user_role == "Admin":
                messagebox.showwarning("Security Alert", message)

    def bind_enter_key(self):
            self.root.bind('<Return>', lambda event: self.login())

    def sensitive_action(self):
            if not self.is_session_active():
                messagebox.showwarning("Session Expired", "Your session has expired. Please log in again.")
                self.end_session()
                self.create_login_frame()
                return
            self.refresh_session()
            # ...proceed with action...
            
            
    def create_main_application(self):
        self.main_frame = Frame(self.root)
        self.main_frame.pack(fill=BOTH, expand=True)

        # Add background image
        # Add a static image to the main frame
        bg_image = PhotoImage(file="C:/Users/user/Desktop/afya.png")
        bg_label = Label(self.main_frame, image=bg_image)
        bg_label.place(relwidth=1, relheight=1)
        bg_label.image = bg_image  # Keep a reference to avoid garbage collection

        # Create menu bar
        self.create_menu_bar()

          # Sidebar
        # Collapsible sidebar
        self.sidebar = Frame(self.main_frame, bg="#222", width=self.sidebar_width)
        self.sidebar.pack(side=LEFT, fill=Y)
        self.sidebar.pack_propagate(False)

        # Toggle/collapse button at the top of the sidebar
        toggle_btn = Button(
            self.sidebar,
            text="≡",  # Hamburger icon
            bg="#222",
            fg="white",
            font=("Arial", 16, "bold"),
            relief=FLAT,
            command=self.toggle_sidebar
        )
        toggle_btn.pack(anchor="nw", padx=5, pady=5)

        # Store sidebar menu buttons for toggling
        self.menu_buttons = []

        # Main content area
        self.content_area = Frame(self.main_frame, bg="white")
        self.content_area.pack(side=RIGHT, fill=BOTH, expand=True)

        # Create the notebook for tabs
        self.notebook = ttk.Notebook(self.content_area)
        self.notebook.pack(fill=BOTH, expand=True)

        # Dictionary to hold module frames
        self.module_frames = {}

        # Define modules and their display names
        # Define modules and their display names, with access roles
        modules = [
            ("Dashboard", self.create_dashboard_tab, ["Admin", "Doctor", "Receptionist", "Pharmacist"]),
            ("Patients", self.create_patient_tab, ["Admin", "Doctor", "Receptionist"]),
            ("Appointments", self.create_appointment_tab, ["Admin", "Doctor", "Receptionist"]),
            ("Admissions", self.create_admissions_tab, ["Admin", "Doctor", "Receptionist"]),
            ("Doctors", self.create_doctor_tab, ["Admin", "Doctor"]),
            ("Laboratory", self.create_laboratory_tab, ["Admin", "Doctor", "Receptionist"]),
            ("Pharmacy", self.create_pharmacy_tab, ["Admin", "Pharmacist"]),
            ("Beds", self.create_bed_tab, ["Admin", "Doctor", "Receptionist"]),
            ("Departments", self.create_department_tab, ["Admin"]),
            ("Billing", self.create_billing_tab, ["Admin", "Receptionist"]),
            ("Users", self.create_user_management_tab, ["Admin"]),
            ("Assets", self.create_asset_tab, ["Admin"]),
            ("Staff Schedule", self.create_staff_schedule_tab, ["Admin"]),
            ("Insurance", self.create_insurance_tab, ["Admin", "Receptionist"]),
            ("Reports", self.create_report_tab, ["Admin", "Doctor"]),
            ("Audit Logs", self.create_audit_logs_tab, ["Admin"]),
        ]

        # Sidebar buttons (only show modules allowed for this user)
        self.menu_buttons = []
        for mod_name, mod_func, roles in modules:
            if hasattr(self, "user_role") and self.user_role in roles:
                btn = Button(self.sidebar, text=mod_name, bg="#222", fg="white", font=("Arial", 12), relief=FLAT,
                     anchor="w", command=lambda f=mod_func, n=mod_name: self.show_module(n, f))
            btn.pack(fill=X, padx=10, pady=2)
            self.menu_buttons.append(btn)

        # Show the first allowed module by default
        for mod_name, mod_func, roles in modules:
            if hasattr(self, "user_role") and self.user_role in roles:
                self.show_module(mod_name, mod_func)
            break

        # Sidebar buttons
        for mod_name, mod_func in modules:
            btn = Button(self.sidebar, text=mod_name, bg="#222", fg="white", font=("Arial", 12), relief=FLAT,
                         anchor="w", command=lambda f=mod_func, n=mod_name: self.show_module(n, f))
            btn.pack(fill=X, padx=10, pady=2)

        # Show the first module by default
        self.show_module("Dashboard", self.create_dashboard_tab)

    def show_module(self, module_name, create_func):
        # Hide all module frames
        for frame in self.module_frames.values():
            frame.pack_forget()
        # Create frame if not already created
        if module_name not in self.module_frames:
            frame = Frame(self.content_area, bg="white")
            frame.pack(fill=BOTH, expand=True)
            self.module_frames[module_name] = frame
            # Call the module's creation function
            create_func()
        else:
            self.module_frames[module_name].pack(fill=BOTH, expand=True)
    def toggle_sidebar(self):
        if self.sidebar_expanded:
            self.sidebar.config(width=40)
            for btn in self.menu_buttons:
                btn.pack_forget()
            self.sidebar_expanded = False
        else:
            self.sidebar.config(width=self.sidebar_width)
            for btn in self.menu_buttons:
                btn.pack(fill=X, padx=10, pady=2)
            self.sidebar_expanded = True

        

    def create_user_management_tab(self):
        if self.user_role != "Admin":
            return  # Only admins can access this tab

        self.user_tab = Frame(self.notebook)
        self.notebook.add(self.user_tab, text="User Management")

        # Create user management widgets
        self.user_tree = ttk.Treeview(self.user_tab, columns=("ID", "Username", "Role"), show="headings")
        self.user_tree.heading("ID", text="ID")
        self.user_tree.heading("Username", text="Username")
        self.user_tree.heading("Role", text="Role")

        self.user_tree.column("ID", width=50)
        self.user_tree.column("Username", width=150)
        self.user_tree.column("Role", width=100)

        self.user_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Buttons frame
        button_frame = Frame(self.user_tab)
        button_frame.pack(fill=X, padx=10, pady=10)

        Button(button_frame, text="Add User", command=self.show_add_user_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Edit User", command=self.show_edit_user_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Delete User", command=self.delete_user).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_user_list).pack(side=LEFT, padx=5)
    
    def delete_user(self):
            selected_item = self.user_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a user to delete")
                return
    
            user_data = self.user_tree.item(selected_item)['values']
            user_id = user_data[0]
    
            confirmation = messagebox.askyesno("Confirm", f"Are you sure you want to delete user {user_data[1]}?")
            if confirmation:
                try:
                    self.cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                    self.conn.commit()
                    messagebox.showinfo("Success", "User deleted successfully")
                    self.refresh_user_list()
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Failed to delete user: {e}")
    
    def show_edit_user_dialog(self):
            selected_item = self.user_tree.selection()
            if not selected_item:
                messagebox.showwarning("Warning", "Please select a user to edit")
                return
    
            user_data = self.user_tree.item(selected_item)['values']
    
            dialog = Toplevel(self.root)
            dialog.title("Edit User")
            dialog.geometry("400x300")
            dialog.resizable(True, True)
    
            Label(dialog, text="Username:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
            username_entry = Entry(dialog)
            username_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
            username_entry.insert(0, user_data[1])
    
            Label(dialog, text="Role:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
            role_var = StringVar(value=user_data[2])
            role_dropdown = ttk.Combobox(dialog, textvariable=role_var, values=["Admin", "Doctor", "Receptionist", "Pharmacist"], state="readonly")
            role_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
    
            Button(dialog, text="Save", command=lambda: self.update_user(
                user_data[0],  # user_id
                username_entry.get(),
                role_var.get(),
                dialog
            )).grid(row=2, column=0, columnspan=2, pady=20)    
    
    def update_user(self, user_id, username, role, dialog):
            if not username or not role:
                messagebox.showerror("Error", "All fields are required")
                return
    
            try:
                self.cursor.execute("UPDATE users SET username = ?, role = ? WHERE id = ?", (username, role, user_id))
                self.conn.commit()
                messagebox.showinfo("Success", "User updated successfully")
                dialog.destroy()
                self.refresh_user_list()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists")

        # Load initial user data
            self.refresh_user_list()    

    def refresh_user_list(self):
        # Clear existing data
        for item in self.user_tree.get_children():
            self.user_tree.delete(item)

        # Fetch users
        self.cursor.execute("SELECT id, username, role FROM users")
        users = self.cursor.fetchall()

        # Populate the table
        for user in users:
            self.user_tree.insert("", END, values=user)

    def show_add_user_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add New User")
        dialog.geometry("400x300")
        dialog.resizable(True, True)

        Label(dialog, text="Username:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        username_entry = Entry(dialog)
        username_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Password:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        password_entry = Entry(dialog, show="*")
        password_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Role:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        role_var = StringVar(value="Receptionist")
        role_dropdown = ttk.Combobox(dialog, textvariable=role_var, values=["Admin", "Doctor", "Receptionist", "Pharmacist"], state="readonly")
        role_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Save", command=lambda: self.save_user(
            username_entry.get(),
            password_entry.get(),
            role_var.get(),
            dialog
        )).grid(row=3, column=0, columnspan=2, pady=20)

    def save_user(self, username, password, role, dialog):
        if not username or not password or not role:
            messagebox.showerror("Error", "All fields are required")
            return

        try:
            self.cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", (username, password, role))
            self.conn.commit()
            messagebox.showinfo("Success", "User added successfully")
            dialog.destroy()
            self.refresh_user_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Username already exists")

    def log_action(self, action, details=""):
        username = getattr(self, "username_var", None)
        if isinstance(username, StringVar):
            username = username.get()
        elif hasattr(self, "username_var"):
            username = self.username_var
        else:
            username = "Unknown"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.cursor.execute(
                "INSERT INTO audit_logs (username, action, details, timestamp) VALUES (?, ?, ?, ?)",
                (username, action, details, timestamp)
            )
            self.conn.commit()
        except Exception:
            pass  # Avoid recursion if logging fails

    def create_audit_logs_tab(self):
        if self.user_role != "Admin":
            return
        self.audit_tab = Frame(self.notebook)
        self.notebook.add(self.audit_tab, text="Audit Logs")

         # Button frame for refresh
        button_frame = Frame(self.audit_tab)
        button_frame.pack(fill=X, padx=10, pady=5)
        Button(button_frame, text="Refresh", command=self.refresh_audit_logs).pack(side=LEFT, padx=5)
        self.refresh_audit_logs()

    def refresh_audit_logs(self):
        # Instead of deleting, just re-populate the audit logs
        if not hasattr(self, 'audit_tree'):
            self.audit_tree = ttk.Treeview(self.audit_tab, columns=("ID", "User", "Action", "Details", "Timestamp"), show="headings")
            self.audit_tree.heading("ID", text="ID")
            self.audit_tree.heading("User", text="User")
            self.audit_tree.heading("Action", text="Action")
            self.audit_tree.heading("Details", text="Details")
            self.audit_tree.heading("Timestamp", text="Timestamp")
            self.audit_tree.column("ID", width=40)
            self.audit_tree.column("User", width=100)
            self.audit_tree.column("Action", width=120)
            self.audit_tree.column("Details", width=300)
            self.audit_tree.column("Timestamp", width=140)
            self.audit_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        else:
            # Remove only the rows, not the widget itself
            for item in self.audit_tree.get_children():
                self.audit_tree.delete(item)
        # Re-populate the audit logs
        self.cursor.execute("SELECT id, username, action, details, timestamp FROM audit_logs ORDER BY timestamp DESC")
        for row in self.cursor.fetchall():
            self.audit_tree.insert("", END, values=row)

    def show_flagged_login_alerts(self):
    # Show only recent flagged attempts (e.g., last 24 hours)
        self.cursor.execute("""
            SELECT username, action, details, timestamp
            FROM audit_logs
            WHERE action IN ('Failed Login', 'Account Lockout', 'Security Alert')
            AND timestamp >= datetime('now', '-1 day')
            ORDER BY timestamp DESC
        """)
        flagged = self.cursor.fetchall()
        if flagged:
            msg = "Flagged Login Attempts (last 24h):\n\n"
            for row in flagged:
                msg += f"User: {row[0]}\nAction: {row[1]}\nDetails: {row[2]}\nTime: {row[3]}\n\n"
            messagebox.showwarning("Security Alert", msg)
    def toggle_theme(self):
        def update_widget_colors(widget, bg, fg):
            try:
                widget.configure(bg=bg)
            except:
                pass
            try:
                widget.configure(fg=fg)
            except:
                pass
            for child in widget.winfo_children():
                update_widget_colors(child, bg, fg)

        current_theme = self.root.cget("bg")
        if current_theme == "white":
            # Switch to dark mode
            bg, fg = "white", "#0F0F0F"
            self.root.configure(bg=bg)
            if self.main_frame:
                update_widget_colors(self.main_frame, bg, fg)
            self.status_var.set("Dark Mode Enabled")
        else:
            # Switch to light mode
            bg, fg = "#19191A", "#EBE8E1"
            self.root.configure(bg=bg)
            if self.main_frame:
                update_widget_colors(self.main_frame, bg, fg)
            self.status_var.set("Light Mode Enabled")

    def ai_chatbot(self):
        dialog = Toplevel(self.root)
        dialog.title("Hospital AI Assistant")
        dialog.geometry("600x400")
        dialog.resizable(True, True)

        # Chat display area
        chat_display = Text(dialog, wrap=WORD, state=DISABLED, height=20, width=70)
        chat_display.pack(pady=10, padx=10)

        # Input area
        input_frame = Frame(dialog)
        input_frame.pack(fill=X, padx=10, pady=10)

        # Show default question on load
        chat_display.config(state=NORMAL)
        chat_display.insert(END, "AI: How can I help you today? Type Help.\n")
        chat_display.config(state=DISABLED)

        # Add greetings capability
        def is_greeting(text):
            greetings = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening"]
            return any(greet in text.lower() for greet in greetings)

        input_label = Label(input_frame, text="You:")
        input_label.pack(side=LEFT, padx=5)

        user_input = Entry(input_frame, width=50)
        user_input.pack(side=LEFT, padx=5, fill=X, expand=True)
        # Allow Enter key to send message
        user_input.bind("<Return>", lambda event: process_query())

        def process_query():
            query = user_input.get().lower().strip()
            user_input.delete(0, END)

            if not query:
                return

            chat_display.config(state=NORMAL)
            chat_display.insert(END, f"You: {query}\n")

            if query in ['exit', 'quit', 'bye']:
                chat_display.insert(END, "AI: Goodbye! Have a nice day.\n")
                chat_display.config(state=DISABLED)
                return

            elif query == 'help':
                response = """
    AI Assistant Commands:
    - help: Show this help message
    - doctors: Information about doctors
    - patients: Information about patients
    - departments: List of departments
    - medicines: Information about available medicines
    - appointments: How to schedule appointments
    - contact: Hospital contact information
    - emergency: Emergency contacts
    - exit: Quit the chatbot
    """
            elif 'doctor' in query:
                self.cursor.execute("SELECT COUNT(*) FROM doctors")
                count = self.cursor.fetchone()[0]
                response = f"We have {count} doctors available. You can:\n- View all doctors in Doctor Management\n- Search for specific doctors by name or specialization\n- Contact the hospital for more information."
            elif 'patient' in query:
                self.cursor.execute("SELECT COUNT(*) FROM patients WHERE discharge_date IS NULL")
                count = self.cursor.fetchone()[0]
                response = f"There are currently {count} patients in our care.\n- Patient records can be accessed by authorized staff\n- Use Patient Management to view or update records."
            elif 'department' in query:
                self.cursor.execute("SELECT name FROM departments")
                depts = [d[0] for d in self.cursor.fetchall()]
                if depts:
                    response = "Our hospital has these departments:\n" + "\n".join(f"- {dept}" for dept in depts) + "\nYou can view more details in Department Management."
                else:
                    response = "Department information is not currently available."
            elif 'medicine' in query or 'pharmacy' in query:
                self.cursor.execute("SELECT COUNT(*) FROM pharmacy WHERE stock > 0")
                count = self.cursor.fetchone()[0]
                response = f"Our pharmacy currently stocks {count} different medicines.\n- View available medicines in Pharmacy Management\n- Contact the pharmacy for prescription information."
            elif "admission" in query or "admitted" in query:
                # Admissions today
                today = datetime.now().strftime("%Y-%m-%d")
                self.cursor.execute("SELECT COUNT(*) FROM admissions_log WHERE date(admission_date) = ?", (today,))
                admitted_today = self.cursor.fetchone()[0]
                response = f"Today, {admitted_today} patient(s) have been admitted."

            elif "doctor on leave" in query or "doctors on leave" in query or "staff on leave" in query:
                # Doctors/staff on leave today
                today = datetime.now().strftime("%Y-%m-%d")
                self.cursor.execute("""
                    SELECT COUNT(*) FROM staff_schedule
                    WHERE shift_date = ? AND leave = 1
                """, (today,))
                on_leave = self.cursor.fetchone()[0]
                response = f"Today, {on_leave} doctor(s)/staff are on leave."

            elif "scheduled doctor" in query or "scheduled doctors" in query or "doctor schedule" in query:
                # Scheduled doctors today
                today = datetime.now().strftime("%Y-%m-%d")
                self.cursor.execute("""
                    SELECT COUNT(DISTINCT staff_id) FROM staff_schedule
                    WHERE shift_date = ? AND role = 'Doctor' AND leave = 0
                """, (today,))
                scheduled_doctors = self.cursor.fetchone()[0]
                response = f"Today, {scheduled_doctors} doctor(s) are scheduled for duty."
            elif 'appointment' in query:
                response = """
    To schedule an appointment:
    1. Visit our reception desk
    2. Call our appointment hotline: +254 (700) 111-1111
    3. Use our online portal (coming soon)

    You'll need:
    - Patient information
    - Preferred doctor (if any)
    - Reason for visit
    """
            elif 'contact' in query:
                response = """
    Hospital Contact Information:
    - Main Phone: +254 (700) 111-1112
    - Emergency: +254 (700) 111-1112
    - Email: info@afyahospital.org
    - Address: 123 Nairobi, Kenya
    - Website: www.afyahospital.org
    """
            elif 'emergency' in query:
                response = """
    Emergency Contacts:
    - Hospital Emergency: +1 (555) 789-9999
    - Ambulance: 911 (or local emergency number)
    - Poison Control: +254 (710) 222-3333
    - Mental Health Crisis: +254 (700) 111-1111

    For immediate life-threatening emergencies, call 911.
    """
            else:
                # Greeting detection
                if is_greeting(query):
                    response = "Hello! How can I assist you today? Type 'help' for options."
                # Small talk
                elif "how are you" in query:
                    response = "I'm just a virtual assistant, but I'm here to help you!"
                elif "who are you" in query or "your name" in query:
                    response = "I'm the HMS Pro 2025 Virtual Assistant, here to help with hospital information."
                elif "thank" in query:
                    response = "You're welcome! Let me know if you need anything else."
                elif "time" in query:
                    response = f"The current time is {datetime.now().strftime('%H:%M:%S')}."
                elif "date" in query:
                    response = f"Today's date is {datetime.now().strftime('%Y-%m-%d')}."
                elif "joke" in query:
                    response = "Why did the computer go to the doctor? Because it had a virus!"
                else:
                    response = "I'm sorry, I didn't understand that. Type 'help' for available commands."

            chat_display.insert(END, f"AI: {response}\n")
            chat_display.config(state=DISABLED)

        send_button = Button(input_frame, text="Send", command=process_query)
        send_button.pack(side=LEFT, padx=5)

        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)

    def backup_database(self):
        backup_file = filedialog.asksaveasfilename(
            defaultextension=".db",
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            title="Save database backup as"
        )
        
        if not backup_file:
            return
        
        try:
            # Create a backup connection
            backup_conn = sqlite3.connect(backup_file)
            
            # Use the backup API to copy the database
            with backup_conn:
                self.conn.backup(backup_conn)
            
            backup_conn.close()
            messagebox.showinfo("Success", f"Database backup created successfully at:\n{backup_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Backup failed: {e}")
    
    def restore_database(self):
        backup_file = filedialog.askopenfilename(
            filetypes=[("Database files", "*.db"), ("All files", "*.*")],
            title="Select database backup to restore"
        )
        
        if not backup_file:
            return
        
        confirmation = messagebox.askyesno(
            "Confirm Restore",
            "WARNING: This will overwrite the current database.\nAre you sure you want to continue?"
        )
        
        if not confirmation:
            return
        
        try:
            # Close the current connection
            self.conn.close()
            
            # Make a temporary copy of the current database (just in case)
            temp_backup = "hospital_backup_before_restore.db"
            if os.path.exists("afya.db"):
                os.replace("afya.db", temp_backup)
            
            # Copy the backup file to the current database file
            import shutil
            shutil.copy(backup_file, "afya.db")
            
            # Reconnect to the database
            self.conn = sqlite3.connect("afya.db")
            self.cursor = self.conn.cursor()
            
            messagebox.showinfo(
                "Success", 
                f"Database restored successfully from:\n{backup_file}\n\n"
                f"Original database was saved as:\n{temp_backup}"
            )
            
            # Refresh all views
            if self.main_frame:
                self.refresh_patient_list()
                self.refresh_doctor_list()
                self.refresh_department_list()
                self.refresh_pharmacy_list()
                self.refresh_appointment_list()
                
        except Exception as e:
            messagebox.showerror("Error", f"Restore failed: {e}")
            # Try to reconnect to the original database
            try:
                if os.path.exists(temp_backup):
                    os.replace(temp_backup, "afya.db")
                self.conn = sqlite3.connect("afya.db")
                self.cursor = self.conn.cursor()
            except:
                pass
    
    def show_about(self):
        messagebox.showinfo(
            "About Hospital Management System",
            "Hospital Management System\n\n"
            "Version 1.0\n"
            "Developed by J-FirstHand Software Ltd\n\n"
            "Call us: +254 770641459\n\n"
            "©2025 Hospital Management"
        )
    
    def __del__(self):
        # Close database connection when the application is closed
        if hasattr(self, 'conn'):
            self.conn.close()

    def master_refresh(self):
        # Refresh all main data tables if they exist
        try:
            if hasattr(self, "refresh_patient_list") and hasattr(self, "patient_tree"):
                self.refresh_patient_list()
            if hasattr(self, "refresh_doctor_list") and hasattr(self, "doctor_tree"):
                self.refresh_doctor_list()
            if hasattr(self, "refresh_department_list") and hasattr(self, "department_tree"):
                self.refresh_department_list()
            if hasattr(self, "refresh_pharmacy_list") and hasattr(self, "pharmacy_tree"):
                self.refresh_pharmacy_list()
            if hasattr(self, "refresh_appointment_list") and hasattr(self, "appointment_tree"):
                self.refresh_appointment_list()
            if hasattr(self, "refresh_billing_data") and hasattr(self, "billing_tree"):
                self.refresh_billing_data()
            if hasattr(self, "refresh_admissions_data") and hasattr(self, "admissions_tree"):
                self.refresh_admissions_data()
            if hasattr(self, "refresh_dashboard_charts") and hasattr(self, "chart_notebook"):
                self.refresh_dashboard_charts()
            if hasattr(self, "refresh_audit_logs") and hasattr(self, "audit_tree"):
                self.refresh_audit_logs()
            self.status_var.set("All data refreshed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to refresh all data: {e}")

    def create_menu_bar(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = Menu(menubar, tearoff=0)
        file_menu.add_command(label="Backup Database", command=self.backup_database)
        file_menu.add_command(label="Restore Database", command=self.restore_database)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        email_menu = Menu(menubar, tearoff=0)
        email_menu.add_command(label="Send Email", command=self.show_email_dialog)
        menubar.add_cascade(label="Email", menu=email_menu)

        view_menu = Menu(menubar, tearoff=0)
        view_menu.add_command(label="Virtual Assistant", command=self.ai_chatbot)
        menubar.add_cascade(label="Virtual Assistant", menu=view_menu)

         # View menu
        view_menu = Menu(menubar, tearoff=0)
        view_menu.add_command(label="Toggle Dark Mode", command=self.toggle_theme)
        menubar.add_cascade(label="View", menu=view_menu)

        # Help menu
        help_menu = Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)
        menubar.add_command(label="Refresh All", command=self.master_refresh)
        


    def create_patient_tab(self):
        self.patient_tab = Frame(self.notebook)
        self.notebook.add(self.patient_tab, text="Patient Management")
        
        # Create patient management widgets
        self.patient_tree = ttk.Treeview(self.patient_tab, columns=("ID", "Name", "Age", "Gender", "Contact", "Department", "Doctor", "Admission", "Discharge"), show="headings")
    
        

    # Bind the right-click event to the patient tree   

        # Configure columns
        self.patient_tree.heading("ID", text="ID")
        self.patient_tree.heading("Name", text="Name")
        self.patient_tree.heading("Age", text="Age")
        self.patient_tree.heading("Gender", text="Gender")
        self.patient_tree.heading("Contact", text="Contact")
        self.patient_tree.heading("Department", text="Department")
        self.patient_tree.heading("Doctor", text="Doctor")
        self.patient_tree.heading("Admission", text="Admission Date")
        self.patient_tree.heading("Discharge", text="Discharge Date")
        
        # Set column widths
        self.patient_tree.column("ID", width=50)
        self.patient_tree.column("Name", width=150)
        self.patient_tree.column("Age", width=50)
        self.patient_tree.column("Gender", width=70)
        self.patient_tree.column("Contact", width=120)
        self.patient_tree.column("Department", width=120)
        self.patient_tree.column("Doctor", width=150)
        self.patient_tree.column("Admission", width=150)
        self.patient_tree.column("Discharge", width=150)
        
        self.patient_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Buttons frame
        button_frame = Frame(self.patient_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        
        Button(button_frame, text="Add Patient", command=self.show_add_patient_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Allocate Bed", command=self.allocate_bed_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Triage", command=self.show_triage_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Edit Patient", command=self.edit_patient).pack(side=LEFT, padx=5)
        Button(button_frame, text="Delete Patient", command=self.delete_patient).pack(side=LEFT, padx=5)
        Button(button_frame, text="Discharge Patient", command=self.discharge_patient).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_patient_list).pack(side=LEFT, padx=5)
        Button(button_frame, text="Search", command=self.search_patient_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Reception", command=self.show_reception_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Patient Journey", command=lambda: self.show_patient_journey(self.get_selected_patient_id())).pack(side=LEFT, padx=5)
        Button(button_frame, text="Medical History", command=lambda: self.show_medical_history(self.get_selected_patient_id())).pack(side=LEFT, padx=5)
        Button(button_frame, text="Export CSV", command=self.export_patients_csv).pack(side=LEFT, padx=5)
        if pd is not None:
            Button(button_frame, text="Export Excel", command=self.export_patients_excel).pack(side=LEFT, padx=5)


    def export_patients_csv(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            title="Save Patients Data as CSV"
        )
        if not file_path:
            return

        try:
            self.cursor.execute("""
                SELECT p.id, p.name, p.age, p.gender, p.contact, p.department, 
                       d.name as doctor_name, p.admission_date, p.discharge_date
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
            """)
            patients = self.cursor.fetchall()

            columns = ["ID", "Name", "Age", "Gender", "Contact", "Department", "Doctor", "Admission Date", "Discharge Date"]
            with open(file_path, mode="w", newline="", encoding="utf-8") as file:
                writer = csv.writer(file)
                writer.writerow(columns)
                writer.writerows(patients)

            messagebox.showinfo("Success", f"Patients data exported successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {e}")

    def export_patients_excel(self):
                if pd is None:
                    messagebox.showerror("Error", "Pandas library is not installed. Please install it to export to Excel.")
                    return
        
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".xlsx",
                    filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                    title="Save Patients Data as Excel"
                )
                if not file_path:
                    return
        
                try:
                    self.cursor.execute("""
                        SELECT p.id, p.name, p.age, p.gender, p.contact, p.department, 
                            d.name as doctor_name, p.admission_date, p.discharge_date
                        FROM patients p
                        LEFT JOIN doctors d ON p.doctor_id = d.id
                    """)
                    patients = self.cursor.fetchall()
        
                    columns = ["ID", "Name", "Age", "Gender", "Contact", "Department", "Doctor", "Admission Date", "Discharge Date"]
                    df = pd.DataFrame(patients, columns=columns)
                    df.to_excel(file_path, index=False)
                    messagebox.showinfo("Success", f"Patients data exported successfully to {file_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to export data: {e}")

    def show_medical_history(self, patient_id):
        if not patient_id:
            return
        dialog = Toplevel(self.root)
        dialog.title("Medical History")
        dialog.geometry("700x500")
        dialog.resizable(True, True)

        # Table for history
        tree = ttk.Treeview(dialog, columns=("Date", "Diagnosis", "Allergies", "Notes"), show="headings")
        tree.heading("Date", text="Visit Date")
        tree.heading("Diagnosis", text="Diagnosis")
        tree.heading("Allergies", text="Allergies")
        tree.heading("Notes", text="Notes")
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Load history
        self.cursor.execute("""
            SELECT visit_date, diagnosis, allergies, notes
            FROM medical_history
            WHERE patient_id = ?
            ORDER BY visit_date DESC
        """, (patient_id,))
        for row in self.cursor.fetchall():
            tree.insert("", END, values=row)

        # Add new history entry
        add_frame = Frame(dialog)
        add_frame.pack(fill=X, padx=10, pady=10)

        Label(add_frame, text="Diagnosis:").grid(row=0, column=0, padx=5, pady=5, sticky=W)
        diagnosis_entry = Entry(add_frame)
        diagnosis_entry.grid(row=0, column=1, padx=5, pady=5, sticky=EW)

        Label(add_frame, text="Allergies:").grid(row=1, column=0, padx=5, pady=5, sticky=W)
        allergies_entry = Entry(add_frame)
        allergies_entry.grid(row=1, column=1, padx=5, pady=5, sticky=EW)

        Label(add_frame, text="Notes:").grid(row=2, column=0, padx=5, pady=5, sticky=W)
        notes_entry = Entry(add_frame)
        notes_entry.grid(row=2, column=1, padx=5, pady=5, sticky=EW)

        Button(add_frame, text="Add Entry", command=lambda: self.add_medical_history_entry(
            patient_id, diagnosis_entry.get(), allergies_entry.get(), notes_entry.get(), dialog, tree
        )).grid(row=3, column=0, columnspan=2, pady=10)    

    def add_medical_history_entry(self, patient_id, diagnosis, allergies, notes, dialog, tree):
        visit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            INSERT INTO medical_history (patient_id, diagnosis, allergies, visit_date, notes)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, diagnosis, allergies, visit_date, notes))
        self.conn.commit()
        messagebox.showinfo("Success", "Medical history entry added.")
        # Refresh the tree
        for item in tree.get_children():
            tree.delete(item)
        self.cursor.execute("""
            SELECT visit_date, diagnosis, allergies, notes
            FROM medical_history
            WHERE patient_id = ?
            ORDER BY visit_date DESC
        """, (patient_id,))
        for row in self.cursor.fetchall():
            tree.insert("", END, values=row)    
        

    def show_add_patient_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add New Patient")
        dialog.geometry("500x500")
        dialog.resizable(True, True)
        
        
        # Form fields
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Age:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        age_entry = Entry(dialog)
        age_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Gender:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        gender_var = StringVar(value="M")
        Radiobutton(dialog, text="Male", variable=gender_var, value="M").grid(row=2, column=1, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Female", variable=gender_var, value="F").grid(row=3, column=1, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Other", variable=gender_var, value="Other").grid(row=4, column=1, padx=10, pady=5, sticky=W)
        
        Label(dialog, text="Contact:").grid(row=5, column=0, padx=10, pady=10, sticky=W)
        contact_entry = Entry(dialog)
        contact_entry.grid(row=5, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Department:").grid(row=6, column=0, padx=10, pady=10, sticky=W)
        department_entry = Entry(dialog)
        department_entry.grid(row=6, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Doctor:").grid(row=7, column=0, padx=10, pady=10, sticky=W)

        Label(dialog, text="Patient Type:").grid(row=8, column=0, padx=10, pady=10, sticky=W)
        patient_type_var = StringVar(value="Outpatient")
        type_dropdown = ttk.Combobox(dialog, textvariable=patient_type_var, values=["Outpatient", "Inpatient"], state="readonly")
        type_dropdown.grid(row=8, column=1, padx=10, pady=10, sticky=EW)
        
        # Get available doctors
        self.cursor.execute("SELECT id, name FROM doctors")
        doctors = self.cursor.fetchall()
        doctor_options = ["None"] + [f"{doc[0]} - {doc[1]}" for doc in doctors]
        doctor_var = StringVar(value="None")
        doctor_dropdown = ttk.Combobox(dialog, textvariable=doctor_var, values=doctor_options, state="readonly")
        doctor_dropdown.grid(row=7, column=1, padx=10, pady=10, sticky=EW)
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=8, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Save", command=lambda: self.save_patient(
            name_entry.get(),
            age_entry.get(),
            gender_var.get(),
            contact_entry.get(),
            department_entry.get(),
            doctor_var.get().split(" - ")[0] if doctor_var.get() != "None" else None,
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(dialog, text="Cancel", command=dialog.destroy).grid(row=9, column=0, columnspan=2, pady=20)
    
    def delete_patient(self):
        selected_item = self.patient_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a patient to delete")
            return

        patient_data = self.patient_tree.item(selected_item)['values']
        patient_id = patient_data[0]

        confirm = messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete patient '{patient_data[1]}' (ID: {patient_id})? This action cannot be undone.")
        if not confirm:
            return

        try:
            # Delete related records first if needed (appointments, billing, etc.)
            self.cursor.execute("DELETE FROM appointments WHERE patient_id = ?", (patient_id,))
            self.cursor.execute("DELETE FROM billing WHERE patient_id = ?", (patient_id,))
            self.cursor.execute("DELETE FROM patient_journey WHERE patient_id = ?", (patient_id,))
            self.cursor.execute("DELETE FROM admissions_log WHERE patient_id = ?", (patient_id,))
            self.cursor.execute("DELETE FROM issued_medicines WHERE patient_id = ?", (patient_id,))
            self.cursor.execute("DELETE FROM medical_history WHERE patient_id = ?", (patient_id,))
            # Delete the patient record
            self.cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            self.conn.commit()
            messagebox.showinfo("Success", "Patient deleted successfully")
            self.refresh_patient_list()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete patient: {e}")

    def save_patient(self, name, age, gender, contact, department, doctor_id, dialog):
        # Validation
        if not name or not age or not contact or not department:
            messagebox.showerror("Error", "All fields are required except doctor")
            return
        
        try:
            age = int(age)
            if age <= 0 or age >= 120:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Age must be a number between 1 and 119")
            return
        
        if doctor_id == "None":
            doctor_id = None
        
        admission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.cursor.execute("""
                INSERT INTO patients (name, age, gender, contact, department, doctor_id, admission_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, age, gender, contact, department, doctor_id, admission_date))
            patient_id = self.cursor.lastrowid

            # Log admission
            self.cursor.execute("""
                INSERT INTO admissions_log (patient_id, admission_date, department, doctor_id)
                VALUES (?, ?, ?, ?)
            """, (patient_id, admission_date, department, doctor_id))
            self.conn.commit()
            messagebox.showinfo("Success", "Patient added successfully")
            dialog.destroy()
            self.refresh_patient_list()
            self.refresh_admissions_data()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Contact number already exists in the system")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        
        # Ensure payment_method column exists, ignore error if already exists
        try:
            self.cursor.execute("ALTER TABLE patients ADD COLUMN payment_method TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            pass  # Already exists
    
    def refresh_patient_list(self):
        # Only proceed if patient_tree exists
        if not hasattr(self, "patient_tree"):
            return
        # Clear existing data
        for item in self.patient_tree.get_children():
            self.patient_tree.delete(item)
        
        # Get patients with doctor names via LEFT JOIN
        self.cursor.execute("""
            SELECT p.id, p.name, p.age, p.gender, p.contact, p.department, 
                   d.name as doctor_name, p.admission_date, p.discharge_date
            FROM patients p
            LEFT JOIN doctors d ON p.doctor_id = d.id
        """)
        
        patients = self.cursor.fetchall()
        
        # Add to treeview
        for patient in patients:
            self.patient_tree.insert("", END, values=patient)
    
    def edit_patient(self):
        selected_item = self.patient_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a patient to edit")
            return

        patient_data = self.patient_tree.item(selected_item)['values']

        dialog = Toplevel(self.root)
        dialog.title("Edit Patient")
        dialog.geometry("500x550")
        dialog.resizable(True, True)

        # Form fields with current data
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        name_entry.insert(0, patient_data[1])

        Label(dialog, text="Age:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        age_entry = Entry(dialog)
        age_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        age_entry.insert(0, patient_data[2])

        Label(dialog, text="Gender:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        gender_var = StringVar(value=patient_data[3])
        Radiobutton(dialog, text="Male", variable=gender_var, value="M").grid(row=2, column=1, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Female", variable=gender_var, value="F").grid(row=3, column=1, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Other", variable=gender_var, value="Other").grid(row=4, column=1, padx=10, pady=5, sticky=W)

        Label(dialog, text="Contact:").grid(row=5, column=0, padx=10, pady=10, sticky=W)
        contact_entry = Entry(dialog)
        contact_entry.grid(row=5, column=1, padx=10, pady=10, sticky=EW)
        contact_entry.insert(0, patient_data[4])

        Label(dialog, text="Department:").grid(row=6, column=0, padx=10, pady=10, sticky=W)
        department_entry = Entry(dialog)
        department_entry.grid(row=6, column=1, padx=10, pady=10, sticky=EW)
        department_entry.insert(0, patient_data[5])

        Label(dialog, text="Doctor:").grid(row=7, column=0, padx=10, pady=10, sticky=W)

        # Get available doctors
        self.cursor.execute("SELECT id, name FROM doctors")
        doctors = self.cursor.fetchall()
        doctor_options = ["None"] + [f"{doc[0]} - {doc[1]}" for doc in doctors]

        # Find current doctor if exists
        current_doctor = "None"
        if patient_data[6]:  # If there's a doctor assigned
            for doc in doctors:
                if doc[1] == patient_data[6]:
                    current_doctor = f"{doc[0]} - {doc[1]}"
                    break

        doctor_var = StringVar(value=current_doctor)
        doctor_dropdown = ttk.Combobox(dialog, textvariable=doctor_var, values=doctor_options, state="readonly")
        doctor_dropdown.grid(row=7, column=1, padx=10, pady=10, sticky=EW)

        # Patient Type
        Label(dialog, text="Patient Type:").grid(row=8, column=0, padx=10, pady=10, sticky=W)
        # Fetch current patient_type from DB
        self.cursor.execute("SELECT patient_type FROM patients WHERE id = ?", (patient_data[0],))
        patient_type_row = self.cursor.fetchone()
        current_patient_type = patient_type_row[0] if patient_type_row and patient_type_row[0] else "Outpatient"
        patient_type_var = StringVar(value=current_patient_type)
        type_dropdown = ttk.Combobox(dialog, textvariable=patient_type_var, values=["Outpatient", "Inpatient"], state="readonly")
        type_dropdown.grid(row=8, column=1, padx=10, pady=10, sticky=EW)

        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=9, column=0, columnspan=2, pady=20)

        Button(button_frame, text="Update", command=lambda: self.update_patient(
            patient_data[0],  # patient_id
            name_entry.get(),
            age_entry.get(),
            gender_var.get(),
            contact_entry.get(),
            department_entry.get(),
            doctor_var.get().split(" - ")[0] if doctor_var.get() != "None" else None,
            patient_type_var.get(),
            dialog
        )).pack(side=LEFT, padx=10)

        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)

    def update_patient(self, patient_id, name, age, gender, contact, department, doctor_id, patient_type, dialog):
        # Validation
        if not name or not age or not contact or not department:
            messagebox.showerror("Error", "All fields are required except doctor")
            return

        try:
            age = int(age)
            if age <= 0 or age >= 120:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Age must be a number between 1 and 119")
            return

        if doctor_id == "None":
            doctor_id = None

        try:
            self.cursor.execute("""
                UPDATE patients 
                SET name = ?, age = ?, gender = ?, contact = ?, department = ?, doctor_id = ?, patient_type = ?
                WHERE id = ?
            """, (name, age, gender, contact, department, doctor_id, patient_type, patient_id))
            self.conn.commit()
            messagebox.showinfo("Success", "Patient updated successfully")
            dialog.destroy()
            self.refresh_patient_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Contact number already exists in the system")
    
    

    def discharge_patient(self):
        selected_item = self.patient_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a patient to discharge")
            return
        
        patient_data = self.patient_tree.item(selected_item)['values']
        patient_id = patient_data[0]

        # Retrieve patient_type from the database
        self.cursor.execute("SELECT patient_type FROM patients WHERE id = ?", (patient_id,))
        result = self.cursor.fetchone()
        patient_type = result[0] if result else None

        if patient_type == "Inpatient":
            discharge_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            # Free the bed
            self.cursor.execute("UPDATE beds SET status='Available', patient_id=NULL, discharge_date=? WHERE patient_id=?", (discharge_date, patient_id))
            self.conn.commit()
            # Show discharge summary
            self.show_discharge_summary(patient_id)
            pass

        # Check if already discharged
        if patient_data[8]:  # discharge_date exists
            messagebox.showinfo("Info", "This patient is already discharged")
            return
        
        confirmation = messagebox.askyesno("Confirm", "Are you sure you want to discharge this patient?")
        if confirmation:
            discharge_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.cursor.execute("UPDATE patients SET discharge_date = ? WHERE id = ?", 
                               (discharge_date, patient_id))
            
            # Log discharge
            self.cursor.execute("""
                UPDATE admissions_log 
                SET discharge_date = ? 
                WHERE patient_id = ? AND discharge_date IS NULL
            """, (discharge_date, patient_id))
            self.conn.commit()
            messagebox.showinfo("Success", "Patient discharged successfully")
            self.refresh_patient_list()
            self.refresh_admissions_data()
            
            # Generate discharge report
            self.generate_discharge_report(patient_id)

    def generate_discharge_report(self, patient_id):
        try:
            # Fetch patient details
            self.cursor.execute("""
                SELECT p.name, p.age, p.gender, p.contact, p.department, d.name as doctor_name, p.admission_date, p.discharge_date
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.id = ?
            """, (patient_id,))
            patient = self.cursor.fetchone()

            # Fetch recommended medicines
            self.cursor.execute("""
                SELECT m.medicine_name, m.price, m.supplier
                FROM issued_medicines im
                JOIN pharmacy m ON im.medicine_id = m.id
                WHERE im.patient_id = ?
            """, (patient_id,))
            medicines = self.cursor.fetchall()

            # Fetch diagnosis (if stored in a separate table or as notes)
            self.cursor.execute("""
                SELECT notes
                FROM appointments
                WHERE patient_id = ? AND status = 'Completed'
                ORDER BY appointment_date DESC LIMIT 1
            """, (patient_id,))
            diagnosis = self.cursor.fetchone()

            # Generate report
            report = f"Discharge Report\n{'='*50}\n"
            report += f"Name: {patient[0]}\n"
            report += f"Age: {patient[1]}\n"
            report += f"Gender: {patient[2]}\n"
            report += f"Contact: {patient[3]}\n"
            report += f"Department: {patient[4]}\n"
            report += f"Doctor in Charge: {patient[5]}\n"
            report += f"Admission Date: {patient[6]}\n"
            report += f"Discharge Date: {patient[7]}\n\n"

            report += "Diagnosis:\n"
            report += f"{diagnosis[0] if diagnosis else 'No diagnosis available'}\n\n"

            report += "Medicines Recommended:\n"
            if medicines:
                for med in medicines:
                    report += f"- {med[0]} (Price: {med[1]}, Supplier: {med[2]})\n"
            else:
                report += "No medicines recommended.\n"

            # Display report in a new window
            dialog = Toplevel(self.root)
            dialog.title("Discharge Report")
            dialog.geometry("600x400")
            dialog.resizable(True, True)

            report_text = Text(dialog, wrap=WORD, height=20, width=70)
            report_text.insert(END, report)
            report_text.config(state=DISABLED)
            report_text.pack(pady=10, padx=10)

            Button(dialog, text="Close", command=dialog.destroy).pack(pady=10)

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to generate discharge report: {e}")
    
    def search_patient_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Search Patients")
        dialog.geometry("400x700")
        dialog.resizable(True, True)
        
        Label(dialog, text="Search by:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        
        search_var = StringVar(value="name")
        Radiobutton(dialog, text="Name", variable=search_var, value="name").grid(row=1, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Contact", variable=search_var, value="contact").grid(row=2, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="ID", variable=search_var, value="id").grid(row=3, column=0, padx=10, pady=5, sticky=W)
        
        Label(dialog, text="Search term:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        term_entry = Entry(dialog)
        term_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        
        button_frame = Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        Button(button_frame, text="Search", command=lambda: self.search_patient(
            search_var.get(),
            term_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def search_patient(self, search_by, term, dialog):
        if not term:
            messagebox.showwarning("Warning", "Please enter a search term")
            return
        
        # Clear existing data
        for item in self.patient_tree.get_children():
            self.patient_tree.delete(item)
        
        if search_by == "name":
            self.cursor.execute("""
                SELECT p.id, p.name, p.age, p.gender, p.contact, p.department, 
                       d.name as doctor_name, p.admission_date, p.discharge_date
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.name LIKE ?
            """, (f"%{term}%",))
        elif search_by == "contact":
            self.cursor.execute("""
                SELECT p.id, p.name, p.age, p.gender, p.contact, p.department, 
                       d.name as doctor_name, p.admission_date, p.discharge_date
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.contact LIKE ?
            """, (f"%{term}%",))
        elif search_by == "id":
            self.cursor.execute("""
                SELECT p.id, p.name, p.age, p.gender, p.contact, p.department, 
                       d.name as doctor_name, p.admission_date, p.discharge_date
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.id = ?
            """, (term,))
        
        patients = self.cursor.fetchall()
        
        if not patients:
            messagebox.showinfo("Info", "No matching patients found")
            return
        
        # Add to treeview
        for patient in patients:
            self.patient_tree.insert("", END, values=patient)
        
        dialog.destroy()
    
    
    def create_doctor_tab(self):
        self.doctor_tab = Frame(self.notebook)
        self.notebook.add(self.doctor_tab, text="Doctor Management")
        
        # Create doctor management widgets
        self.doctor_tree = ttk.Treeview(self.doctor_tab, columns=("ID", "Name", "Specialization", "Department", "Contact", "Email", "Availability"), show="headings")
        
        # Configure columns
        self.doctor_tree.heading("ID", text="ID")
        self.doctor_tree.heading("Name", text="Name")
        self.doctor_tree.heading("Specialization", text="Specialization")
        self.doctor_tree.heading("Department", text="Department")
        self.doctor_tree.heading("Contact", text="Contact")
        self.doctor_tree.heading("Email", text="Email")
        self.doctor_tree.heading("Availability", text="Availability")
        
        # Set column widths
        self.doctor_tree.column("ID", width=50)
        self.doctor_tree.column("Name", width=150)
        self.doctor_tree.column("Specialization", width=150)
        self.doctor_tree.column("Department", width=120)
        self.doctor_tree.column("Contact", width=120)
        self.doctor_tree.column("Email", width=150)
        self.doctor_tree.column("Availability", width=150)
        
        self.doctor_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Buttons frame
        button_frame = Frame(self.doctor_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        
        Button(button_frame, text="Add Doctor", command=self.show_add_doctor_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Edit Doctor", command=self.edit_doctor).pack(side=LEFT, padx=5)
        Button(button_frame, text="Delete Doctor", command=self.delete_doctor).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_doctor_list).pack(side=LEFT, padx=5)
        Button(button_frame, text="Search", command=self.search_doctor_dialog).pack(side=LEFT, padx=5)
        
        # Load initial doctor data
        self.refresh_doctor_list()
    
    def show_add_doctor_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add New Doctor")
        dialog.geometry("500x500")
        dialog.resizable(True, True)
        
        # Form fields
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Specialization:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        specialization_entry = Entry(dialog)
        specialization_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Department:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        department_entry = Entry(dialog)
        department_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Contact:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        contact_entry = Entry(dialog)
        contact_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Email:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        email_entry = Entry(dialog)
        email_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Availability:").grid(row=5, column=0, padx=10, pady=10, sticky=W)
        availability_entry = Entry(dialog)
        availability_entry.grid(row=5, column=1, padx=10, pady=10, sticky=EW)
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Save", command=lambda: self.save_doctor(
            name_entry.get(),
            specialization_entry.get(),
            department_entry.get(),
            contact_entry.get(),
            email_entry.get(),
            availability_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def save_doctor(self, name, specialization, department, contact, email, availability, dialog):
        # Validation
        if not name or not specialization or not department or not contact or not availability:
            messagebox.showerror("Error", "All fields except email are required")
            return
        
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messagebox.showerror("Error", "Invalid email format")
            return
        
        try:
            self.cursor.execute("""
                INSERT INTO doctors (name, specialization, department, contact, email, availability)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (name, specialization, department, contact, email or None, availability))
            self.conn.commit()
            messagebox.showinfo("Success", "Doctor added successfully")
            dialog.destroy()
            self.refresh_doctor_list()
        except sqlite3.IntegrityError as e:
            messagebox.showerror("Error", f"Database error: {e}")
    
    def refresh_doctor_list(self):
        # Clear existing data
        for item in self.doctor_tree.get_children():
            self.doctor_tree.delete(item)
        
        # Get all doctors
        self.cursor.execute("SELECT id, name, specialization, department, contact, email, availability FROM doctors")
        doctors = self.cursor.fetchall()
        
        # Add to treeview
        for doctor in doctors:
            self.doctor_tree.insert("", END, values=doctor)
    
    def edit_doctor(self):
        selected_item = self.doctor_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a doctor to edit")
            return
        
        doctor_data = self.doctor_tree.item(selected_item)['values']
        
        dialog = Toplevel(self.root)
        dialog.title("Edit Doctor")
        dialog.geometry("500x700")
        dialog.resizable(True, True)
        
        # Form fields with current data
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        name_entry.insert(0, doctor_data[1])
        
        Label(dialog, text="Specialization:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        specialization_entry = Entry(dialog)
        specialization_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        specialization_entry.insert(0, doctor_data[2])
        
        Label(dialog, text="Department:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        department_entry = Entry(dialog)
        department_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        department_entry.insert(0, doctor_data[3])
        
        Label(dialog, text="Contact:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        contact_entry = Entry(dialog)
        contact_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        contact_entry.insert(0, doctor_data[4])
        
        Label(dialog, text="Email:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        email_entry = Entry(dialog)
        email_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        email_entry.insert(0, doctor_data[5] if doctor_data[5] else "")
        
        Label(dialog, text="Availability:").grid(row=5, column=0, padx=10, pady=10, sticky=W)
        availability_entry = Entry(dialog)
        availability_entry.grid(row=5, column=1, padx=10, pady=10, sticky=EW)
        availability_entry.insert(0, doctor_data[6])
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Update", command=lambda: self.update_doctor(
            doctor_data[0],  # doctor_id
            name_entry.get(),
            specialization_entry.get(),
            department_entry.get(),
            contact_entry.get(),
            email_entry.get(),
            availability_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def update_doctor(self, doctor_id, name, specialization, department, contact, email, availability, dialog):
        # Validation
        if not name or not specialization or not department or not contact or not availability:
            messagebox.showerror("Error", "All fields except email are required")
            return
        
        if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messagebox.showerror("Error", "Invalid email format")
            return
        
        try:
            self.cursor.execute("""
                UPDATE doctors 
                SET name = ?, specialization = ?, department = ?, contact = ?, email = ?, availability = ?
                WHERE id = ?
            """, (name, specialization, department, contact, email or None, availability, doctor_id))
            self.conn.commit()
            messagebox.showinfo("Success", "Doctor updated successfully")
            dialog.destroy()
            self.refresh_doctor_list()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
    
    def delete_doctor(self):
        selected_item = self.doctor_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a doctor to delete")
            return
        
        doctor_data = self.doctor_tree.item(selected_item)['values']
        doctor_id = doctor_data[0]
        
        # Check if doctor is assigned to any patients
        self.cursor.execute("SELECT id FROM patients WHERE doctor_id = ?", (doctor_id,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Cannot delete doctor. They are assigned to patients.")
            return
        
        # Check if doctor is head of any department
        self.cursor.execute("SELECT id FROM departments WHERE head_doctor_id = ?", (doctor_id,))
        if self.cursor.fetchone():
            messagebox.showerror("Error", "Cannot delete doctor. They are head of a department.")
            return
        
        confirmation = messagebox.askyesno("Confirm", f"Are you sure you want to delete doctor {doctor_data[1]}?")
        if confirmation:
            self.cursor.execute("DELETE FROM doctors WHERE id = ?", (doctor_id,))
            self.conn.commit()
            messagebox.showinfo("Success", "Doctor deleted successfully")
            self.refresh_doctor_list()
    
    def search_doctor_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Search Doctors")
        dialog.geometry("400x700")
        dialog.resizable(True, True)
        
        Label(dialog, text="Search by:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        
        search_var = StringVar(value="name")
        Radiobutton(dialog, text="Name", variable=search_var, value="name").grid(row=1, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Specialization", variable=search_var, value="specialization").grid(row=2, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Department", variable=search_var, value="department").grid(row=3, column=0, padx=10, pady=5, sticky=W)
        
        Label(dialog, text="Search term:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        term_entry = Entry(dialog)
        term_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        
        button_frame = Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        Button(button_frame, text="Search", command=lambda: self.search_doctor(
            search_var.get(),
            term_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def search_doctor(self, search_by, term, dialog):
        if not term:
            messagebox.showwarning("Warning", "Please enter a search term")
            return
        
        # Clear existing data
        for item in self.doctor_tree.get_children():
            self.doctor_tree.delete(item)
        
        if search_by == "name":
            self.cursor.execute("SELECT * FROM doctors WHERE name LIKE ?", (f"%{term}%",))
        elif search_by == "specialization":
            self.cursor.execute("SELECT * FROM doctors WHERE specialization LIKE ?", (f"%{term}%",))
        elif search_by == "department":
            self.cursor.execute("SELECT * FROM doctors WHERE department LIKE ?", (f"%{term}%",))
        
        doctors = self.cursor.fetchall()
        
        if not doctors:
            messagebox.showinfo("Info", "No matching doctors found")
            return
        
        # Add to treeview
        for doctor in doctors:
            self.doctor_tree.insert("", END, values=doctor)
        
        dialog.destroy()
    
    def create_department_tab(self):
        self.department_tab = Frame(self.notebook)
        self.notebook.add(self.department_tab, text="Departments")
        
        # Create department management widgets
        self.department_tree = ttk.Treeview(self.department_tab, columns=("ID", "Name", "Head Doctor", "Description"), show="headings")
        
        # Configure columns
        self.department_tree.heading("ID", text="ID")
        self.department_tree.heading("Name", text="Name")
        self.department_tree.heading("Head Doctor", text="Head Doctor")
        self.department_tree.heading("Description", text="Description")
        
        # Set column widths
        self.department_tree.column("ID", width=50)
        self.department_tree.column("Name", width=200)
        self.department_tree.column("Head Doctor", width=200)
        self.department_tree.column("Description", width=300)
        
        self.department_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Buttons frame
        button_frame = Frame(self.department_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        
        Button(button_frame, text="Add Department", command=self.show_add_department_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Edit Department", command=self.edit_department).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_department_list).pack(side=LEFT, padx=5)
        
        # Load initial department data
        self.refresh_department_list()
    
    def show_add_department_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add New Department")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        
        # Form fields
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Head Doctor:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        
        # Get available doctors
        self.cursor.execute("SELECT id, name FROM doctors")
        doctors = self.cursor.fetchall()
        doctor_options = ["None"] + [f"{doc[0]} - {doc[1]}" for doc in doctors]
        doctor_var = StringVar(value="None")
        doctor_dropdown = ttk.Combobox(dialog, textvariable=doctor_var, values=doctor_options, state="readonly")
        doctor_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Description:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        description_entry = Text(dialog, height=5, width=40)
        description_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Save", command=lambda: self.save_department(
            name_entry.get(),
            doctor_var.get().split(" - ")[0] if doctor_var.get() != "None" else None,
            description_entry.get("1.0", END).strip(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def save_department(self, name, head_doctor_id, description, dialog):
        if not name:
            messagebox.showerror("Error", "Department name is required")
            return
        
        try:
            self.cursor.execute("""
                INSERT INTO departments (name, head_doctor_id, description)
                VALUES (?, ?, ?)
            """, (name, head_doctor_id, description or None))
            self.conn.commit()
            messagebox.showinfo("Success", "Department added successfully")
            dialog.destroy()
            self.refresh_department_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Department name already exists")
    
    def refresh_department_list(self):
        # Clear existing data
        for item in self.department_tree.get_children():
            self.department_tree.delete(item)
        
        # Get departments with head doctor names via LEFT JOIN
        self.cursor.execute("""
            SELECT d.id, d.name, doc.name as head_doctor, d.description
            FROM departments d
            LEFT JOIN doctors doc ON d.head_doctor_id = doc.id
        """)
        
        departments = self.cursor.fetchall()
        
        # Add to treeview
        for dept in departments:
            self.department_tree.insert("", END, values=dept)
    
    def edit_department(self):
        selected_item = self.department_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a department to edit")
            return
        
        dept_data = self.department_tree.item(selected_item)['values']
        
        dialog = Toplevel(self.root)
        dialog.title("Edit Department")
        dialog.geometry("500x400")
        dialog.resizable(True, True)
        
        # Form fields with current data
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        name_entry.insert(0, dept_data[1])
        
        Label(dialog, text="Head Doctor:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        
        # Get available doctors
        self.cursor.execute("SELECT id, name FROM doctors")
        doctors = self.cursor.fetchall()
        doctor_options = ["None"] + [f"{doc[0]} - {doc[1]}" for doc in doctors]
        
        # Find current head doctor if exists
        current_doctor = "None"
        if dept_data[2]:  # If there's a head doctor
            for doc in doctors:
                if doc[1] == dept_data[2]:
                    current_doctor = f"{doc[0]} - {doc[1]}"
                    break
        
        doctor_var = StringVar(value=current_doctor)
        doctor_dropdown = ttk.Combobox(dialog, textvariable=doctor_var, values=doctor_options, state="readonly")
        doctor_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Description:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        description_entry = Text(dialog, height=5, width=40)
        description_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        description_entry.insert("1.0", dept_data[3] if dept_data[3] else "")
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Update", command=lambda: self.update_department(
            dept_data[0],  # department_id
            name_entry.get(),
            doctor_var.get().split(" - ")[0] if doctor_var.get() != "None" else None,
            description_entry.get("1.0", END).strip(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def update_department(self, department_id, name, head_doctor_id, description, dialog):
        if not name:
            messagebox.showerror("Error", "Department name is required")
            return
        
        try:
            self.cursor.execute("""
                UPDATE departments 
                SET name = ?, head_doctor_id = ?, description = ?
                WHERE id = ?
            """, (name, head_doctor_id, description or None, department_id))
            self.conn.commit()
            messagebox.showinfo("Success", "Department updated successfully")
            dialog.destroy()
            self.refresh_department_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Department name already exists")
    
    def create_pharmacy_tab(self):
        self.pharmacy_tab = Frame(self.notebook)
        self.notebook.add(self.pharmacy_tab, text="Pharmacy")
        
        # Create pharmacy management widgets
        self.pharmacy_tree = ttk.Treeview(self.pharmacy_tab, columns=("ID", "Name", "Stock", "Price", "Expiry", "Supplier"), show="headings")
        
        # Configure columns
        self.pharmacy_tree.heading("ID", text="ID")
        self.pharmacy_tree.heading("Name", text="Name")
        self.pharmacy_tree.heading("Stock", text="Stock")
        self.pharmacy_tree.heading("Price", text="Price")
        self.pharmacy_tree.heading("Expiry", text="Expiry Date")
        self.pharmacy_tree.heading("Supplier", text="Supplier")
        
        # Set column widths
        self.pharmacy_tree.column("ID", width=50)
        self.pharmacy_tree.column("Name", width=200)
        self.pharmacy_tree.column("Stock", width=80)
        self.pharmacy_tree.column("Price", width=80)
        self.pharmacy_tree.column("Expiry", width=100)
        self.pharmacy_tree.column("Supplier", width=150)
        
        self.pharmacy_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Buttons frame
        button_frame = Frame(self.pharmacy_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        
        Button(button_frame, text="Add Medicine", command=self.show_add_medicine_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Edit Medicine", command=self.edit_medicine).pack(side=LEFT, padx=5)
        Button(button_frame, text="Restock", command=self.restock_medicine_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_pharmacy_list).pack(side=LEFT, padx=5)
        Button(button_frame, text="Search", command=self.search_medicine_dialog).pack(side=LEFT, padx=5)
        
        # Load initial pharmacy data
        self.refresh_pharmacy_list()
    
    def show_add_medicine_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add New Medicine")
        dialog.geometry("500x700")
        dialog.resizable(True, True)
        
        # Form fields
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Stock:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        stock_entry = Entry(dialog)
        stock_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Price:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        price_entry = Entry(dialog)
        price_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Expiry Date (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        expiry_entry = Entry(dialog)
        expiry_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Supplier:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        supplier_entry = Entry(dialog)
        supplier_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Save", command=lambda: self.save_medicine(
            name_entry.get(),
            stock_entry.get(),
            price_entry.get(),
            expiry_entry.get(),
            supplier_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def save_medicine(self, name, stock, price, expiry, supplier, dialog):
        # Validation
        if not name or not stock or not price:
            messagebox.showerror("Error", "Name, stock and price are required")
            return
        
        try:
            stock = int(stock)
            if stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Stock must be a positive integer")
            return
        
        try:
            price = float(price)
            if price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Price must be a positive number")
            return
        
        if expiry and not re.match(r'^\d{4}-\d{2}-\d{2}$', expiry):
            messagebox.showerror("Error", "Expiry date must be in YYYY-MM-DD format")
            return
        
        try:
            self.cursor.execute("""
                INSERT INTO pharmacy (medicine_name, stock, price, expiry_date, supplier)
                VALUES (?, ?, ?, ?, ?)
            """, (name, stock, price, expiry or None, supplier or None))
            self.conn.commit()
            messagebox.showinfo("Success", "Medicine added successfully")
            dialog.destroy()
            self.refresh_pharmacy_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Medicine name already exists")
    
    def refresh_pharmacy_list(self):
        # Clear existing data
        for item in self.pharmacy_tree.get_children():
            self.pharmacy_tree.delete(item)
        
        # Get all medicines
        self.cursor.execute("SELECT id, medicine_name, stock, price, expiry_date, supplier FROM pharmacy")
        medicines = self.cursor.fetchall()
        
        # Add to treeview
        for med in medicines:
            self.pharmacy_tree.insert("", END, values=med)
    
    def edit_medicine(self):
        selected_item = self.pharmacy_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a medicine to edit")
            return
        
        med_data = self.pharmacy_tree.item(selected_item)['values']
        
        dialog = Toplevel(self.root)
        dialog.title("Edit Medicine")
        dialog.geometry("500x700")
        dialog.resizable(True, True)
        
        # Form fields with current data
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        name_entry.insert(0, med_data[1])
        
        Label(dialog, text="Stock:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        stock_entry = Entry(dialog)
        stock_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        stock_entry.insert(0, med_data[2])
        
        Label(dialog, text="Price:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        price_entry = Entry(dialog)
        price_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        price_entry.insert(0, med_data[3])
        
        Label(dialog, text="Expiry Date (YYYY-MM-DD):").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        expiry_entry = Entry(dialog)
        expiry_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        expiry_entry.insert(0, med_data[4] if med_data[4] else "")
        
        Label(dialog, text="Supplier:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        supplier_entry = Entry(dialog)
        supplier_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        supplier_entry.insert(0, med_data[5] if med_data[5] else "")
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Update", command=lambda: self.update_medicine(
            med_data[0],  # medicine_id
            name_entry.get(),
            stock_entry.get(),
            price_entry.get(),
            expiry_entry.get(),
            supplier_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def update_medicine(self, medicine_id, name, stock, price, expiry, supplier, dialog):
        # Validation
        if not name or not stock or not price:
            messagebox.showerror("Error", "Name, stock and price are required")
            return
        
        try:
            stock = int(stock)
            if stock < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Stock must be a positive integer")
            return
        
        try:
            price = float(price)
            if price <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Price must be a positive number")
            return
        
        if expiry and not re.match(r'^\d{4}-\d{2}-\d{2}$', expiry):
            messagebox.showerror("Error", "Expiry date must be in YYYY-MM-DD format")
            return
        
        try:
            self.cursor.execute("""
                UPDATE pharmacy 
                SET medicine_name = ?, stock = ?, price = ?, expiry_date = ?, supplier = ?
                WHERE id = ?
            """, (name, stock, price, expiry or None, supplier or None, medicine_id))
            self.conn.commit()
            messagebox.showinfo("Success", "Medicine updated successfully")
            dialog.destroy()
            self.refresh_pharmacy_list()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error", "Medicine name already exists")
    
    def restock_medicine_dialog(self):
        selected_item = self.pharmacy_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a medicine to restock")
            return
        
        med_data = self.pharmacy_tree.item(selected_item)['values']
        
        dialog = Toplevel(self.root)
        dialog.title("Restock Medicine")
        dialog.geometry("300x200")
        dialog.resizable(True, True)
        
        Label(dialog, text=f"Medicine: {med_data[1]}").pack(pady=10)
        Label(dialog, text=f"Current Stock: {med_data[2]}").pack(pady=5)
        
        Label(dialog, text="Quantity to add:").pack(pady=10)
        quantity_entry = Entry(dialog)
        quantity_entry.pack(pady=5)
        
        button_frame = Frame(dialog)
        button_frame.pack(pady=20)
        
        Button(button_frame, text="Restock", command=lambda: self.restock_medicine(
            med_data[0],  # medicine_id
            med_data[2],  # current stock
            quantity_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def restock_medicine(self, medicine_id, current_stock, quantity, dialog):
        try:
            quantity = int(quantity)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Quantity must be a positive integer")
            return
        
        new_stock = int(current_stock) + quantity
        
        self.cursor.execute("UPDATE pharmacy SET stock = ? WHERE id = ?", 
                          (new_stock, medicine_id))
        self.conn.commit()
        messagebox.showinfo("Success", f"Medicine restocked successfully. New stock: {new_stock}")
        dialog.destroy()
        self.refresh_pharmacy_list()
    
    def search_medicine_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Search Medicines")
        dialog.geometry("400x700")
        dialog.resizable(True, True)
        
        Label(dialog, text="Search by:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        
        search_var = StringVar(value="name")
        Radiobutton(dialog, text="Name", variable=search_var, value="name").grid(row=1, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Supplier", variable=search_var, value="supplier").grid(row=2, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Low Stock (<10)", variable=search_var, value="low_stock").grid(row=3, column=0, padx=10, pady=5, sticky=W)
        
        Label(dialog, text="Search term:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        term_entry = Entry(dialog)
        term_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        
        button_frame = Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        Button(button_frame, text="Search", command=lambda: self.search_medicine(
            search_var.get(),
            term_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def search_medicine(self, search_by, term, dialog):
        # Clear existing data
        for item in self.pharmacy_tree.get_children():
            self.pharmacy_tree.delete(item)
        
        if search_by == "name":
            if not term:
                messagebox.showwarning("Warning", "Please enter a search term")
                return
            self.cursor.execute("SELECT * FROM pharmacy WHERE medicine_name LIKE ?", (f"%{term}%",))
        elif search_by == "supplier":
            if not term:
                messagebox.showwarning("Warning", "Please enter a search term")
                return
            self.cursor.execute("SELECT * FROM pharmacy WHERE supplier LIKE ?", (f"%{term}%",))
        elif search_by == "low_stock":
            self.cursor.execute("SELECT * FROM pharmacy WHERE stock < 10")
        
        medicines = self.cursor.fetchall()
        
        if not medicines:
            messagebox.showinfo("Info", "No matching medicines found")
            return
        
        # Add to treeview
        for med in medicines:
            self.pharmacy_tree.insert("", END, values=med)
        
        dialog.destroy()
    
    def issue_medicine(self, patient_id, medicine_id, quantity):
        try:
            # Check stock availability
            self.cursor.execute("SELECT stock FROM pharmacy WHERE id = ?", (medicine_id,))
            stock = self.cursor.fetchone()[0]
            if stock < quantity:
                messagebox.showerror("Error", "Not enough stock available")
                return

            # Update stock
            new_stock = stock - quantity
            self.cursor.execute("UPDATE pharmacy SET stock = ? WHERE id = ?", (new_stock, medicine_id))

            # Record issued medicine
            self.cursor.execute("""
                INSERT INTO issued_medicines (patient_id, medicine_id, issue_date)
                VALUES (?, ?, ?)
            """, (patient_id, medicine_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

            # Log the pharmacy stage in the patient journey
            self.cursor.execute(
                "INSERT INTO patient_journey (patient_id, stage, timestamp, details) VALUES (?, ?, ?, ?)",
                (patient_id, "Pharmacy", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"Issued {quantity} units of medicine ID {medicine_id}")
            )
            self.conn.commit()

            messagebox.showinfo("Success", "Medicine issued and patient journey updated.")
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to issue medicine: {e}")
        # ...existing code to check stock, update stock, etc...
        self.cursor.execute("""
            INSERT INTO issued_medicines (patient_id, medicine_id, issue_date)
            VALUES (?, ?, ?)
        """, (patient_id, medicine_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        self.conn.commit()

        # Log the pharmacy stage in the patient journey
        self.cursor.execute(
            "INSERT INTO patient_journey (patient_id, stage, timestamp, details) VALUES (?, ?, ?, ?)",
            (patient_id, "Pharmacy", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Medicine issued")
        )
        self.conn.commit()

        messagebox.showinfo("Success", "Medicine issued and patient journey updated.")

    
    def create_appointment_tab(self):
        self.appointment_tab = Frame(self.notebook)
        self.notebook.add(self.appointment_tab, text="Appointments")
        
        # Create appointment management widgets
        self.appointment_tree = ttk.Treeview(self.appointment_tab, columns=("ID", "Patient", "Doctor", "Date", "Status", "Notes"), show="headings")
        
        # Configure columns
        self.appointment_tree.heading("ID", text="ID")
        self.appointment_tree.heading("Patient", text="Patient")
        self.appointment_tree.heading("Doctor", text="Doctor")
        self.appointment_tree.heading("Date", text="Date")
        self.appointment_tree.heading("Status", text="Status")
        self.appointment_tree.heading("Notes", text="Notes")
        
        # Set column widths
        self.appointment_tree.column("ID", width=50)
        self.appointment_tree.column("Patient", width=150)
        self.appointment_tree.column("Doctor", width=150)
        self.appointment_tree.column("Date", width=150)
        self.appointment_tree.column("Status", width=100)
        self.appointment_tree.column("Notes", width=200)
        
        self.appointment_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Buttons frame
        button_frame = Frame(self.appointment_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        
        Button(button_frame, text="Schedule Appointment", command=self.show_schedule_appointment_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Update Status", command=self.update_appointment_status).pack(side=LEFT, padx=5)
        Button(button_frame, text="Cancel Appointment", command=self.cancel_appointment).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_appointment_list).pack(side=LEFT, padx=5)
        Button(button_frame, text="Search", command=self.search_appointment_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Export CSV", command=self.export_appointments_csv).pack(side=LEFT, padx=5)
            # Load initial appointment data
        self.refresh_appointment_list()
    
    def export_appointments_csv(self):
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if not file_path:
                return
            self.cursor.execute("""
                SELECT a.id, p.name, d.name, a.appointment_date, a.status, a.notes
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
            """)
            rows = self.cursor.fetchall()
            headers = ["ID", "Patient", "Doctor", "Date", "Status", "Notes"]
            with open(file_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            messagebox.showinfo("Export", f"Appointment data exported to {file_path}")


    def show_schedule_appointment_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Schedule Appointment")
        dialog.geometry("500x700")
        dialog.resizable(True, True)
        
        # Get available patients
        self.cursor.execute("SELECT id, name FROM patients")
        patients = self.cursor.fetchall()
        
        if not patients:
            messagebox.showwarning("Warning", "No patients available. Please add patients first.")
            dialog.destroy()
            return
        
        Label(dialog, text="Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        patient_var = StringVar()
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, 
                                      values=[f"{p[0]} - {p[1]}" for p in patients], 
                                      state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        
        # Get available doctors
        self.cursor.execute("SELECT id, name FROM doctors")
        doctors = self.cursor.fetchall()
        
        if not doctors:
            messagebox.showwarning("Warning", "No doctors available. Please add doctors first.")
            dialog.destroy()
            return
        
        Label(dialog, text="Doctor:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        doctor_var = StringVar()
        doctor_dropdown = ttk.Combobox(dialog, textvariable=doctor_var, 
                                      values=[f"{d[0]} - {d[1]}" for d in doctors], 
                                      state="readonly")
        doctor_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        
        Label(dialog, text="Date and Time:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        date_entry = Entry(dialog)
        date_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        date_entry.insert(0, datetime.now().strftime("%Y-%m-%d %H:%M"))
        
        Label(dialog, text="Notes:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        notes_entry = Text(dialog, height=5, width=40)
        notes_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        
        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        Button(button_frame, text="Schedule", command=lambda: self.save_appointment(
            patient_var.get().split(" - ")[0],
            doctor_var.get().split(" - ")[0],
            date_entry.get(),
            notes_entry.get("1.0", END).strip(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
        Button(button_frame, text="Export CSV", command=self.export_appointments_csv).pack(side=LEFT, padx=5)


    
    
    def save_appointment(self, patient_id, doctor_id, date_time, notes, dialog):
        if not patient_id or not doctor_id or not date_time:
            messagebox.showerror("Error", "Patient, doctor and date/time are required")
            return
        
        try:
            # Validate date format
            datetime.strptime(date_time, "%Y-%m-%d %H:%M")
        except ValueError:
            messagebox.showerror("Error", "Invalid date format. Please use YYYY-MM-DD HH:MM")
            return
        
        try:
            self.cursor.execute("""
                INSERT INTO appointments (patient_id, doctor_id, appointment_date, notes)
                VALUES (?, ?, ?, ?)
            """, (patient_id, doctor_id, date_time, notes or None))
            self.conn.commit()
            messagebox.showinfo("Success", "Appointment scheduled successfully")
            dialog.destroy()
            self.refresh_appointment_list()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")
    
    def refresh_appointment_list(self):
        # Clear existing data
        for item in self.appointment_tree.get_children():
            self.appointment_tree.delete(item)
        
        # Get appointments with patient and doctor names via JOIN
        self.cursor.execute("""
            SELECT a.id, p.name as patient, d.name as doctor, 
                   a.appointment_date, a.status, a.notes
            FROM appointments a
            JOIN patients p ON a.patient_id = p.id
            JOIN doctors d ON a.doctor_id = d.id
            ORDER BY a.appointment_date
        """)
        
        appointments = self.cursor.fetchall()
        
        # Add to treeview
        for appt in appointments:
            self.appointment_tree.insert("", END, values=appt)
    
    def update_appointment_status(self):
        selected_item = self.appointment_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an appointment to update")
            return
        
        appt_data = self.appointment_tree.item(selected_item)['values']
        appt_id = appt_data[0]
        
        dialog = Toplevel(self.root)
        dialog.title("Update Appointment Status")
        dialog.geometry("300x700")
        dialog.resizable(True, True)
        
        Label(dialog, text="Current Status:").pack(pady=10)
        Label(dialog, text=appt_data[4], font=("Arial", 12, "bold")).pack()
        
        Label(dialog, text="New Status:").pack(pady=10)
        status_var = StringVar(value=appt_data[4])
        status_frame = Frame(dialog)
        status_frame.pack()
        
        Radiobutton(status_frame, text="Scheduled", variable=status_var, value="Scheduled").grid(row=0, column=0, padx=5)
        Radiobutton(status_frame, text="Completed", variable=status_var, value="Completed").grid(row=0, column=1, padx=5)
        Radiobutton(status_frame, text="Cancelled", variable=status_var, value="Cancelled").grid(row=0, column=2, padx=5)
        
        button_frame = Frame(dialog)
        button_frame.pack(pady=20)
        
        Button(button_frame, text="Update", command=lambda: self.save_appointment_status(
            appt_id,
            status_var.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def save_appointment_status(self, appointment_id, status, dialog):
        self.cursor.execute("UPDATE appointments SET status = ? WHERE id = ?", 
                          (status, appointment_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Appointment status updated successfully")
        dialog.destroy()
        self.refresh_appointment_list()
    
    def cancel_appointment(self):
        selected_item = self.appointment_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select an appointment to cancel")
            return
        
        appt_data = self.appointment_tree.item(selected_item)['values']
        
        if appt_data[4] == "Cancelled":
            messagebox.showinfo("Info", "This appointment is already cancelled")
            return
        
        confirmation = messagebox.askyesno("Confirm", "Are you sure you want to cancel this appointment?")
        if confirmation:
            self.cursor.execute("UPDATE appointments SET status = 'Cancelled' WHERE id = ?", 
                              (appt_data[0],))
            self.conn.commit()
            messagebox.showinfo("Success", "Appointment cancelled successfully")
            self.refresh_appointment_list()
    
    def search_appointment_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Search Appointments")
        dialog.geometry("400x700")
        dialog.resizable(True, True)
        
        Label(dialog, text="Search by:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        
        search_var = StringVar(value="patient")
        Radiobutton(dialog, text="Patient", variable=search_var, value="patient").grid(row=1, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Doctor", variable=search_var, value="doctor").grid(row=2, column=0, padx=10, pady=5, sticky=W)
        Radiobutton(dialog, text="Date", variable=search_var, value="date").grid(row=3, column=0, padx=10, pady=5, sticky=W)
        
        Label(dialog, text="Search term:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        term_entry = Entry(dialog)
        term_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        
        button_frame = Frame(dialog)
        button_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        Button(button_frame, text="Search", command=lambda: self.search_appointment(
            search_var.get(),
            term_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)
        
        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)
    
    def search_appointment(self, search_by, term, dialog):
        if not term and search_by != "date":
            messagebox.showwarning("Warning", "Please enter a search term")
            return
        
        # Clear existing data
        for item in self.appointment_tree.get_children():
            self.appointment_tree.delete(item)
        
        if search_by == "patient":
            self.cursor.execute("""
                SELECT a.id, p.name as patient, d.name as doctor, 
                       a.appointment_date, a.status, a.notes
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE p.name LIKE ?
                ORDER BY a.appointment_date
            """, (f"%{term}%",))
        elif search_by == "doctor":
            self.cursor.execute("""
                SELECT a.id, p.name as patient, d.name as doctor, 
                       a.appointment_date, a.status, a.notes
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE d.name LIKE ?
                ORDER BY a.appointment_date
            """, (f"%{term}%",))
        elif search_by == "date":
            self.cursor.execute("""
                SELECT a.id, p.name as patient, d.name as doctor, 
                       a.appointment_date, a.status, a.notes
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                WHERE date(a.appointment_date) = ?
                ORDER BY a.appointment_date
            """, (term,))
        
        appointments = self.cursor.fetchall()
        
        if not appointments:
            messagebox.showinfo("Info", "No matching appointments found")
            return
        
        # Add to treeview
        for appt in appointments:
            self.appointment_tree.insert("", END, values=appt)
        
        dialog.destroy()
    
        def export_appointments_csv(self):
            file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
            if not file_path:
                return
            self.cursor.execute("""
                SELECT a.id, p.name, d.name, a.appointment_date, a.status, a.notes
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
            """)
            rows = self.cursor.fetchall()
            headers = ["ID", "Patient", "Doctor", "Date", "Status", "Notes"]
            with open(file_path, "w", newline='', encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)
            messagebox.showinfo("Export", f"Appointment data exported to {file_path}")


    def create_report_tab(self):
        self.report_tab = Frame(self.notebook)
        self.notebook.add(self.report_tab, text="Reports")

        # Create report generation widgets
        Label(self.report_tab, text="Generate Patient Report", font=("Arial", 16, "bold")).pack(pady=10)

        Label(self.report_tab, text="Select Patient:", font=("Arial", 12)).pack(pady=5)
        self.cursor.execute("SELECT id, name FROM patients")
        patients = self.cursor.fetchall()
        patient_options = [f"{p[0]} - {p[1]}" for p in patients]
        self.selected_patient_var = StringVar(value=patient_options[0] if patients else "")
        patient_dropdown = ttk.Combobox(self.report_tab, textvariable=self.selected_patient_var, values=patient_options, state="readonly")
        patient_dropdown.pack(pady=5)

        Button(self.report_tab, text="Generate Report", command=self.generate_patient_report).pack(pady=10)

        # Add Print Button
        Button(self.report_tab, text="Print Report", command=self.print_report).pack(pady=10)

        # Text area to display the report
        self.report_text = Text(self.report_tab, wrap=WORD, height=20, width=80)
        self.report_text.pack(pady=10)

    def generate_patient_report(self):
        selected_patient = self.selected_patient_var.get()
        if not selected_patient:
            messagebox.showwarning("Warning", "Please select a patient to generate the report")
            return

        patient_id = selected_patient.split(" - ")[0]

        try:
            # Fetch patient details
            self.cursor.execute("""
                SELECT p.name, p.age, p.gender, p.contact, p.department, d.name as doctor_name, p.admission_date, p.discharge_date
                FROM patients p
                LEFT JOIN doctors d ON p.doctor_id = d.id
                WHERE p.id = ?
            """, (patient_id,))
            patient = self.cursor.fetchone()

            # Fetch recommended medicines
            self.cursor.execute("""
                SELECT m.medicine_name, m.price, m.supplier
                FROM issued_medicines im
                JOIN pharmacy m ON im.medicine_id = m.id
                WHERE im.patient_id = ?
            """, (patient_id,))
            medicines = self.cursor.fetchall()

            # Generate report
            report = f"Patient Report\n{'='*50}\n"
            report += f"Name: {patient[0]}\n"
            report += f"Age: {patient[1]}\n"
            report += f"Gender: {patient[2]}\n"
            report += f"Contact: {patient[3]}\n"
            report += f"Department: {patient[4]}\n"
            report += f"Doctor: {patient[5]}\n"
            report += f"Admission Date: {patient[6]}\n"
            report += f"Discharge Date: {patient[7] if patient[7] else 'N/A'}\n\n"

            report += "Medicines Recommended:\n"
            if medicines:
                for med in medicines:
                    report += f"- {med[0]} (Price: {med[1]}, Supplier: {med[2]})\n"
            else:
                report += "No medicines recommended.\n"

            # Display report in the text area
            self.report_text.delete(1.0, END)
            self.report_text.insert(END, report)

            # Save the report to a temporary file for printing
            with open("patient_report.txt", "w") as file:
                file.write(report)

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to generate report: {e}")

    def print_report(self):
        try:
            # Open the report file in the default text editor for printing
            os.startfile("patient_report.txt", "print")
            # Clear the text area after printing
            self.report_text.delete(1.0, END)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print the report: {e}")

    def create_admissions_tab(self):
        self.admissions_tab = Frame(self.notebook)
        self.notebook.add(self.admissions_tab, text="Admissions")

        # Frame for analytics
        analytics_frame = Frame(self.admissions_tab)
        analytics_frame.pack(fill=X, padx=10, pady=10)
        button_frame = Frame(self.admissions_tab)
        button_frame.pack(fill=X, padx=10, pady=5)
        Button(button_frame, text="Refresh", command=self.refresh_admissions_data).pack(side=LEFT, padx=5)

        # Total admissions
        self.total_admissions_var = StringVar(value="0")
        Label(analytics_frame, text="Total Admissions:", font=("Arial", 12)).grid(row=0, column=0, sticky=W, padx=5)
        Label(analytics_frame, textvariable=self.total_admissions_var, font=("Arial", 12, "bold")).grid(row=0, column=1, sticky=W, padx=5)

        # Currently admitted patients
        self.current_admissions_var = StringVar(value="0")
        Label(analytics_frame, text="Currently Admitted:", font=("Arial", 12)).grid(row=1, column=0, sticky=W, padx=5)
        Label(analytics_frame, textvariable=self.current_admissions_var, font=("Arial", 12, "bold")).grid(row=1, column=1, sticky=W, padx=5)

        # Total discharges
        self.total_discharges_var = StringVar(value="0")
        Label(analytics_frame, text="Total Discharges:", font=("Arial", 12)).grid(row=2, column=0, sticky=W, padx=5)
        Label(analytics_frame, textvariable=self.total_discharges_var, font=("Arial", 12, "bold")).grid(row=2, column=1, sticky=W, padx=5)

        # Admissions log table
        admissions_frame = Frame(self.admissions_tab)
        admissions_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.admissions_tree = ttk.Treeview(admissions_frame, columns=("ID", "Patient", "Department", "Doctor", "Admission Date", "Discharge Date"), show="headings")
        self.admissions_tree.heading("ID", text="ID")
        self.admissions_tree.heading("Patient", text="Patient")
        self.admissions_tree.heading("Department", text="Department")
        self.admissions_tree.heading("Doctor", text="Doctor")
        self.admissions_tree.heading("Admission Date", text="Admission Date")
        self.admissions_tree.heading("Discharge Date", text="Discharge Date")

        self.admissions_tree.column("ID", width=50)
        self.admissions_tree.column("Patient", width=150)
        self.admissions_tree.column("Department", width=120)
        self.admissions_tree.column("Doctor", width=150)
        self.admissions_tree.column("Admission Date", width=150)
        self.admissions_tree.column("Discharge Date", width=150)

        self.admissions_tree.pack(fill=BOTH, expand=True)

        # Load initial data
        self.refresh_admissions_data()
    
    def refresh_admissions_data(self):
        try:
            # Clear existing data
            for item in self.admissions_tree.get_children():
                self.admissions_tree.delete(item)

            # Fetch admissions log
            self.cursor.execute("""
                SELECT al.id, p.name, al.department, d.name as doctor_name, al.admission_date, al.discharge_date
                FROM admissions_log al
                JOIN patients p ON al.patient_id = p.id
                LEFT JOIN doctors d ON al.doctor_id = d.id
            """)
            admissions = self.cursor.fetchall()

            # Populate the table
            for admission in admissions:
                self.admissions_tree.insert("", END, values=admission)

            # Update analytics
            self.cursor.execute("SELECT COUNT(*) FROM admissions_log")
            self.total_admissions_var.set(self.cursor.fetchone()[0])

            self.cursor.execute("SELECT COUNT(*) FROM admissions_log WHERE discharge_date IS NULL")
            self.current_admissions_var.set(self.cursor.fetchone()[0])

            self.cursor.execute("SELECT COUNT(*) FROM admissions_log WHERE discharge_date IS NOT NULL")
            self.total_discharges_var.set(self.cursor.fetchone()[0])

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to refresh admissions data: {e}")        

    def create_billing_tab(self):
        self.billing_tab = Frame(self.notebook)
        self.notebook.add(self.billing_tab, text="Billing & Collection")

        # Frame for billing table
        billing_frame = Frame(self.billing_tab)
        billing_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)

        self.billing_tree = ttk.Treeview(billing_frame, columns=("ID", "Patient", "Description", "Amount", "Date"), show="headings")
        self.billing_tree.heading("ID", text="ID")
        self.billing_tree.heading("Patient", text="Patient")
        self.billing_tree.heading("Description", text="Description")
        self.billing_tree.heading("Amount", text="Amount")
        self.billing_tree.heading("Date", text="Date")

        self.billing_tree.column("ID", width=50)
        self.billing_tree.column("Patient", width=150)
        self.billing_tree.column("Description", width=200)
        self.billing_tree.column("Amount", width=100)
        self.billing_tree.column("Date", width=150)

        self.billing_tree.pack(fill=BOTH, expand=True)

        # Buttons frame
        button_frame = Frame(self.billing_tab)
        button_frame.pack(fill=X, padx=10, pady=10)

        Button(button_frame, text="Add Transaction", command=self.show_add_transaction_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Generate Invoice", command=self.generate_invoice_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_billing_data).pack(side=LEFT, padx=5)
        Button(button_frame, text="Export CSV", command=self.export_billing_csv).pack(side=LEFT, padx=5)

        # Load initial billing data
        # Ensure the billing table has the required columns
        try:
            self.cursor.execute("ALTER TABLE billing ADD COLUMN date TEXT")
            self.conn.commit()
        except sqlite3.OperationalError:
            # Column already exists
            pass

        self.refresh_billing_data()

    def export_billing_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return
        self.cursor.execute("""
            SELECT b.id, p.name, b.description, b.amount, b.date
            FROM billing b
            JOIN patients p ON b.patient_id = p.id
        """)
        rows = self.cursor.fetchall()
        headers = ["ID", "Patient", "Description", "Amount", "Date"]
        with open(file_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        messagebox.showinfo("Export", f"Billing data exported to {file_path}")
        

    def show_add_transaction_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Transaction")
        dialog.geometry("500x400")
        dialog.resizable(True, True)

        # Get available patients
        self.cursor.execute("SELECT id, name FROM patients")
        patients = self.cursor.fetchall()

        if not patients:
            messagebox.showwarning("Warning", "No patients available. Please add patients first.")
            dialog.destroy()
            return

        Label(dialog, text="Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        patient_var = StringVar()
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, 
                                        values=[f"{p[0]} - {p[1]}" for p in patients], 
                                        state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Description:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        description_entry = Entry(dialog)
        description_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Amount:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        amount_entry = Entry(dialog)
        amount_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)

        Button(button_frame, text="Save", command=lambda: self.save_transaction(
            patient_var.get().split(" - ")[0],
            description_entry.get(),
            amount_entry.get(),
            dialog
        )).pack(side=LEFT, padx=10)

        Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)

    def save_transaction(self, patient_id, description, amount, dialog):
        if not patient_id or not description or not amount:
            messagebox.showerror("Error", "All fields are required")
            return

        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Amount must be a positive number")
            return

        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Insert transaction into the database
        try:
            self.cursor.execute("""
                INSERT INTO billing (patient_id, description, amount, date)
                VALUES (?, ?, ?, ?)
            """, (patient_id, description, amount, date))
            self.conn.commit()
            messagebox.showinfo("Success", "Transaction added successfully")
            dialog.destroy()
            self.refresh_billing_data()
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}")

    def refresh_billing_data(self):
        try:
            # Clear existing data
            for item in self.billing_tree.get_children():
                self.billing_tree.delete(item)

            # Fetch billing data
            self.cursor.execute("""
                SELECT b.id, p.name, b.description, b.amount, b.date
                FROM billing b
                JOIN patients p ON b.patient_id = p.id
            """)
            transactions = self.cursor.fetchall()

            # Populate the table
            for transaction in transactions:
                self.billing_tree.insert("", END, values=transaction)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to refresh billing data: {e}")

        def update_billing_table(self):
            try:
                # Add the 'description' column if it doesn't exist
                self.cursor.execute("ALTER TABLE billing ADD COLUMN description, date TEXT NOT NULL DEFAULT ''")
                self.conn.commit()
            except sqlite3.OperationalError:
                # Column already exists
                pass       

    def generate_invoice_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Generate Invoice")
        dialog.geometry("500x400")
        dialog.resizable(True, True)

        # Get available patients
        self.cursor.execute("SELECT id, name FROM patients")
        patients = self.cursor.fetchall()

        if not patients:
            messagebox.showwarning("Warning", "No patients available. Please add patients first.")
            dialog.destroy()
            return

        Label(dialog, text="Select Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        patient_var = StringVar()
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, 
                                        values=[f"{p[0]} - {p[1]}" for p in patients], 
                                        state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        # Buttons
        button_frame = Frame(dialog)
        button_frame.grid(row=1, column=0, columnspan=2, pady=20)

        Button(button_frame, text="Generate", command=lambda: self.generate_invoice(
                    patient_var.get().split(" - ")[0],
                    dialog
                )).pack(side=LEFT, padx=10)

    def generate_invoice(self, patient_id, dialog):
                button_frame = Frame(dialog)
                button_frame.grid(row=1, column=0, columnspan=2, pady=20)

                Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=LEFT, padx=10)

                
                try:
                    # Fetch patient details
                    self.cursor.execute("SELECT name FROM patients WHERE id = ?", (patient_id,))
                    patient_name = self.cursor.fetchone()[0]
        
                    # Fetch billing transactions for the patient
                    self.cursor.execute("""
                        SELECT description, amount, date
                        FROM billing
                        WHERE patient_id = ?
                    """, (patient_id,))
                    transactions = self.cursor.fetchall()
        
                    if not transactions:
                        messagebox.showinfo("Info", "No transactions found for the selected patient")
                        return
        
                    # Generate invoice content
                    invoice = f"Invoice for {patient_name}\n{'='*50}\n"
                    total_amount = 0
                    for desc, amount, date in transactions:
                        invoice += f"{date}: {desc} - ${amount:.2f}\n"
                        total_amount += amount
                    invoice += f"\nTotal Amount: ${total_amount:.2f}\n"
        
                    # Save invoice to a file
                    invoice_file = filedialog.asksaveasfilename(
                        defaultextension=".txt",
                        filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                        title="Save Invoice As"
                    )
                    if invoice_file:
                        with open(invoice_file, "w") as file:
                            file.write(invoice)
                        messagebox.showinfo("Success", "Invoice generated and saved successfully")
                        dialog.destroy()
        
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Failed to generate invoice: {e}")
      
    def create_dashboard_tab(self):
        self.dashboard_tab = Frame(self.notebook)
        self.notebook.add(self.dashboard_tab, text="Analytics Dashboard")

        # Button frame for refresh
        button_frame = Frame(self.dashboard_tab)
        button_frame.pack(fill=X, padx=10, pady=5)
        Button(button_frame, text="Refresh", command=self.refresh_dashboard_charts).pack(side=LEFT, padx=5)

        # Create a notebook inside the dashboard for multiple charts
        self.chart_notebook = ttk.Notebook(self.dashboard_tab)
        self.chart_notebook.pack(fill=BOTH, expand=True)
        self.refresh_dashboard_charts()

    def refresh_dashboard_charts(self):
        # Clear previous tabs
        for tab in self.chart_notebook.winfo_children():
            tab.destroy()

        # --- Patient Demographics ---
        demo_frame = Frame(self.chart_notebook)
        self.chart_notebook.add(demo_frame, text="Patient Demographics")

        fig1, axs1 = plt.subplots(1, 3, figsize=(12, 4))
        fig1.tight_layout(pad=3.0)

        # Age distribution
        self.cursor.execute("SELECT age FROM patients")
        ages = [row[0] for row in self.cursor.fetchall()]
        axs1[0].hist(ages, bins=range(0, 120, 10), color='skyblue', edgecolor='black')
        axs1[0].set_title("Age Distribution")
        axs1[0].set_xlabel("Age")
        axs1[0].set_ylabel("Count")

        # Gender distribution
        self.cursor.execute("SELECT gender FROM patients")
        genders = [row[0] for row in self.cursor.fetchall()]
        gender_counts = {g: genders.count(g) for g in set(genders)}
        axs1[1].pie(gender_counts.values(), labels=gender_counts.keys(), autopct='%1.1f%%', startangle=90)
        axs1[1].set_title("Gender Distribution")

        # Department distribution
        self.cursor.execute("SELECT department FROM patients")
        departments = [row[0] for row in self.cursor.fetchall()]
        dept_counts = {d: departments.count(d) for d in set(departments)}
        axs1[2].bar(dept_counts.keys(), dept_counts.values(), color='orange')
        axs1[2].set_title("Department Distribution")
        axs1[2].set_xticklabels(dept_counts.keys(), rotation=45, ha='right')

        canvas1 = FigureCanvasTkAgg(fig1, master=demo_frame)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=BOTH, expand=True)

        # --- Revenue Trends ---
        revenue_frame = Frame(self.chart_notebook)
        self.chart_notebook.add(revenue_frame, text="Revenue Trends")

        fig2, ax2 = plt.subplots(figsize=(7, 4))
        self.cursor.execute("""
            SELECT strftime('%Y-%m', date), SUM(amount)
            FROM billing
            GROUP BY strftime('%Y-%m', date)
            ORDER BY strftime('%Y-%m', date)
        """)
        data = self.cursor.fetchall()
        months = [row[0] for row in data]
        totals = [row[1] for row in data]
        ax2.plot(months, totals, marker='o', color='green')
        ax2.set_title("Monthly Revenue")
        ax2.set_xlabel("Month")
        ax2.set_ylabel("Total Revenue")
        ax2.tick_params(axis='x', rotation=45)
        canvas2 = FigureCanvasTkAgg(fig2, master=revenue_frame)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=BOTH, expand=True)

        # --- Appointment Statistics ---
        appt_frame = Frame(self.chart_notebook)
        self.chart_notebook.add(appt_frame, text="Appointment Stats")

        fig3, ax3 = plt.subplots(figsize=(5, 4))
        self.cursor.execute("""
            SELECT status, COUNT(*) FROM appointments GROUP BY status
        """)
        appt_data = self.cursor.fetchall()
        statuses = [row[0] for row in appt_data]
        counts = [row[1] for row in appt_data]
        ax3.bar(statuses, counts, color=['blue', 'red', 'gray'])
        ax3.set_title("Appointment Status Counts")
        ax3.set_xlabel("Status")
        ax3.set_ylabel("Count")
        canvas3 = FigureCanvasTkAgg(fig3, master=appt_frame)
        canvas3.draw()
        canvas3.get_tk_widget().pack(fill=BOTH, expand=True)
    
    
    

    def show_reception_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Reception - Patient Check-in")
        dialog.geometry("400x250")
        dialog.resizable(True, True)

        # Select patient
        self.cursor.execute("SELECT id, name FROM patients WHERE admission_date IS NOT NULL AND discharge_date IS NULL")
        patients = self.cursor.fetchall()
        if not patients:
            messagebox.showwarning("Warning", "No admitted patients found.")
            dialog.destroy()
            return

        Label(dialog, text="Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        patient_var = StringVar()
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, values=[f"{p[0]} - {p[1]}" for p in patients], state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Payment Method:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        payment_var = StringVar(value="Cash")
        payment_dropdown = ttk.Combobox(dialog, textvariable=payment_var, values=["Cash", "Insurance", "Mpesa", "Card"], state="readonly")
        payment_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Check-in", command=lambda: self.reception_checkin(
            patient_var.get().split(" - ")[0],
            payment_var.get(),
            dialog
        )).grid(row=2, column=0, columnspan=2, pady=20)

    def reception_checkin(self, patient_id, payment_method, dialog):
        try:
            self.cursor.execute("UPDATE patients SET payment_method = ? WHERE id = ?", (payment_method, patient_id))
            self.cursor.execute(
                "INSERT INTO patient_journey (patient_id, stage, timestamp, details) VALUES (?, ?, ?, ?)",
                (patient_id, "Reception", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"Payment: {payment_method}")
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Patient checked in at Reception.")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to check in: {e}")        

    def show_triage_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Triage - Patient Assessment")
        dialog.geometry("400x300")
        dialog.resizable(True, True)

        # Select patient
        self.cursor.execute("SELECT id, name FROM patients WHERE admission_date IS NOT NULL AND discharge_date IS NULL")
        patients = self.cursor.fetchall()
        if not patients:
            messagebox.showwarning("Warning", "No admitted patients found.")
            dialog.destroy()
            return

        Label(dialog, text="Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        patient_var = StringVar()
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, values=[f"{p[0]} - {p[1]}" for p in patients], state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Vitals/Notes:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        notes_entry = Text(dialog, height=5, width=30)
        notes_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Record Triage", command=lambda: self.triage_record(
            patient_var.get().split(" - ")[0],
            notes_entry.get("1.0", END).strip(),
            dialog
        )).grid(row=2, column=0, columnspan=2, pady=20)

    def triage_record(self, patient_id, notes, dialog):
        try:
            self.cursor.execute(
                "INSERT INTO patient_journey (patient_id, stage, timestamp, details) VALUES (?, ?, ?, ?)",
                (patient_id, "Triage", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), notes)
            )
            self.conn.commit()
            messagebox.showinfo("Success", "Triage recorded.")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record triage: {e}")        

    def show_patient_journey(self, patient_id):
        dialog = Toplevel(self.root)
        dialog.title("Patient Journey")
        dialog.geometry("600x400")
        dialog.resizable(True, True)

        tree = ttk.Treeview(dialog, columns=("Stage", "Timestamp", "Details"), show="headings")
        tree.heading("Stage", text="Stage")
        tree.heading("Timestamp", text="Timestamp")
        tree.heading("Details", text="Details")
        tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Ensure the patient_journey table exists
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patient_journey (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                stage TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                details TEXT,
                FOREIGN KEY (patient_id) REFERENCES patients (id)
            )
        """)
        self.conn.commit()

        # Fetch patient journey data
        self.cursor.execute("SELECT stage, timestamp, details FROM patient_journey WHERE patient_id = ? ORDER BY timestamp", (patient_id,))
        for row in self.cursor.fetchall():
            tree.insert("", END, values=row)
        
    def complete_appointment(self, patient_id, doctor_id, notes):
        # ...existing code to mark appointment as completed...
        self.cursor.execute(
            "INSERT INTO patient_journey (patient_id, stage, timestamp, details) VALUES (?, ?, ?, ?)",
            (patient_id, "Doctor", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), f"Seen by doctor {doctor_id}: {notes}")
        )
        self.conn.commit()
    def get_selected_patient_id(self):
        selected_item = self.patient_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a patient")
            return None
        patient_data = self.patient_tree.item(selected_item)['values']
        return patient_data[0]

    from tkinter import filedialog


    def show_email_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Send Email")
        dialog.geometry("400x400")
        dialog.resizable(True, True)

        Label(dialog, text="To:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        to_entry = Entry(dialog, width=40)
        to_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Subject:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        subject_entry = Entry(dialog, width=40)
        subject_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Message:").grid(row=2, column=0, padx=10, pady=10, sticky=NW)
        message_text = Text(dialog, width=40, height=10)
        message_text.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Send", command=lambda: self.send_email(
            to_entry.get(),
            subject_entry.get(),
            message_text.get("1.0", END),
            dialog
        )).grid(row=3, column=0, columnspan=2, pady=20)

    def send_email(self, to_addr, subject, message, dialog):
        # Configure your SMTP settings for Gmail
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "afyaadmin@gmail.com"
        sender_password = ""  # Generate an App Password from your Google Account (https://myaccount.google.com/apppasswords)

        if not to_addr or not subject or not message.strip():
            messagebox.showerror("Error", "All fields are required")
            return

        try:
            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = to_addr
            msg["Subject"] = subject
            msg.attach(MIMEText(message, "plain"))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, to_addr, msg.as_string())
            server.quit()
            messagebox.showinfo("Success", "Email sent successfully")
            dialog.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send email: {e}")

    def create_asset_tab(self):
        self.asset_tab = Frame(self.notebook)
        self.notebook.add(self.asset_tab, text="Asset Management")

        # Asset Treeview
        self.asset_tree = ttk.Treeview(self.asset_tab, columns=("ID", "Name", "Category", "Status", "Location", "Assigned To", "Notes"), show="headings")
        for col in ("ID", "Name", "Category", "Status", "Location", "Assigned To", "Notes"):
            self.asset_tree.heading(col, text=col)
            self.asset_tree.column(col, width=100)
        self.asset_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Buttons
        button_frame = Frame(self.asset_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        Button(button_frame, text="Add Asset", command=self.show_add_asset_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Edit Asset", command=self.edit_asset).pack(side=LEFT, padx=5)
        Button(button_frame, text="Delete Asset", command=self.delete_asset).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_asset_list).pack(side=LEFT, padx=5)

        self.refresh_asset_list()

    def show_add_asset_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Asset")
        dialog.geometry("400x400")
        dialog.resizable(True, True)

        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Category:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        category_entry = Entry(dialog)
        category_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Status:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        status_var = StringVar(value="Available")
        status_dropdown = ttk.Combobox(dialog, textvariable=status_var, values=["Available", "In Use", "Maintenance", "Out of Service"], state="readonly")
        status_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Location:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        location_entry = Entry(dialog)
        location_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Assigned To:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        assigned_entry = Entry(dialog)
        assigned_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Notes:").grid(row=5, column=0, padx=10, pady=10, sticky=W)
        notes_entry = Entry(dialog)
        notes_entry.grid(row=5, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Save", command=lambda: self.save_asset(
            name_entry.get(),
            category_entry.get(),
            status_var.get(),
            location_entry.get(),
            assigned_entry.get(),
            notes_entry.get(),
            dialog
        )).grid(row=6, column=0, columnspan=2, pady=20)

    def save_asset(self, name, category, status, location, assigned_to, notes, dialog):
        if not name or not category or not status:
            messagebox.showerror("Error", "Name, category, and status are required")
            return
        self.cursor.execute("""
            INSERT INTO assets (name, category, status, location, assigned_to, notes)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, category, status, location, assigned_to, notes))
        self.conn.commit()
        messagebox.showinfo("Success", "Asset added successfully")
        dialog.destroy()
        self.refresh_asset_list()

    def refresh_asset_list(self):
        for item in self.asset_tree.get_children():
            self.asset_tree.delete(item)
        self.cursor.execute("SELECT id, name, category, status, location, assigned_to, notes FROM assets")
        for asset in self.cursor.fetchall():
            self.asset_tree.insert("", END, values=asset)

    def edit_asset(self):
        selected = self.asset_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an asset to edit")
            return
        asset_data = self.asset_tree.item(selected)['values']
        dialog = Toplevel(self.root)
        dialog.title("Edit Asset")
        dialog.geometry("400x400")
        dialog.resizable(True, True)

        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        name_entry.insert(0, asset_data[1])

        Label(dialog, text="Category:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        category_entry = Entry(dialog)
        category_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        category_entry.insert(0, asset_data[2])

        Label(dialog, text="Status:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        status_var = StringVar(value=asset_data[3])
        status_dropdown = ttk.Combobox(dialog, textvariable=status_var, values=["Available", "In Use", "Maintenance", "Out of Service"], state="readonly")
        status_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Location:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        location_entry = Entry(dialog)
        location_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        location_entry.insert(0, asset_data[4])

        Label(dialog, text="Assigned To:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        assigned_entry = Entry(dialog)
        assigned_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
        assigned_entry.insert(0, asset_data[5])

        Label(dialog, text="Notes:").grid(row=5, column=0, padx=10, pady=10, sticky=W)
        notes_entry = Entry(dialog)
        notes_entry.grid(row=5, column=1, padx=10, pady=10, sticky=EW)
        notes_entry.insert(0, asset_data[6])

        Button(dialog, text="Update", command=lambda: self.update_asset(
            asset_data[0],
            name_entry.get(),
            category_entry.get(),
            status_var.get(),
            location_entry.get(),
            assigned_entry.get(),
            notes_entry.get(),
            dialog
        )).grid(row=6, column=0, columnspan=2, pady=20)

    def update_asset(self, asset_id, name, category, status, location, assigned_to, notes, dialog):
        if not name or not category or not status:
            messagebox.showerror("Error", "Name, category, and status are required")
            return
        self.cursor.execute("""
            UPDATE assets SET name=?, category=?, status=?, location=?, assigned_to=?, notes=?
            WHERE id=?
        """, (name, category, status, location, assigned_to, notes, asset_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Asset updated successfully")
        dialog.destroy()
        self.refresh_asset_list()

    def delete_asset(self):
        selected = self.asset_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select an asset to delete")
            return
        asset_data = self.asset_tree.item(selected)['values']
        confirm = messagebox.askyesno("Confirm", f"Delete asset '{asset_data[1]}'?")
        if confirm:
            self.cursor.execute("DELETE FROM assets WHERE id=?", (asset_data[0],))
            self.conn.commit()
            self.refresh_asset_list()
    
    def allocate_bed_dialog(self):
        selected_item = self.patient_tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a patient")
            return
        patient_data = self.patient_tree.item(selected_item)['values']
        patient_id = patient_data[0]
        # Check if inpatient
        self.cursor.execute("SELECT patient_type FROM patients WHERE id=?", (patient_id,))
        ptype = self.cursor.fetchone()
        if not ptype or ptype[0] != "Inpatient":
            messagebox.showinfo("Info", "Bed allocation is only for inpatients.")
            return

        dialog = Toplevel(self.root)
        dialog.title("Allocate Bed")
        dialog.geometry("400x300")
        dialog.resizable(True, True)

        # List available beds
        self.cursor.execute("SELECT id, ward, bed_number FROM beds WHERE status='Available'")
        beds = self.cursor.fetchall()
        if not beds:
            messagebox.showinfo("Info", "No available beds.")
            dialog.destroy()
            return

        bed_var = StringVar()
        bed_dropdown = ttk.Combobox(dialog, textvariable=bed_var, values=[f"{b[0]} - Ward {b[1]} Bed {b[2]}" for b in beds], state="readonly")
        bed_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        Label(dialog, text="Select Bed:").grid(row=0, column=0, padx=10, pady=10, sticky=W)

        Button(dialog, text="Allocate", command=lambda: self.allocate_bed(
            patient_id, bed_var.get().split(" - ")[0], dialog
        )).grid(row=1, column=0, columnspan=2, pady=20)

    def allocate_bed(self, patient_id, bed_id, dialog):
        admission_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("UPDATE beds SET status='Occupied', patient_id=?, admission_date=? WHERE id=?", (patient_id, admission_date, bed_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Bed allocated successfully.")
        dialog.destroy()

    def create_bed_tab(self):
        self.bed_tab = Frame(self.notebook)
        self.notebook.add(self.bed_tab, text="Bed/Ward Management")
        self.bed_tree = ttk.Treeview(self.bed_tab, columns=("ID", "Ward", "Bed", "Status", "Patient", "Admission", "Discharge"), show="headings")
        for col in ("ID", "Ward", "Bed", "Status", "Patient", "Admission", "Discharge"):
            self.bed_tree.heading(col, text=col)
            self.bed_tree.column(col, width=100)
        self.bed_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)
        button_frame = Frame(self.bed_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        Button(button_frame, text="Add Bed", command=self.show_add_bed_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_bed_list).pack(side=LEFT, padx=5)
        self.refresh_bed_list()

    def show_add_bed_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Bed")
        dialog.geometry("300x200")
        Label(dialog, text="Ward:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        ward_entry = Entry(dialog)
        ward_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        Label(dialog, text="Bed Number:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        bed_entry = Entry(dialog)
        bed_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        Button(dialog, text="Save", command=lambda: self.save_bed(ward_entry.get(), bed_entry.get(), dialog)).grid(row=2, column=0, columnspan=2, pady=20)

    def save_bed(self, ward, bed_number, dialog):
        self.cursor.execute("INSERT INTO beds (ward, bed_number) VALUES (?, ?)", (ward, bed_number))
        self.conn.commit()
        messagebox.showinfo("Success", "Bed added.")
        dialog.destroy()
        self.refresh_bed_list()

    def refresh_bed_list(self):
        for item in self.bed_tree.get_children():
            self.bed_tree.delete(item)
        self.cursor.execute("""
            SELECT b.id, b.ward, b.bed_number, b.status, p.name, b.admission_date, b.discharge_date
            FROM beds b LEFT JOIN patients p ON b.patient_id = p.id
        """)
        for row in self.cursor.fetchall():
            self.bed_tree.insert("", END, values=row)

    def create_laboratory_tab(self):
        self.laboratory_tab = Frame(self.notebook)
        self.notebook.add(self.laboratory_tab, text="Laboratory Management")

        # Lab Treeview
        self.lab_tree = ttk.Treeview(self.laboratory_tab, columns=("ID", "Patient", "Test Type", "Request Date", "Result Date", "Result", "Status"), show="headings")
        for col in ("ID", "Patient", "Test Type", "Request Date", "Result Date", "Result", "Status"):
            self.lab_tree.heading(col, text=col)
            self.lab_tree.column(col, width=120)
        self.lab_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Buttons
        button_frame = Frame(self.laboratory_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        Button(button_frame, text="Add Lab Request", command=self.show_add_lab_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Enter Result", command=self.show_enter_result_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Print Report", command=self.print_lab_report).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_lab_list).pack(side=LEFT, padx=5)
        Button(button_frame, text="Advanced Filter", command=self.show_lab_advanced_filter).pack(side=LEFT, padx=5)
        self.refresh_lab_list()

    def show_lab_advanced_filter(self):
        dialog = Toplevel(self.root)
        dialog.title("Advanced Lab Filter")
        dialog.geometry("400x350")
        dialog.resizable(True, True)

        # Patient filter
        Label(dialog, text="Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        self.cursor.execute("SELECT id, name FROM patients")
        patients = self.cursor.fetchall()
        patient_var = StringVar(value="")
        patient_options = [""] + [f"{p[0]} - {p[1]}" for p in patients]
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, values=patient_options, state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        # Test type filter
        Label(dialog, text="Test Type:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        test_type_entry = Entry(dialog)
        test_type_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        # Status filter
        Label(dialog, text="Status:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        status_var = StringVar(value="")
        status_dropdown = ttk.Combobox(dialog, textvariable=status_var, values=["", "Pending", "Completed"], state="readonly")
        status_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        # Date range filter
        Label(dialog, text="From Date:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        from_date = DateEntry(dialog, date_pattern="yyyy-mm-dd")
        from_date.grid(row=3, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="To Date:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        to_date = DateEntry(dialog, date_pattern="yyyy-mm-dd")
        to_date.grid(row=4, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Apply Filter", command=lambda: self.apply_lab_advanced_filter(
            patient_var.get().split(" - ")[0] if patient_var.get() else None,
            test_type_entry.get(),
            status_var.get(),
            from_date.get_date().strftime("%Y-%m-%d"),
            to_date.get_date().strftime("%Y-%m-%d"),
            dialog
        )).grid(row=5, column=0, columnspan=2, pady=20)

    def apply_lab_advanced_filter(self, patient_id, test_type, status, from_date, to_date, dialog):
        query = """
            SELECT l.id, p.name, l.test_type, l.request_date, l.result_date, l.result, l.status
            FROM laboratory l
            JOIN patients p ON l.patient_id = p.id
            WHERE 1=1
        """
        params = []
        if patient_id:
            query += " AND l.patient_id = ?"
            params.append(patient_id)
        if test_type:
            query += " AND l.test_type LIKE ?"
            params.append(f"%{test_type}%")
        if status:
            query += " AND l.status = ?"
            params.append(status)
        if from_date:
            query += " AND date(l.request_date) >= ?"
            params.append(from_date)
        if to_date:
            query += " AND date(l.request_date) <= ?"
            params.append(to_date)
        query += " ORDER BY l.request_date DESC"

        for item in self.lab_tree.get_children():
            self.lab_tree.delete(item)
        self.cursor.execute(query, params)
        for row in self.cursor.fetchall():
            self.lab_tree.insert("", END, values=row)
        dialog.destroy()

    def show_add_lab_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Lab Request")
        dialog.geometry("400x300")
        dialog.resizable(True, True)

        Label(dialog, text="Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        self.cursor.execute("SELECT id, name FROM patients")
        patients = self.cursor.fetchall()
        patient_var = StringVar()
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, values=[f"{p[0]} - {p[1]}" for p in patients], state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Test Type:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        test_entry = Entry(dialog)
        test_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        notes_entry = Entry(dialog)
        notes_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Save", command=lambda: self.save_lab_request(
            patient_var.get().split(" - ")[0],
            test_entry.get(),
            notes_entry.get(),
            dialog
        )).grid(row=3, column=0, columnspan=2, pady=20)

    def save_lab_request(self, patient_id, test_type, notes, dialog):
        if not patient_id or not test_type:
            messagebox.showerror("Error", "Patient and test type are required")
            return
        request_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            INSERT INTO laboratory (patient_id, test_type, request_date, notes)
            VALUES (?, ?, ?, ?)
        """, (patient_id, test_type, request_date, notes))
        self.conn.commit()
        messagebox.showinfo("Success", "Lab request added.")
        dialog.destroy()
        self.refresh_lab_list()

    def refresh_lab_list(self):
        for item in self.lab_tree.get_children():
            self.lab_tree.delete(item)
        self.cursor.execute("""
            SELECT l.id, p.name, l.test_type, l.request_date, l.result_date, l.result, l.status
            FROM laboratory l
            JOIN patients p ON l.patient_id = p.id
            ORDER BY l.request_date DESC
        """)
        for row in self.cursor.fetchall():
            self.lab_tree.insert("", END, values=row)

    def show_enter_result_dialog(self):
        selected = self.lab_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a lab request")
            return
        lab_data = self.lab_tree.item(selected)['values']
        dialog = Toplevel(self.root)
        dialog.title("Enter Lab Result")
        dialog.geometry("400x300")
        dialog.resizable(True, True)

        Label(dialog, text="Result:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        result_entry = Entry(dialog)
        result_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Status:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        status_var = StringVar(value=lab_data[6])
        status_dropdown = ttk.Combobox(dialog, textvariable=status_var, values=["Pending", "Completed"], state="readonly")
        status_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Save", command=lambda: self.save_lab_result(
            lab_data[0], result_entry.get(), status_var.get(), dialog
        )).grid(row=2, column=0, columnspan=2, pady=20)

    def save_lab_result(self, lab_id, result, status, dialog):
        result_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            UPDATE laboratory SET result=?, result_date=?, status=?
            WHERE id=?
        """, (result, result_date, status, lab_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Lab result updated.")
        dialog.destroy()
        self.refresh_lab_list()

    def print_lab_report(self):
        selected = self.lab_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a lab request")
            return
        lab_data = self.lab_tree.item(selected)['values']
        # Fetch full lab record
        self.cursor.execute("""
            SELECT l.id, p.name, l.test_type, l.request_date, l.result_date, l.result, l.status, l.notes
            FROM laboratory l
            JOIN patients p ON l.patient_id = p.id
            WHERE l.id = ?
        """, (lab_data[0],))
        record = self.cursor.fetchone()
        if not record:
            messagebox.showerror("Error", "Lab record not found")
            return
        report = f"Lab Report\n{'='*40}\n"
        report += f"Patient: {record[1]}\nTest: {record[2]}\nRequested: {record[3]}\n"
        report += f"Result Date: {record[4]}\nStatus: {record[6]}\n\nResult:\n{record[5]}\n\nNotes:\n{record[7]}"
        # Save to file and print
        with open("lab_report.txt", "w") as f:
            f.write(report)
        try:
            os.startfile("lab_report.txt", "print")
            messagebox.showinfo("Print", "Lab report sent to printer.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print: {e}")

    def create_staff_schedule_tab(self):
        self.staff_schedule_tab = Frame(self.notebook)
        self.notebook.add(self.staff_schedule_tab, text="Staff Scheduling")

        # Calendar widget
        cal_frame = Frame(self.staff_schedule_tab)
        cal_frame.pack(fill=X, padx=10, pady=10)
        Label(cal_frame, text="Select Date:").pack(side=LEFT)
        self.schedule_date = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.schedule_cal = DateEntry(cal_frame, textvariable=self.schedule_date, date_pattern="yyyy-mm-dd")
        self.schedule_cal.pack(side=LEFT, padx=5)
        Button(cal_frame, text="View", command=self.refresh_staff_schedule).pack(side=LEFT, padx=5)

        # Treeview for shifts
        self.schedule_tree = ttk.Treeview(self.staff_schedule_tab, columns=("ID", "Name", "Role", "Shift Type", "Leave", "Notes"), show="headings")
        for col in ("ID", "Name", "Role", "Shift Type", "Leave", "Notes"):
            self.schedule_tree.heading(col, text=col)
            self.schedule_tree.column(col, width=100)
        self.schedule_tree.pack(fill=BOTH, expand=True, padx=10, pady=10)

        # Buttons
        button_frame = Frame(self.staff_schedule_tab)
        button_frame.pack(fill=X, padx=10, pady=10)
        Button(button_frame, text="Add Shift/Leave", command=self.show_add_shift_dialog).pack(side=LEFT, padx=5)
        Button(button_frame, text="Edit", command=self.edit_shift).pack(side=LEFT, padx=5)
        Button(button_frame, text="Delete", command=self.delete_shift).pack(side=LEFT, padx=5)
        Button(button_frame, text="Refresh", command=self.refresh_staff_schedule).pack(side=LEFT, padx=5)

        self.refresh_staff_schedule()

    def show_add_shift_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Shift/Leave")
        dialog.geometry("400x350")
        dialog.resizable(True, True)

        Label(dialog, text="Staff:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        # Fetch doctors
        self.cursor.execute("SELECT id, name, 'Doctor' as role FROM doctors")
        doctors = self.cursor.fetchall()
        # Fetch nurses (assuming nurses are in users table with role 'Nurse')
        self.cursor.execute("SELECT id, username as name, role FROM users WHERE role='Nurse'")
        nurses = self.cursor.fetchall()
        staff = doctors + nurses
        staff_list = [f"{s[0]} - {s[1]} ({s[2]})" for s in staff]
        staff_var = StringVar()
        staff_dropdown = ttk.Combobox(dialog, textvariable=staff_var, values=staff_list, state="readonly")
        staff_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        if staff_list:
            staff_dropdown.current(0)

        Label(dialog, text="Date:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        date_var = StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        date_entry = DateEntry(dialog, textvariable=date_var, date_pattern="yyyy-mm-dd")
        date_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)

        Label(dialog, text="Shift Type:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        shift_var = StringVar(value="Day")

        # Leave days
        leave_days_var = IntVar(value=0)
        # Leave Days (only show if "On Leave" is checked)
        def toggle_leave_days(*args):
            if leave_var.get():
                leave_days_label.grid(row=4, column=0, padx=10, pady=10, sticky=W)
                leave_days_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)
            else:
                leave_days_label.grid_remove()
                leave_days_entry.grid_remove()

        leave_days_label = Label(dialog, text="Leave Days:")
        leave_days_entry = Entry(dialog, textvariable=leave_days_var)

        leave_var = IntVar(value=0)
        Checkbutton(dialog, text="On Leave", variable=leave_var, command=toggle_leave_days).grid(row=3, column=1, padx=10, pady=10, sticky=W)

        # Initialize leave days field visibility
        toggle_leave_days()
        shift_dropdown = ttk.Combobox(dialog, textvariable=shift_var, values=["Day", "Night", "Off"], state="readonly")
        shift_dropdown.grid(row=2, column=1, padx=10, pady=10, sticky=EW)

        leave_var = IntVar(value=0)
        Checkbutton(dialog, text="On Leave", variable=leave_var).grid(row=3, column=1, padx=10, pady=10, sticky=W)

        Label(dialog, text="Notes:").grid(row=4, column=0, padx=10, pady=10, sticky=W)
        notes_entry = Entry(dialog)
        notes_entry.grid(row=4, column=1, padx=10, pady=10, sticky=EW)

        Button(dialog, text="Save", command=lambda: self.save_shift(
            staff_var.get(), date_var.get(), shift_var.get(), leave_var.get(), notes_entry.get(), dialog
        )).grid(row=5, column=0, columnspan=2, pady=20)

    def save_shift(self, staff_info, date, shift_type, leave, notes, dialog):
        if not staff_info or not date or not shift_type:
            messagebox.showerror("Error", "All fields except notes are required")
            return
        staff_id, staff_name_role = staff_info.split(" - ", 1)
        staff_name, role = staff_name_role.rsplit(" (", 1)
        role = role.rstrip(")")
        self.cursor.execute("""
            INSERT INTO staff_schedule (staff_id, staff_name, role, shift_date, shift_type, leave, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (staff_id, staff_name.strip(), role, date, shift_type, leave, notes))
        self.conn.commit()
        messagebox.showinfo("Success", "Shift/Leave added.")
        dialog.destroy()
        self.refresh_staff_schedule()

    def refresh_staff_schedule(self):
        for item in self.schedule_tree.get_children():
            self.schedule_tree.delete(item)
        date = self.schedule_date.get()
        self.cursor.execute("""
            SELECT id, staff_name, role, shift_type, leave, notes
            FROM staff_schedule
            WHERE shift_date = ?
        """, (date,))
        for row in self.cursor.fetchall():
            self.schedule_tree.insert("", END, values=row)

    def edit_shift(self):
        selected = self.schedule_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a shift/leave to edit")
            return
        shift_data = self.schedule_tree.item(selected)['values']
        dialog = Toplevel(self.root)
        dialog.title("Edit Shift/Leave")
        dialog.geometry("400x350")
        dialog.resizable(True, True)

        Label(dialog, text="Shift Type:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        shift_var = StringVar(value=shift_data[3])
        shift_dropdown = ttk.Combobox(dialog, textvariable=shift_var, values=["Day", "Night", "Off"], state="readonly")
        shift_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)

        leave_var = IntVar(value=int(shift_data[4]))
        Checkbutton(dialog, text="On Leave", variable=leave_var).grid(row=1, column=1, padx=10, pady=10, sticky=W)

        Label(dialog, text="Notes:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        notes_entry = Entry(dialog)
        notes_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        notes_entry.insert(0, shift_data[5])

        Button(dialog, text="Update", command=lambda: self.update_shift(
            shift_data[0], shift_var.get(), leave_var.get(), notes_entry.get(), dialog
        )).grid(row=3, column=0, columnspan=2, pady=20)

    def update_shift(self, shift_id, shift_type, leave, notes, dialog):
        self.cursor.execute("""
            UPDATE staff_schedule SET shift_type=?, leave=?, notes=?
            WHERE id=?
        """, (shift_type, leave, notes, shift_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Shift/Leave updated.")
        dialog.destroy()
        self.refresh_staff_schedule()

    def delete_shift(self):
        selected = self.schedule_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a shift/leave to delete")
            return
        shift_id = self.schedule_tree.item(selected)['values'][0]
        confirm = messagebox.askyesno("Confirm", "Delete this shift/leave?")
        if confirm:
            self.cursor.execute("DELETE FROM staff_schedule WHERE id=?", (shift_id,))
            self.conn.commit()
            self.refresh_staff_schedule()


    def create_insurance_tab(self):
        self.insurance_tab = Frame(self.notebook)
        self.notebook.add(self.insurance_tab, text="Insurance Claims")

        # Providers Section
        provider_frame = LabelFrame(self.insurance_tab, text="Insurance Providers")
        provider_frame.pack(fill=X, padx=10, pady=5)
        self.provider_tree = ttk.Treeview(provider_frame, columns=("ID", "Name", "Contact", "Email", "Address"), show="headings", height=4)
        for col in ("ID", "Name", "Contact", "Email", "Address"):
            self.provider_tree.heading(col, text=col)
            self.provider_tree.column(col, width=120)
        self.provider_tree.pack(side=LEFT, fill=X, expand=True, padx=5, pady=5)
        Button(provider_frame, text="Add Provider", command=self.show_add_provider_dialog).pack(side=LEFT, padx=5)
        Button(provider_frame, text="Refresh", command=self.refresh_provider_list).pack(side=LEFT, padx=5)

        # Claims Section
        claims_frame = LabelFrame(self.insurance_tab, text="Insurance Claims")
        claims_frame.pack(fill=BOTH, expand=True, padx=10, pady=5)
        self.claims_tree = ttk.Treeview(claims_frame, columns=("ID", "Patient", "Provider", "Date", "Amount", "Status", "Description", "Response"), show="headings")
        for col in ("ID", "Patient", "Provider", "Date", "Amount", "Status", "Description", "Response"):
            self.claims_tree.heading(col, text=col)
            self.claims_tree.column(col, width=100)
        self.claims_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)
        btn_frame = Frame(claims_frame)
        btn_frame.pack(fill=X, padx=5, pady=5)
        Button(btn_frame, text="Add Claim", command=self.show_add_claim_dialog).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Edit Claim", command=self.edit_claim_dialog).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Delete Claim", command=self.delete_claim).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Generate Report", command=self.generate_claim_report).pack(side=LEFT, padx=5)
        Button(btn_frame, text="Refresh", command=self.refresh_claims_list).pack(side=LEFT, padx=5)

        self.refresh_provider_list()
        self.refresh_claims_list()

    def show_add_provider_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Insurance Provider")
        dialog.geometry("400x300")
        Label(dialog, text="Name:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        name_entry = Entry(dialog)
        name_entry.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        Label(dialog, text="Contact:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        contact_entry = Entry(dialog)
        contact_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        Label(dialog, text="Email:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        email_entry = Entry(dialog)
        email_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        Label(dialog, text="Address:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        address_entry = Entry(dialog)
        address_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        Button(dialog, text="Save", command=lambda: self.save_provider(
            name_entry.get(), contact_entry.get(), email_entry.get(), address_entry.get(), dialog
        )).grid(row=4, column=0, columnspan=2, pady=20)

    def save_provider(self, name, contact, email, address, dialog):
        if not name:
            messagebox.showerror("Error", "Name is required")
            return
        self.cursor.execute("""
            INSERT INTO insurance_providers (name, contact, email, address)
            VALUES (?, ?, ?, ?)
        """, (name, contact, email, address))
        self.conn.commit()
        messagebox.showinfo("Success", "Provider added")
        dialog.destroy()
        self.refresh_provider_list()

    def refresh_provider_list(self):
        for item in self.provider_tree.get_children():
            self.provider_tree.delete(item)
        self.cursor.execute("SELECT id, name, contact, email, address FROM insurance_providers")
        for row in self.cursor.fetchall():
            self.provider_tree.insert("", END, values=row)

    def show_add_claim_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Add Insurance Claim")
        dialog.geometry("500x400")
        # Patient
        Label(dialog, text="Patient:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        self.cursor.execute("SELECT id, name FROM patients")
        patients = self.cursor.fetchall()
        patient_var = StringVar()
        patient_dropdown = ttk.Combobox(dialog, textvariable=patient_var, values=[f"{p[0]} - {p[1]}" for p in patients], state="readonly")
        patient_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        # Provider
        Label(dialog, text="Provider:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        self.cursor.execute("SELECT id, name FROM insurance_providers")
        providers = self.cursor.fetchall()
        provider_var = StringVar()
        provider_dropdown = ttk.Combobox(dialog, textvariable=provider_var, values=[f"{p[0]} - {p[1]}" for p in providers], state="readonly")
        provider_dropdown.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        # Amount
        Label(dialog, text="Amount:").grid(row=2, column=0, padx=10, pady=10, sticky=W)
        amount_entry = Entry(dialog)
        amount_entry.grid(row=2, column=1, padx=10, pady=10, sticky=EW)
        # Description
        Label(dialog, text="Description:").grid(row=3, column=0, padx=10, pady=10, sticky=W)
        desc_entry = Entry(dialog)
        desc_entry.grid(row=3, column=1, padx=10, pady=10, sticky=EW)
        Button(dialog, text="Save", command=lambda: self.save_claim(
            patient_var.get().split(" - ")[0],
            provider_var.get().split(" - ")[0],
            amount_entry.get(),
            desc_entry.get(),
            dialog
        )).grid(row=4, column=0, columnspan=2, pady=20)

    def save_claim(self, patient_id, provider_id, amount, description, dialog):
        if not patient_id or not provider_id or not amount:
            messagebox.showerror("Error", "Patient, provider, and amount are required")
            return
        try:
            amount = float(amount)
        except ValueError:
            messagebox.showerror("Error", "Amount must be a number")
            return
        claim_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute("""
            INSERT INTO insurance_claims (patient_id, provider_id, claim_date, amount, description)
            VALUES (?, ?, ?, ?, ?)
        """, (patient_id, provider_id, claim_date, amount, description))
        self.conn.commit()
        messagebox.showinfo("Success", "Claim added")
        dialog.destroy()
        self.refresh_claims_list()

    def refresh_claims_list(self):
        for item in self.claims_tree.get_children():
            self.claims_tree.delete(item)
        self.cursor.execute("""
            SELECT c.id, p.name, ip.name, c.claim_date, c.amount, c.status, c.description, c.response
            FROM insurance_claims c
            JOIN patients p ON c.patient_id = p.id
            JOIN insurance_providers ip ON c.provider_id = ip.id
            ORDER BY c.claim_date DESC
        """)
        for row in self.cursor.fetchall():
            self.claims_tree.insert("", END, values=row)

    def edit_claim_dialog(self):
        selected = self.claims_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a claim to edit")
            return
        claim_data = self.claims_tree.item(selected)['values']
        dialog = Toplevel(self.root)
        dialog.title("Edit Claim")
        dialog.geometry("400x350")
        Label(dialog, text="Status:").grid(row=0, column=0, padx=10, pady=10, sticky=W)
        status_var = StringVar(value=claim_data[5])
        status_dropdown = ttk.Combobox(dialog, textvariable=status_var, values=["Pending", "Approved", "Rejected", "Paid"], state="readonly")
        status_dropdown.grid(row=0, column=1, padx=10, pady=10, sticky=EW)
        Label(dialog, text="Response:").grid(row=1, column=0, padx=10, pady=10, sticky=W)
        response_entry = Entry(dialog)
        response_entry.grid(row=1, column=1, padx=10, pady=10, sticky=EW)
        response_entry.insert(0, claim_data[7] if claim_data[7] else "")
        Button(dialog, text="Update", command=lambda: self.update_claim(
            claim_data[0], status_var.get(), response_entry.get(), dialog
        )).grid(row=2, column=0, columnspan=2, pady=20)

    def update_claim(self, claim_id, status, response, dialog):
        self.cursor.execute("""
            UPDATE insurance_claims SET status=?, response=? WHERE id=?
        """, (status, response, claim_id))
        self.conn.commit()
        messagebox.showinfo("Success", "Claim updated")
        dialog.destroy()
        self.refresh_claims_list()

    def delete_claim(self):
        selected = self.claims_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a claim to delete")
            return
        claim_id = self.claims_tree.item(selected)['values'][0]
        if messagebox.askyesno("Confirm", "Delete this claim?"):
            self.cursor.execute("DELETE FROM insurance_claims WHERE id=?", (claim_id,))
            self.conn.commit()
            self.refresh_claims_list()

    def generate_claim_report(self):
        selected = self.claims_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Select a claim to generate report")
            return
        claim_data = self.claims_tree.item(selected)['values']
        report = f"Insurance Claim Report\n{'='*40}\n"
        report += f"Claim ID: {claim_data[0]}\nPatient: {claim_data[1]}\nProvider: {claim_data[2]}\n"
        report += f"Date: {claim_data[3]}\nAmount: {claim_data[4]}\nStatus: {claim_data[5]}\n"
        report += f"Description: {claim_data[6]}\nResponse: {claim_data[7]}\n"
        # Save and print
        with open("claim_report.txt", "w") as f:
            f.write(report)
        try:
            os.startfile("claim_report.txt", "print")
            messagebox.showinfo("Print", "Claim report sent to printer.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to print: {e}")

if __name__ == "__main__":
    show_welcome_and_start()
    root = Tk()
    app = HospitalManagementSystem(root)
    root.configure(bg="cyan")
    root.mainloop()
