import socket
import threading
import os

HOST = '127.0.0.1'
PORT = 55555
UPLOAD_FOLDER = 'server_data'
CHUNK_SIZE = 1024 * 64

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def handle_client(client_socket, client_address):
    print(f"[INFO] Client connected from {client_address}")
    try:
        while True:
            command = client_socket.recv(1024).decode().strip()
            if command == 'upload':
                print(f"[INFO] Client {client_address[1]} requested upload")
                handle_upload(client_socket, client_address)
            elif command == 'download':
                print(f"[INFO] Client {client_address[1]} requested download")
                handle_download(client_socket, client_address)
            elif command == 'disconnect':
                print(f"[INFO] Client {client_address[1]} disconnected")
                break
            else:
                print(f"[WARNING] Unknown command from client {client_address[1]}: {command}")
    except Exception as e:
        print(f"[ERROR] Error handling client {client_address[1]}: {e}")
    finally:
        client_socket.close()

def handle_upload(client_socket, client_address):
    filename = client_socket.recv(1024).decode()
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    with open(filepath, 'wb') as f:
        print(f"[INFO] Receiving file '{filename}' from client {client_address[1]}")
        while True:
            data = client_socket.recv(CHUNK_SIZE)
            if not data:
                break
            f.write(data)
    print(f"[INFO] File '{filename}' received successfully from client {client_address[1]}")

def handle_download(client_socket, client_address):
    filename = client_socket.recv(1024).decode()
    filepath = os.path.join(UPLOAD_FOLDER, filename)

    if not os.path.exists(filepath):
        client_socket.sendall(b"ERROR: File not found.")
        print(f"[WARNING] Client {client_address[1]} requested nonexistent file: {filename}")
        return

    client_socket.sendall(b"READY")
    with open(filepath, 'rb') as f:
        print(f"[INFO] Sending file '{filename}' to client {client_address[1]}")
        while chunk := f.read(CHUNK_SIZE):
            client_socket.sendall(chunk)
    print(f"[INFO] File '{filename}' sent successfully to client {client_address[1]}")

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        print(f"[INFO] Server listening on {HOST}:{PORT}")

        while True:
            client_socket, client_address = server_socket.accept()
            client_thread = threading.Thread(
                target=handle_client,
                args=(client_socket, client_address)
            )
            client_thread.daemon = True
            client_thread.start()
            print(f"[INFO] Started thread for client {client_address}")

if __name__ == '__main__':
    start_server()
