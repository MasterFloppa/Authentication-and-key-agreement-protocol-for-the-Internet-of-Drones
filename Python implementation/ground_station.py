import hashlib
import socket
import json
import time
import random
import os

def H(data):
    """Hash function H() used for pseudonym generation."""
    return hashlib.sha256(data.encode()).digest()

def SecureSend(sock, data):
    """Sends data over a socket connection."""
    sock.sendall(json.dumps(data).encode())
    print(f"Sent: {data}")

def RandNum(t):
    """Generate a 16-byte random number."""
    return random.randbytes(16)

def Fpuf(chetuk):
    """Simulate a PUF response."""
    return chetuk  # Placeholder for the actual PUF implementation

def GroundStationOperations():
    # Control Center connection
    # Setup the client to connect to the Control Center
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gz_socket:
        gz_socket.connect(('localhost', 65432))  # Control Center address
        print("Ground Station: Connected to Control Center")

        # Receive drone data from Control Center
        drone_data = json.loads(gz_socket.recv(1024).decode())
        print(f"Ground Station: Received drone information: {drone_data}")


    # Open a new port for Drone connection
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gz_listener:
        gz_listener.bind(('localhost', 65435))
        gz_listener.listen()
        print("Ground Station: Listening for Drone connections...")

        gz_drone_conn, drone_addr = gz_listener.accept()
        with gz_drone_conn:
            print(f"Ground Station: Connected by Drone: {drone_addr}")


            # repeat for all tasks
            for i in range(5):   #CHANGE to actual number of tasks
            # Receive data from the drone

                print()
                print(f"Processing task dt{i+1}")
                print()


                M1 = json.loads(gz_drone_conn.recv(1024).decode())
                print(f"Received M1: {M1}")

                GIDz = bytes.fromhex(M1["GIDz"])
                PIDik = bytes.fromhex(M1["PIDik"])
                RIDk = bytes.fromhex(M1["RIDk"])
                tj = int(M1["tj"])
                m1a = int(M1["m1a"], 16)
                m1b = int(M1["m1b"], 16)
                m1c = int(M1["m1c"], 16)
                task = M1["task"]
                restik = bytes.fromhex(M1['restik'])
                rtj = bytes.fromhex(M1["rtj"])

                tcur = int(time.time())
                if tcur - tj >= 5:  # Assume a threshold Δ = 5 seconds
                    print("Message M1 rejected: Timestamp difference exceeds threshold.")
                    return
                
            
                # Step 12: Ground station calculates r'tj, dtx', and m1c'
                r_tj = m1a ^ int.from_bytes(H(GIDz.hex() + str(tj) + RIDk.hex() + restik.hex()), byteorder='big')
                dtx_prime = m1b ^ int.from_bytes(H(GIDz.hex() + str(tj) + RIDk.hex() + restik.hex() + str(rtj)), byteorder='big')
                m1c_prime = int.from_bytes(H(GIDz.hex() + str(tj) + RIDk.hex() + restik.hex() + str(rtj) + task), byteorder='big')
                # Step 13: Verify m1c
                if m1c_prime != m1c:
                    print("Message M1 rejected: Integrity check failed.")
                    return
                    
                tj= int(time.time())
                # Step 14: If verification passes, generate random number stp and calculate m2a and m2b
                stp = RandNum(int(time.time()))  # Random number for session key generation
                m2a = int.from_bytes(rtj, byteorder='big') ^ int.from_bytes(H(RIDk.hex() + restik.hex() + str(rtj) + str(stp) + GIDz.hex()), byteorder='big')
                m2b = int.from_bytes(H(RIDk.hex() + restik.hex() + str(rtj) + str(tj)+ GIDz.hex()+str(stp)), byteorder='big')
                
            
                # Step 15: Ground station sends m2a and m2b back to the drone
                M2 = {
                    "stp": stp.hex(),
                    "m2a": hex(m2a),
                    "m2b": hex(m2b),
                    "tj": tj
                }
                SecureSend(gz_drone_conn, M2)

                # Step 16: Receive verification from the drone
                M3 = json.loads(gz_drone_conn.recv(1024).decode())
                # check if empty
                if not M3:
                    print("No data received")
                    break
                else:
                    print(f"Gz: Received data from Drone: {M3}")
                    

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
    GroundStationOperations()
