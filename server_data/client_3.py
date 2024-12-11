import os
import socket
import threading
# GUI
import tkinter as tk
from tkinter import Tk
from tkinter import PhotoImage 
from tkinter import Button
from tkinter import Label
from tkinter import Entry
from tkinter import Frame
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import messagebox
# Import ttk for Progressbar
from tkinter import ttk  

# IP loopback (use for test)
HOST ='127.0.0.1'
PORT = 55555
CHUNK_SIZE = 1024*64
UPLOAD_FOLDER = 'server_data'
socket_lock = threading.Lock()
client_socket = None

# Split file into chunks
def split_file(file_path, chunk_size):
    chunks = []
    with open(file_path, 'rb') as file:
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            chunk_filename = f"{file_path}_part_{len(chunks)}"
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            chunks.append(chunk_filename)
    return chunks

# Merge all chunks into one file
def merge_chunks(chunks, output_file):
    with open(output_file, 'wb') as out_file:
        for chunk_file in chunks:
            with open(chunk_file,'rb') as chunk:
                out_file.write(chunk.read())
            os.remove(chunk_file)

# UPLOAD
def upload_file(file_path):
    global client_socket

    if not client_socket:
        print("No connection to server.")
        return

    try:
        chunks = split_file(file_path, CHUNK_SIZE)
        num_chunks = len(chunks)
        print(f"Num of chunks: {num_chunks}")

        # Send request type and file info
        file_info = f"{os.path.basename(file_path)}:{num_chunks}"
        client_socket.sendall(f"upload{file_info}".encode())
        print(f"Send request to server: upload")

        ack = client_socket.recv(1024).decode().strip()
        if ack != 'OK':
            raise Exception("Failed to receive acknowledgment from server")

        threads = []
        for index, chunk_path in enumerate(chunks):
            thread = threading.Thread(target=upload_chunk, args=(index, chunk_path, client_socket, socket_lock))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        ack = client_socket.recv(1024).decode().strip()
        if ack != "OK":
            raise Exception("Failed to receive acknowledgment from server")
        else:
            print(f"File {file_path} uploaded successfully.")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")
    finally:
        for chunk in chunks:
            if os.path.exists(chunk):
                os.remove(chunk)

def upload_chunk(chunk_index, chunk_path, client_socket, socket_lock):
    try:
        with socket_lock:
            client_socket.sendall(f"{chunk_index}:{os.path.getsize(chunk_path)}".encode())
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server")

        with open(chunk_path, 'rb') as chunk_file:
            chunk_data = chunk_file.read()
            client_socket.sendall(chunk_data)

        ack = client_socket.recv(1024).decode().strip()
        if ack != "OK":
            raise Exception("Failed to receive acknowledgment from server")
        else:
            print(f"Sent chunk {chunk_path} size: {os.path.getsize(chunk_path)}")

    except Exception as e:
        print(f"Error sending chunk {chunk_path}: {e}")

# DOWNLOAD
def download_file(file_path, download_folder_path):
    global client_socket
    if not client_socket:
        print("No connection to server.")
        return
    
    try:
        # Send request type and file info
        client_socket.sendall(f"download{file_path}".encode())
        print(f"Send request to server: download")
        print(f"Send file name to server: {file_path}")
        
        # Receive acknowledgment
        ack = client_socket.recv(1024).decode().strip()
        if ack != "OK":
            raise Exception("Failed to receive acknowledgment from server")
        
        # Receive the number of chunks 
        num_chunks = int(client_socket.recv(1024).decode())
        print(f"Num of chunks: {num_chunks}")
        
        # Init list to store chunk paths and threads
        chunk_paths = []
        threads = []
        for index in range(num_chunks):
            thread = threading.Thread(target=download_chunk, args=(file_path, client_socket, chunk_paths, download_folder_path))
            threads.append(thread)
            thread.start()

        # Wait for all threads finish
        for thread in threads:
            thread.join()

        # Merge chunks if all were downloaded successfully
        if None not in chunk_paths:
            output_file = os.path.join(download_folder_path, os.path.basename(file_path))
            merge_chunks(chunk_paths, output_file)

            client_socket.send('OK'.encode())
            print(f"File {file_path} downloaded successfully")
    except socket.error as E:
        print(f"Socket error: {E}")
    except Exception as E:
        print(f"Error: {E}")

