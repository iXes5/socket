import socket
import tkinter as tk
from tkinter import messagebox

HOST = '127.0.0.1'
PORT = 55555

# Connect to server
def send_to_server(request_type, data):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            client_socket.sendall(request_type.encode())
            client_socket.sendall(data.encode())
            response = client_socket.recv(1024).decode()
            return response
    except Exception as e:
        messagebox.showerror("Error", f"Could not connect to server: {e}")
        return None

# Register logic
def register_account():
    username = entry_username.get()
    password = entry_password.get()
    if not username or not password:
        messagebox.showwarning("Warning", "Please enter both username and password!")
        return
    response = send_to_server("REGISTER", f"{username}:{password}")
    if response == "REGISTER_OK":
        messagebox.showinfo("Success", "Account registered successfully!")
        switch_to_login()
    else:
        messagebox.showerror("Error", "Username already exists.")

# Login logic
def login_account():
    username = entry_username.get()
    password = entry_password.get()
    if not username or not password:
        messagebox.showwarning("Warning", "Please enter both username and password!")
        return
    response = send_to_server("LOGIN", f"{username}:{password}")
    if response == "LOGIN_OK":
        messagebox.showinfo("Success", "Login successful!")
        open_upload_download()
    else:
        messagebox.showerror("Error", "Invalid username or password.")

# Open upload/download dialog
def open_upload_download():
    messagebox.showinfo("Upload/Download", "Proceed to your upload/download logic.")
    root.destroy()

# Switch between register and login
def switch_to_register():
    frame_login.pack_forget()
    frame_register.pack()

def switch_to_login():
    frame_register.pack_forget()
    frame_login.pack()

# GUI setup
root = tk.Tk()
root.title("Account System")

# Login frame
frame_login = tk.Frame(root)
tk.Label(frame_login, text="Login", font=("Arial", 16)).pack(pady=10)
tk.Label(frame_login, text="Username").pack()
entry_username = tk.Entry(frame_login)
entry_username.pack()
tk.Label(frame_login, text="Password").pack()
entry_password = tk.Entry(frame_login, show="*")
entry_password.pack()
tk.Button(frame_login, text="Login", command=login_account).pack(pady=10)
tk.Button(frame_login, text="Switch to Register", command=switch_to_register).pack()
frame_login.pack()

# Register frame
frame_register = tk.Frame(root)
tk.Label(frame_register, text="Register", font=("Arial", 16)).pack(pady=10)
tk.Label(frame_register, text="Username").pack()
entry_username = tk.Entry(frame_register)
entry_username.pack()
tk.Label(frame_register, text="Password").pack()
entry_password = tk.Entry(frame_register, show="*")
entry_password.pack()
tk.Button(frame_register, text="Register", command=register_account).pack(pady=10)
tk.Button(frame_register, text="Switch to Login", command=switch_to_login).pack()

root.mainloop()
