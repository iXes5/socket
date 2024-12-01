import socket
import threading

HOST = "192.168.1.2"
# (>50000)
SERVER_PORT = 54321
FORMAT = "utf8"

# Biến đếm số lượng client đang kết nối
active_clients = 0
lock = threading.Lock()  # Đảm bảo đồng bộ hóa khi thay đổi biến đếm

def handleClient(conn: socket, addr):
    global active_clients
    
    print("connect:", conn.getsockname())
    print("address", addr)
    
    msg = None
    while (msg != "quit"):
        msg = conn.recv(1024).decode(FORMAT)
        print("client:", addr, msg)
    
    print(addr, "finished")
    print(conn.getsockname(), "closed")
    
    # Giảm số lượng client khi client ngắt kết nối
    with lock:
        active_clients -= 1
    conn.close()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # SOCK_STREAM = TCP

s.bind((HOST, SERVER_PORT))
s.listen()

print("SERVER SIDE")
print("server:", HOST, SERVER_PORT)
print("waiting for client")

while active_clients < 5:
    try:
        conn, addr = s.accept()

        # Tăng số lượng client khi có kết nối mới
        with lock:
            active_clients += 1
        
        thr = threading.Thread(target=handleClient, args=(conn, addr))
        thr.daemon = False
        thr.start()

    except Exception as e:
        print(f"Error: {e}")

print("end")
s.close()