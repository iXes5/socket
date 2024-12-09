import socket

HOST = '127.0.0.1'
PORT = 55555

def login(username, password):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            client_socket.connect((HOST, PORT))
            # Send login info
            client_socket.sendall(f"{username}:{password}".encode())
            # Receive response
            response = client_socket.recv(1024).decode().strip()
            if response == "AUTH_OK":
                print("Login successful!")
                return True
            else:
                print("Login failed.")
                return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def main():
    username = input("Enter username: ")
    password = input("Enter password: ")
    if login(username, password):
        print("Proceed to file upload/download.")
    else:
        print("Authentication failed. Exiting.")

if __name__ == "__main__":
    main()
