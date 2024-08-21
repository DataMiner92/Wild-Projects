import tkinter as tk
from datetime import datetime
import random
import sqlite3
from tkinter.font import Font

root = tk.Tk()

root.title("Student Management")

conn = sqlite3.connect('ssm_data.db')
c = conn.cursor()


c.execute('''CREATE TABLE IF NOT EXISTS students
             (id INTEGER PRIMARY KEY, name TEXT, school TEXT, action TEXT, timestamp TEXT)''')
conn.commit()

def generate_index():
    return random.randint(99, 999)

def report_action(student_name, school_name):
    index = generate_index()
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    action = f"{student_name}, Index No: {index}, \n has reported to {school_name} \n at: {timestamp}"
    c.execute("INSERT INTO students (name, school, action, timestamp) VALUES (?, ?, ?, ?)",
              (student_name, school_name, action, timestamp))
    conn.commit()
    return action

def leave_out_action(student_name, school_name):
    index = generate_index()
    timestamp = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    action = f"{student_name}, Index No: {index}, \n has been released from {school_name} \n on: {timestamp}"
    c.execute("INSERT INTO students (name, school, action, timestamp) VALUES (?, ?, ?, ?)",
              (student_name, school_name, action, timestamp))
    conn.commit()
    return action





def on_exit():
    root.destroy()

def main_window():

    

    def on_submit():
        student_name = name_entry.get()
        school_name = school_entry.get()
        choice = choice_var.get()

        if choice == 1:
            action = report_action(student_name, school_name)
        elif choice == 2:
            action = leave_out_action(student_name, school_name)
        else:
            action = "Wrong choice. Please Enter 1 or 2"

        result_text.config(state=tk.NORMAL)
        result_text.delete('1.0', tk.END)
        result_text.insert(tk.END, action)
        result_text.config(state=tk.DISABLED)

    choice_var = tk.IntVar()
    choice_var.set(1)

    frame = tk.Frame(root)
    frame.pack(padx=20, pady=20)
    
 

    tk.Label(frame, text="Student Name:").grid(row=0, column=0, sticky="w")
    name_entry = tk.Entry(frame)
    name_entry.grid(row=0, column=1,columnspan=1)

    tk.Label(frame, text="School Name:").grid(row=1, column=0, sticky="w")
    school_entry = tk.Entry(frame)
    school_entry.grid(row=1, column=1,columnspan=1)

    tk.Radiobutton(frame, text="Reporting", variable=choice_var, value=1).grid(row=2, column=0, sticky="w")
    tk.Radiobutton(frame, text="Leave Out", variable=choice_var, value=2).grid(row=3, column=0, sticky="w")

    submit_button = tk.Button(frame, text="Submit", command=on_submit)
    submit_button.grid(row=4, column=0, columnspan=2, pady=10)

    exit_button = tk.Button(frame, text="Exit", command=on_exit)
    exit_button.grid(row=5, column=0, columnspan=2, pady=10)

    result_text = tk.Text(frame, height=4, width=50, wrap=tk.WORD)
    result_text.grid(row=6, column=0, columnspan=2)
    result_text.config(state=tk.DISABLED)

    root.mainloop()

if __name__ == "__main__":

    main_window()


conn.close()