def download_chunk(file_path, client_socket, chunk_paths, download_folder_path):
    try: 
        with socket_lock:
            # Recive chunk info
            chunk_info = client_socket.recv(1024).decode().strip()
            chunk_index, chunk_size = map(int, chunk_info.split(':'))
            # ACK for chunk info 
            client_socket.sendall('OK'.encode())

        # Recive chunk data
            chunk_data = b''
            while len(chunk_data) < chunk_size:
                chunk_data += client_socket.recv(min(1024, chunk_size - len(chunk_data)))

            # Save the chunk data to a file 
            chunk_path = os.path.join(download_folder_path, f"{file_path}_part_{chunk_index}")
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)

            # ACK for chunk data
            client_socket.sendall('OK'. encode())
            print(f"Received chunk_{chunk_index} size: {chunk_size} ({chunk_info})")
            chunk_paths.append(chunk_path)

    except Exception as e:
        print(f"Error downloading file {file_path}:{e}")

def connect_to_server():
    global client_socket
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((HOST, PORT))
        print(f"Connected to server at {HOST}:{PORT}")
    except Exception as e:
        print(f"Error connecting to server: {e}")
        client_socket = None

# Receive files name and do the request from client (up or down)
def select_file_to_upload():
    # Open file fialog to select a file for upload
    file_paths = filedialog.askopenfilenames(initialdir = os.getcwd(), title = "choose file")
    for file_path in file_paths:
        if file_path:
            print(f"File selected: {file_path}")
            upload_file(file_path)
        else:
            print("No file selected to up looad.")
    
def select_file_to_download(menu):
    # Open window to enter file name
    file_paths = open_file_input_dialog(menu)

    # Open dialog to choose destination of downLoad folder
    download_folder_path = filedialog.askdirectory()
    if not download_folder_path:
        print("No download folder selected.")
        return 

    for file_path in file_paths:
        if file_path:
            print(f"File selected: {file_path}")
            download_file(file_path, download_folder_path)
        else:
            print("No file selected to download.")

# Register account
def register_account(username, password):
    global client_socket
    connect_to_server()
    try:
        # Send username and password to server
        client_socket.sendall(f"register{username}:{password}".encode())
        print(f"Send request to server: register")
        
        # Waiting for response
        response = client_socket.recv(1024).decode()
        if (response == 'OK'):
            print(f"Register successfully")
            show_secondary_window()
    except Exception as e:
        print(f"Cannot register: {e}")

# Login account
def login_account(username, password):
    global client_socket
    connect_to_server()
    try:
        # Send username and password to server
        client_socket.sendall(f"login{username}:{password}".encode())
        print(f"Send request to server: login")
        
        # Waiting for response
        response = client_socket.recv(1024).decode()
        if (response == 'OK'):
            print(f"Login successfully")
            show_secondary_window()
        else:
            print(f"Wrong username or password")
            client_socket.close()
    except Exception as e:
        print(f"Cannot login: {e}")

# Log out account
def disconnect_to_server():
    global client_socket
    if not client_socket:
        print("No connection to server")
        return
    
    try:
        # Send disconnect request to the server with additional info
        client_id = "goodbye"
        client_socket.sendall(f"disconnect:{client_id}".encode())
        print(f"Send request to server: disconnect")
        
        # Waiting for response
        response = client_socket.recv(1024).decode()
        if (response == 'OK'):
            response = client_socket.recv(1024).decode()
        print(f"Response from server: {response}")

        # Close socket
        client_socket.close()
        print("Disconnected from server")
        client_socket = None
    except Exception as e:
        print(f"Cannot disconnect: {e}")

