import os
import socket
import threading
# GUI
import tkinter as tk
from tkinter import Tk
from tkinter import filedialog
from tkinter import simpledialog
from tkinter import PhotoImage 
from tkinter import Button
from tkinter import messagebox

# IP loopback (use for test)
HOST ='127.0.0.1'
PORT = 55555
CHUNK_SIZE = 1024*64
UPLOAD_FOLDER = 'server_data'
socket_lock = threading.Lock()

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
    try:
        # Split the file into chunks
        chunks = split_file(file_path, CHUNK_SIZE)
        num_chunks = len(chunks)
        print(f"Num of chunks: {num_chunks}")

        # Create a socket for the client
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # Connect to the server
            client_socket.connect((HOST,PORT))
            # Send the request type
            client_socket.sendall('upload'.encode())
            print(f"Send request to server: upload")

            # Send the file info
            file_info =f"{os.path.basename(file_path)}:{num_chunks}"
            client_socket.sendall(file_info.encode())
            # ACK for receving file info
            ack = client_socket.recv(1024).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive acknowledgment from server")
            
            # Create threads to upload each chunk
            threads = []
            # Start threads
            for index, chunk_path in enumerate(chunks):
                thread = threading.Thread(target=upload_chunk, args=(index, chunk_path, client_socket, socket_lock))
                threads.append(thread)
                thread.start()

            # Wait for all threads finish
            for thread in threads:
                thread.join()

            # Final ACK
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server")
            else:
                print(f"File {file_path} uploaded successfully.")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")
    finally:
        # Clean up chunk file
        for chunk in chunks:
            if(os.path.exists(chunk)):
                os.remove(chunk)

def upload_chunk(chunk_index, chunk_path, client_socket, socket_lock):
    try:
        # Synchronize access to the socket
        with socket_lock:
            # Send chunk index and size
            client_socket.sendall(f"{chunk_index}:{os.path.getsize(chunk_path)}".encode())
            # ACK for chunk index and size 
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server")
        
        # Open and send the chunk data the server
            with open(chunk_path, 'rb') as chunk_file:
                chunk_data = chunk_file.read()
                client_socket.sendall(chunk_data)

        # ACK for finishing a chunk file
            ack = client_socket.recv(1024).decode().strip()
            if ack !="OK":
                raise Exception("Failed to receive acknowledgment from server")
            else:
                print(f"sent chunk_{chunk_path} size: {os.path.getsize(chunk_path)}")
    except Exception as e:
        print(f"Error sending chunk {chunk_path}: {e}")

# DOWNLOAD
def download_file(file_path):
    try:
        # Create socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            # Connect to server
            client_socket.connect((HOST,PORT))
            print(f"Host: {HOST}, Port: {PORT}")

            # Send the request type
            client_socket.sendall("download".encode())
            print(f"Send request to server: download")

            # Send the file name
            client_socket.sendall(file_path.encode())
            print(f"Send file name to server: {file_path}")
            # ACK for receiving file name
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server")
            
            # Receive the number of chunks 
            num_chunks = int(client_socket.recv(1024).decode())
            print(f"Num of chunks: {num_chunks}")
            
            # Open dialog to choose destination of downLoad folder
            download_folder_path = filedialog.askdirectory()
            if not download_folder_path:
                print("No download folder selected.")
                return 
            
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
            chunk_path = os.path.join(download_folder_path, f"{file_path}_chunk_data")
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)

            # ACK for chunk data
            client_socket.sendall('OK'. encode())
            print(f"Received chunk_{chunk_index} size: {chunk_size} ({chunk_info})")
            chunk_paths.append(chunk_path)
    except Exception as e:
        print(f"Error downloading file {file_path}:{e}")

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
    dialog.grab_set()  # Khóa các hành động khác khi hộp thoại đang mở
    dialog.wait_window()  # Chờ hộp thoại đóng lại
    return result_var.get().strip().split(", ")  # Ensure list is correctly formatted

# Receive files name and do the request from client (up or down)
def select_file_to_upload():
    # Open file fialog to select a file for upload
    file_paths = filedialog.askopenfilenames(initialdir = os.getcwd(), title = "choose file")
    for file_path in file_paths:
        if file_path:
            upload_file(file_path)
            print(f"File selected: {file_path}")
        else:
            print("No file selected to up looad.")
    
def select_file_to_download(menu):
    # Open window to enter file name
    file_paths = open_file_input_dialog(menu)

    for file_path in file_paths:
        if file_path:
            download_file(file_path)
            print(f"File selected: {file_path}")
        else:
            print("No file selected to download.")

def main():
    # Initialize the Tkinter menu window
    global menu 

    menu = Tk()
    menu.title("File Transfer Application")
    menu.geometry("410x300+500+150")
    menu.configure(bg = "linen")
    menu.resizable(False, False)

    # App icon
    image_icon = PhotoImage(file = "image/transfer.png")
    menu.iconphoto(False, image_icon)

    # Upload button
    upload_image = PhotoImage(file = "image/upload.png")
    upload = Button(menu, image = upload_image, bg = "linen", bd = 0, command = select_file_to_upload)
    upload.place(x = 50, y = 50)

    # Download button
    download_image = PhotoImage(file = "image/download.png")
    download = Button(menu, image=download_image, bg="linen", bd=0, command=lambda: select_file_to_download(menu))
    download.place(x = 228, y = 50)

    menu.mainloop()

if __name__ == "__main__":
    main()