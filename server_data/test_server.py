import socket
import threading
import json
import os

HOST = '127.0.0.1'
PORT = 55555
USER_DATA = 'users.json'

# Load user data
def load_users():
    if not os.path.exists(USER_DATA):
        with open(USER_DATA, 'w') as f:
            json.dump({}, f)
    with open(USER_DATA, 'r') as f:
        return json.load(f)

# Save user data
def save_users(users):
    with open(USER_DATA, 'w') as f:
        json.dump(users, f)

# Handle client
def handle_client(client_socket, addr):
    try:
        print(f"Connection from {addr}")
        # Receive request type
        request_type = client_socket.recv(1024).decode().strip()
        
        if request_type == "REGISTER":
            # Handle registration
            data = client_socket.recv(1024).decode().strip()
            username, password = data.split(':')
            users = load_users()
            
            if username in users:
                client_socket.sendall("REGISTER_FAIL".encode())
            else:
                users[username] = password
                save_users(users)
                client_socket.sendall("REGISTER_OK".encode())
        
        elif request_type == "LOGIN":
            # Handle login
            data = client_socket.recv(1024).decode().strip()
            username, password = data.split(':')
            users = load_users()
            
            if users.get(username) == password:
                client_socket.sendall("LOGIN_OK".encode())
            else:
                client_socket.sendall("LOGIN_FAIL".encode())
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

# Main server loop
def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f"Server listening on {HOST}:{PORT}")
    
    while True:
        client_socket, addr = server_socket.accept()
        threading.Thread(target=handle_client, args=(client_socket, addr)).start()

if __name__ == "__main__":
    main()