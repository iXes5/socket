import os
import socket
import threading

# IP loopback (use for test)
HOST ='127.0.0.1'
PORT = 55555
CHUNK_SIZE = 1024*64
DATA_FOLDER = 'server_data'
socket_lock = threading.Lock()

# If not server_data, create server_data
if not os.path.exists(DATA_FOLDER):
    os.makedirs(DATA_FOLDER)

# Split file into chunks
def split_file(file_path, chunk_size):
    chunks = []
    base_name = os.path.basename(file_path)
    dir_name = os.path.dirname(file_path)
    
    with open(file_path, 'rb') as file:
        index = 0
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            chunk_filename = os.path.join(dir_name, f"{base_name}_part_{index}")
            with open(chunk_filename, 'wb') as chunk_file:
                chunk_file.write(chunk)
            
            chunks.append(chunk_filename)
            index += 1
    return chunks

# Merge all chunks into one file
def merge_chunks(chunks, output_file):
    with open(output_file, 'wb') as out_file:
        for chunk_file in chunks:
            with open(chunk_file, 'rb') as chunk:
                out_file.write(chunk.read())
            os.remove(chunk_file)

# Accept connect from client and do the request
def handle_client(conn, addr):
    print(f"Connected from {addr}")
    try:
        while True:
            # Receive the request form client
            request_type, file_info = receive_request_type_and_file_info(conn)
            if not request_type or not file_info:
                raise ValueError("Invalid request file or file info")
            print(f"Request file: {request_type}")
            if file_info:
                print(f"File info: {file_info}")

            # Upload request
            if request_type == 'upload':
                file_name, num_chunks = file_info.strip().split(':')
                num_chunks = int(num_chunks.strip())
                print(f"File upload's name: {file_name}, num of chunks: {num_chunks}")
                handle_upload(conn, file_name, num_chunks)

            # Download request
            elif request_type == 'download':
                file_name = file_info.strip()
                print(f"File download's name: {file_name}")
                handle_download(conn, file_name)

            # Disconnect request
            elif request_type == 'disconnect':
                conn.sendall("BYE".encode())
                break

            else:
                print(f"Unknown request type: {request_type}")
    except socket.error as E:
        print(f"Socket error: {E}")
    except OSError as E:
        print(f"Cannot writing to file: {E}")
    except ValueError as E:
        print(f"Cannot parsing file info: {E}")
    except Exception as E:
        print(f"Error: {E}")
    finally:
        print(f"Client {addr} requested disconnection.")
        conn.close()

# Handle upload request
def handle_upload(conn, file_name, num_chunks):
    try:
        chunk_paths = [None] * num_chunks

        threads = []
        for _ in range(num_chunks):
            thread = threading.Thread(target=receive_chunk, args=(conn, socket_lock, chunk_paths, file_name, num_chunks))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        if None not in chunk_paths:
            output_file = ensure_unique_filename(os.path.join(DATA_FOLDER, file_name))
            merge_chunks(chunk_paths, output_file)

            conn.sendall("OK".encode())
            print(f"File {file_name} uploaded successfully")

    except Exception as E:
        print(f"Error handling upload: {E}")

def receive_chunk(conn, socket_lock, chunk_paths, file_name, num_chunks):
    try:
        with socket_lock:
            # Receive chunk info
            chunk_info = conn.recv(1024).decode().strip()
            chunk_index, chunk_size = map(int, chunk_info.split(':'))

            # ACK for sendall
            conn.sendall("OK".encode())

            # Receive chunk data
            chunk_data = b''
            while len(chunk_data) < chunk_size:
                chunk_data += conn.recv(min(1024, chunk_size - len(chunk_data)))

            # Save the chunk data to a file
            chunk_path = os.path.join(DATA_FOLDER, f"{file_name}_chunk_{chunk_index}")
            with open(chunk_path, 'wb') as chunk_file:
                chunk_file.write(chunk_data)
            
            # ACK for a chunk
            conn.sendall("OK".encode())
            print(f"Received chunk_{chunk_index} size: {chunk_size} ({chunk_info})")

            # Save chunk path
            chunk_paths[chunk_index] = chunk_path
    except Exception as E:
        print(f"Error receiving chunk: {E}")

# Handle download request
def handle_download(conn, file_name):
    try:
        # Get file path
        file_path = os.path.join(DATA_FOLDER, file_name)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_name} not found")
        
        # Split file into chunk
        chunks = split_file(file_path, CHUNK_SIZE)
        num_chunks = len(chunks)
        conn.sendall(f"{num_chunks}".encode())

        # Send chunks to the client
        threads = []
        for index, chunk_path in enumerate(chunks):
            thread = threading.Thread(target=send_chunk, args=(conn, index, chunk_path, num_chunks))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # ACK for send all chunks
        ack = conn.recv(10).decode().strip()
        if ack != 'OK':
            raise Exception("Failed to receive aknowledgment from client")
        else:
            print(f"File {file_name} downloaded successfully")

    except Exception as E:
        print(f"Error handling download: {E}")
    

def send_chunk(conn, chunk_index, chunk_path, num_chunks):
    try:
        with socket_lock:
            # Get chunk size
            chunk_size = os.path.getsize(chunk_path)
            conn.sendall(f"{chunk_index}:{chunk_size}\n".encode())
            # ACK for chunk size
            ack = conn.recv(10).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive aknowledgment from client")
            
            # Send chunk data
            with open(chunk_path, 'rb') as chunk_file:
                chunk_data = chunk_file.read()
                conn.sendall(chunk_data)
            # ACK for chunk data
            ack = conn.recv(10).decode().strip()
            if ack != 'OK':
                raise Exception("Failed to receive aknowledgment from client")
            else:
                print(f"send chunk_{chunk_index} size: {chunk_size}") 
    except Exception as E:
        print(f"Error sending chunk: {E}")

def receive_request_type_and_file_info(conn):
    try:
        data = conn.recv(1024).decode().strip()
        conn.sendall("OK".encode())

        if data.startswith('upload'):
            return 'upload', data[len('upload'):]
        elif data.startswith('download'):
            return 'download', data[len('download'):]
        elif data.startswith('disconnect'):
            info = data[len('disconnect:'):] if ':' in data else None
            return 'disconnect', info
        else:
            print(f"Unknown request received: {data}")
            return None, None
    except Exception as e:
        print(f"Error receiving data: {e}")
        return None, None

# Make sure file name not duplicate
def ensure_unique_filename(file_path):
    base, ext = os.path.splitext(file_path)
    counter = 1
    unique_file_path = file_path

    # If duplicate, add a number to the end of file name
    while os.path.exists(unique_file_path):
        unique_file_path = f"{base}_{counter}{ext}"
        counter += 1

    return unique_file_path

def start_server():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(50)
        print(f"Server started: {HOST} {PORT}")

        # Accept the request from multiple client
        while True:
            conn, addr = server_socket.accept()
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.start()

def main():
    try:
        start_server()
    except KeyboardInterrupt:
        print(f"Server stopped")
    except Exception as E:
        print(f"Error: {E}")
if __name__ == "__main__":
    main()