# Open a window to enter file name
def open_file_input_dialog(menu):
    def add_file_name():
        file_name = entry.get().strip()
        if file_name:
            listbox.insert(tk.END, file_name)
            entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Warning", "file name cannot be blank!")

    def delete_selected_file():
        selected = listbox.curselection()
        if selected:
            listbox.delete(selected[0])
        else:
            messagebox.showwarning("Warning", "Select file name to delete!")

    def save_and_close():
        file_names = listbox.get(0, tk.END)
        file_names_str = ", ".join(file_names)
        print("File name entered:")
        for file_name in file_names:
            print(file_name)
        result_var.set(file_names_str)
        dialog.destroy()

    # Create child window
    dialog = tk.Toplevel(menu)
    dialog.title("Enter file name")
    dialog.geometry("300x300+600+150")
    dialog.resizable(False, False)

    # Enter file name bar
    entry_frame = tk.Frame(dialog)
    entry_frame.pack(pady=10)
    entry = tk.Entry(entry_frame, width=25)
    entry.pack(side=tk.LEFT, padx=5)
    add_button = tk.Button(entry_frame, text="Add", command=add_file_name)
    add_button.pack(side=tk.RIGHT)

    # List of file name
    listbox = tk.Listbox(dialog, width=40, height=10)
    listbox.pack(pady=10)

    # Delete button
    delete_button = tk.Button(dialog, text="Delete", command=delete_selected_file)
    delete_button.pack(pady=5)

    # Save & Close button
    save_button = tk.Button(dialog, text="Save&Close", command=save_and_close)
    save_button.pack(pady=10)

    # Result to save list of file name
    result_var = tk.StringVar()
    dialog.grab_set()
    dialog.wait_window()
    return result_var.get().strip().split(", ")  # Ensure list is correctly formatted

# Show main menu
def show_secondary_window():
    """
    Hiển thị cửa sổ con chứa ba nút: Upload, Download và Disconnect nằm ngang nhau.
    """
    secondary_window = tk.Toplevel(menu)
    secondary_window.title("Main Menu")
    secondary_window.geometry("400x300+600+200")
    secondary_window.configure(bg="linen")
    secondary_window.resizable(False, False)

    # Frame to contain buttons
    button_frame = Frame(secondary_window, bg="linen")
    button_frame.pack(expand=True, pady=20)

    # Upload button
    upload_image = PhotoImage(file="image/upload.png")
    Button(button_frame, image=upload_image, bg="linen", bd=0,
           command=select_file_to_upload).grid(row=0, column=0, padx=10)
    upload_image.image = upload_image

    # Download button
    download_image = PhotoImage(file="image/download.png")
    Button(button_frame, image=download_image, bg="linen", bd=0,
           command=lambda: select_file_to_download(menu)).grid(row=0, column=1, padx=10)
    download_image.image = download_image

    # Disconnect button
    disconnect_image = PhotoImage(file="image/disconnect.png")
    Button(button_frame, image=disconnect_image, bg="linen", bd=0,
           command=lambda: [disconnect_to_server(), secondary_window.destroy()]).grid(row=0, column=2, padx=10)
    disconnect_image.image = disconnect_image


def main():
    # Initialize the Tkinter menu window
    global menu
    menu = Tk()
    menu.title("File Transfer Application")
    screen_width = menu.winfo_screenwidth()
    screen_height = menu.winfo_screenheight()
    place_x = int((screen_width - 400) / 2)
    place_y = int((screen_height - 300) / 2)
    menu.geometry(f"400x300+{place_x}+{place_y}")
    menu.configure(bg="linen")
    menu.resizable(False, False)

    # Giao diện đăng nhập
    Label(menu, text="Username:", bg="linen").grid(row=0, column=0, padx=5, pady=5)
    username_entry = Entry(menu)
    username_entry.grid(row=0, column=1, padx=5, pady=5)

    Label(menu, text="Password:", bg="linen").grid(row=1, column=0, padx=5, pady=5)
    password_entry = Entry(menu, show="*")
    password_entry.grid(row=1, column=1, padx=5, pady=5)

    Button(menu, text="Login",
           command=lambda: login_account(username_entry.get(), password_entry.get()), bg="linen").grid(row=2, column=0, padx=5, pady=10)
    Button(menu, text="Register",
           command=lambda: register_account(username_entry.get(), password_entry.get()), bg="linen").grid(row=2, column=1, padx=5, pady=10)
    menu.mainloop()

if __name__ == "__main__":
    main()