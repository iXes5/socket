import socket

#192.168.1.4
HOST = "192.168.1.8"
SERVER_PORT = 54321
FORMAT = "utf8"

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

print("CLIENT SIDE")

try:
    client.connect((HOST, SERVER_PORT))
    print("client address:", client.getsockname())

    msg = None
    while (msg != "quit"):
        msg = input("client: ")
        client.sendall(msg.encode(FORMAT))

except:
    print("Error")

print("end")
client.close()