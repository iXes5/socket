import os
import socket
import threading
import tkinter as tk
import pandas as pd
from tkinter import *
from tkinter import filedialog, simpledialog, ttk

# CONSTANTS
HOST ='localhost'
PORT = 9999
CHUNK_SIZE = 1024*1024
UPLOAD_FOLDER = 'Server_data'
socket_lock = threading.Lock()

#UPLOAD
def upload_file(file_path):
    try:
        #split the file into chunks
        chunks = split_file(file_path, CHUNK_SIZE)
        num_chunks = len(chunks)
        print(f"Num of chunks: {num_chunks}")

        #Create a socket for the client
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            #COnnect to the server
            client_socket.connect((HOST,PORT))
            #send the request type
            client_socket.sendall('upload'.encode())

            #Send the file info
            file_info =f"{os.path.basename(file_path)}:{num_chunks}"
            client_socket.sendall(file_info.encode())
            #ACK for receving file info
            ack = client_socket.recv(1024).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive acknowledgment from server")
            
            #Create threads to upload each chunk
            threads = []
            #Start threads
            for index, chunk_path in enumerate(chunks):
                thread = threading.Thread(target=upload_chunk, args=(index, chunk_path, client_socket, socket_lock))
                threads.append(thread)
                thread.start()

            #Wait for all threads finish
            for thread in threads:
                thread.join()

            #Final ACK
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server")
            else:
                print(f"File {file_path} uploaded successfully.")
    except Exception as e:
        print(f"Error uploading file {file_path}: {e}")
    finally:
        #Clean up chunk file
        for chunk in chunks:
            if(os.path.exists(chunk)):
                os.remove(chunk)

def upload_chunk(chunk_index, chunk_path, client_socket, socket_lock):
    try:
        #synchronize access to the socket
        with socket_lock:
            #send chunk index and size
            client_socket.sendall(f"{chunk_index}:{os.path.getsize(chunk_path)}")
            # ACK for chunk index and size 
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server")
        
        #Open and send the chunk data the server
            with open(chunk_path, 'rb') as chunk_file:
                chunk_data = chunk_file.read()
                client_socket.sendall(chunk_data)

        #ACK for finishing a chunk file
            ack = client_socket.recv(1024).decode().strip()
            if ack !="OK":
                raise Exception("Failed to receive acknowledgment from server")
            else:
                print(f"sent chunk_{chunk_path} size: {os.path.getsize(chunk_path)}")
    except Exception as e:
        print(f"Error sending chunk {chunk_path}: {e}")

#DOWLOAD
def download_file(file_path):
    try:
        #create socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            #connect to server
            client_socket.connect((HOST,PORT))
            print(f"Host: {HOST}, Port: {PORT}")

            #send the request type
            client_socket.sendall("download".encode())
            print(f"Send request to server: {"download".encode()}")

            #Send the file name
            client_socket.sendall(file_path.encode())
            print(f"Send filename to server: {file_path.encode()}")
            #ACK for recrving file name
            ack = client_socket.recv(1024).decode().strip()
            if ack != "OK":
                raise Exception("Failed to receive acknowledgment from server")
            
            #Receive the number of chunks 
            num_chunks = int(client_socket.recv(1024).decode())
            print(f"Num of chunks: {num_chunks}")
            
            #Open dialog to choose destination of downLoad folder
            download_folder_path = filedialog.askdirectory()
            if not download_folder_path:
                print("No download folder selected.")
                return 
            
            #Init list to store chunk paths and threads
            chunk_paths = []
            threads = []
            for index in range(num_chunks):
                thread = threading.Thread(target=download_chunk, args=(file_path, client_socket, chunk_paths, download_folder_path))
                threads.append(thread)
                thread.start()

            for thread in threads:
                thread.join()

            #Merge chunks if all were downloaded successfully
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
            #Recive truck infoo
            chunk_info = client_socket.recv(1024).decode().strip()
            chunk_index, chunk_size = map(int, chunk_info.split(':'))
            #ACK for chunk info 
            client_socket.sendall('OK'.encode())

        #Recive chunk data
        chunk_data = b''
        while len(chunk_data) < chunk_size:
            chunk_data += client_socket.recv(min(1024, chunk_size - len(chunk_data)))

            #save the chunk data to a file 
            chunk_path = os.path.join(download_folder_path, f"{file_path}_chunk_data")
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)

            #ACK for chunk data
            client_socket.sendall('OK'. encode())
            print(f"Received chunk_{chunk_index} size: {chunk_size} ({chunk_info})")
            chunk_paths.append(chunk_path)
    except Exception as e:
        print(f"Error downloading file {file_path}:{e}")

# ACEESS TO BROWSER
def select_file_to_upload():
    #open file fialog to select a file for upload
    file_paths = filedialog.askopenfilenames(initialdir = os.getcwd(), title = "choose file")
    for file_path in file_paths:
        if file_path:
            upload_file(file_path)
            print(f"File selected: {file_path}")
        else:
            print("No file selected to up looad.")
    
def select_file_to_download():
    # Open file dialog to select a file from 'server_data' folder 
    file_paths = filedialog.askopenfilenames(initialdir = UPLOAD_FOLDER, title = "choose file")

    for file_path in file_paths:
        if file_path:
            download_file(file_path)
            print(f"File selected: {file_path}")
        else:
            print("No file selected to download.")

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

def merge_chunks(chunks, output_file):
    with open(output_file, 'wb') as out_file:
        for chunk_file in chunks:
            with open(chunk_file,'rb') as chunk:
                out_file.write(chunk.read())
            os.remove(chunk_file)


def main():
    #Initialize the Tkinter root window
    global root 

    root = Tk()
    root.title("File Transfer Application")
    root.geometry("300x250+300+300")
    root.configure(bg = "linen")
    root.resizable(False, False)

#App icon
image_icon = PhotoImage(file = "")
root.iconphoto(False, image_icon)

#upload button
upload_image = PhotoImage(file = "")
upload = Button(root, image = upload_image, bg = "linen", bd = 0, command = select_file_to_upload)
upload.place(x = 50, y = 50)
Label(root, text = "upload", font = ('arial', 16, 'bold'), bg = 'linen').place(x = 50, y = 50)

# download button
download_image = PhotoImage(file = "")
download = Button(root, image = download_image, bg = "linen", bd = 0, command = select_file_to_download)
download.place(x = 185, y = 50)
Label(root, text = "download", font = ('arial', 16, 'bold'), bg = 'linen').place(x = 185, y = 50)

root.mainloop()

if __name__ == "__main__":
    main()