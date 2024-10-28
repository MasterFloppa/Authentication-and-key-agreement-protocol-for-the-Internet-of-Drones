import os
import hashlib
import socket
import json
import time

def H(data):
    """Hash function H() used for pseudonym generation."""
    return hashlib.sha256(data.encode()).digest()

def SecureSend(sock, data):
    """Sends data over a socket connection."""
    sock.sendall(json.dumps(data).encode())
    print(f"Sent: {data}")

def ControlCenterOperations():
    # Setup the server to listen for connections from the Drone
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as cc_socket:
        cc_socket.bind(('localhost', 65432))  # Bind to localhost on port 65432
        cc_socket.listen(3)
        print("Control Center is listening for connections from Drone...")
        
        conn, addr = cc_socket.accept()
        with conn:
            print(f"Control Center: Connected by Drone: {addr}")

            # Step 1: Receive identity information from Drone
            data = json.loads(conn.recv(1024).decode())
            print(f"Control Center: Received data from Drone: {data}")

            # Step 2: Send tasks back to the Drone
            tasks = [f"dt{i+1}" for i in range(5)]
            SecureSend(conn, tasks)

        # Accept connection from Ground Station
            print("Control Center: Waiting for Ground Station to connect...")
            gz_conn, gz_addr = cc_socket.accept()
            with gz_conn:
                print(f"Control Center: Connected by Ground Station: {gz_addr}")
                SecureSend(gz_conn, data)  # Sending the last received data from the drone

        #----------------------------------NOT to done by control center----------------------------------
        # Recv verifications from drone
            # for i in tasks:

            #     print()
            #     print(f"Processing task {i}")
            #     print()

            #     print("Control Center: Waiting for verification from Drone...")
            
                
    #----------------------------------NOT to done by control center----------------------------------

# Example usage
if __name__ == "__main__":
    ControlCenterOperations()
