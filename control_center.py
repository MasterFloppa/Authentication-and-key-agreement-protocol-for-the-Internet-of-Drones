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

        # Recv verifications from drone
            for i in tasks:

                print()
                print(f"Processing task {i}")
                print()

                print("Control Center: Waiting for verification from Drone...")
            
                M3 = json.loads(conn.recv(1024).decode())
 
                # check if empty
                if not M3:
                    print("No data received")
                    break
                else:
                    print(f"Control Center: Received data from Drone: {M3}")
                    

                stu = bytes.fromhex(M3["stu"])
                s_prime_tp = M3["s_prime_tp"]
                restuk = bytes.fromhex(M3["restuk"])
                DTk = M3["DTk"]
                RIDk = bytes.fromhex(M3["RIDk"])
                GIDz = bytes.fromhex(M3["GIDz"])
                restik = bytes.fromhex(M3["restik"])
                chetuk = bytes.fromhex(M3["chetuk"])
                PIDtk = bytes.fromhex(M3["PIDtk"])
                
                m3a = int(M3["m3a"], 16)
                m3b = int(M3["m3b"], 16)
                m3c = int(M3["m3c"], 16)    
                m3d = int(M3["m3d"], 16)
                tu = M3["tu"]


                stu_prime = m3a ^ int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex() + restik.hex()), byteorder='big')
                che_tu_k_prime = m3b ^ int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex() + restik.hex() + str(stu_prime)), byteorder='big')
                restu_k_prime = m3c ^ int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex() + restik.hex() + str(stu_prime) + str(che_tu_k_prime)), byteorder='big')
                PID_tu_k_prime = H(RIDk.hex() + str(restu_k_prime))
                m3d_prime = int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex()+restik.hex()+str(tu)+chetuk.hex()+restuk.hex()+PIDtk.hex()),byteorder='big')
                if m3d_prime!=m3d:
                    print("Authentication failed")
                else:
                    SK=int.from_bytes(H(stu.hex()), byteorder='big') \
                    ^ int.from_bytes(H(str(s_prime_tp)), byteorder='big') \
                    ^ int.from_bytes(H(restuk.hex()), byteorder='big') \
                    ^ int.from_bytes(H(str(DTk)), byteorder='big')
                    print("Session Key succesfully established {}".format(SK))


# Example usage
if __name__ == "__main__":
    ControlCenterOperations()
