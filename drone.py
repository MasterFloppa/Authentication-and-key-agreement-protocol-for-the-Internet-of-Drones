import os
import hashlib
import time
import socket
import json

def RandID(tcur):
    """Generates a random ID based on the current time."""
    return hashlib.sha256(str(tcur).encode()).digest()

def RandNum(RIDk):
    """Generates a random number for the PUF challenge."""
    return os.urandom(16)  # 128-bit random challenge

def Fpuf(chek):
    """Simulates the PUF response generation."""
    return hashlib.sha256(chek).digest()

def H(data):
    """Hash function H() used for pseudonym generation."""
    return hashlib.sha256(data.encode()).digest()

def SecureSend(sock, data):
    """Sends data over a socket connection."""
    sock.sendall(json.dumps(data).encode())
    print(f"Sent: {data}")

def DroneRegistration_Authenticationplus():
    # Connect to Control Center
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as drone_socket:
        drone_socket.connect(('localhost', 65432))  
        print("Drone: Connected to Control Center")

        # Generate pseudonyms and keys
        tcur = int(time.time())
        RIDk = RandID(tcur)
        chetik = RandNum(RIDk)
        restik = Fpuf(chetik)
        PIDik = H(RIDk.hex() + restik.hex())

        # Send identity data to Control Center
        identity_data = {
            "RIDk": RIDk.hex(),
            "PIDik": PIDik.hex(),
            "chetik": chetik.hex(),
            "restik": restik.hex()
        }
        SecureSend(drone_socket, identity_data)

        # Receive tasks from Control Center
        tasks = json.loads(drone_socket.recv(1024).decode())
        print(f"Drone: Received tasks from Control Center: {tasks}")

        # Connect to Ground Station
        time.sleep(3)  # Ensure server is ready
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as gz_socket:
            gz_socket.connect(('localhost', 65435))  
            print("Drone: Connected to Ground Station")

            GIDz = RandID("GroundStation")
            for task in tasks:       

                print()
                print(f"Task: {task}")
                print()

                restik = Fpuf(chetik) 
                PIDik = H(RIDk.hex() + restik.hex())
                tj= int(time.time())
                rtj=RandNum(tj)
                m1a=int.from_bytes(rtj, byteorder='big')^int.from_bytes(H(GIDz.hex() + str(tj) + RIDk.hex() + restik.hex()), byteorder='big')
                m1b = int.from_bytes(H(GIDz.hex() + str(tj) + RIDk.hex() + restik.hex() + str(rtj)), byteorder='big') ^ int.from_bytes(H(task), byteorder='big')
                m1c = int.from_bytes(H(GIDz.hex() + str(tj) + RIDk.hex() + restik.hex() + str(rtj) + task), byteorder='big')
                M1 = {
                    "GIDz": GIDz.hex(),
                    "tj": tj,
                    "PIDik": PIDik.hex(),
                    "m1a": hex(m1a),
                    "m1b": hex(m1b),
                    "m1c": hex(m1c),
                    "task": task,
                    "RIDk": RIDk.hex(),
                    "restik": restik.hex(),
                    "rtj": rtj.hex()
                }

                # Send registration data to Ground Station
                SecureSend(gz_socket, M1)

            
                # receive M2 from ground station
                response = json.loads(gz_socket.recv(1024).decode())
                print(f"Drone: Received response from Ground Station: {response}")

                tj = response["tj"]
                m2a = int(response["m2a"], 16)
                m2b = int(response["m2b"], 16)
                stp = bytes.fromhex(response["stp"])

                tcur = int(time.time())
                if tcur - tj >= 5:  # Assume a threshold Δ = 5 seconds
                    print("Message M2 rejected: Timestamp difference exceeds threshold.")
                    continue

                s_prime_tp = m2a ^ int.from_bytes(H(RIDk.hex()+ restik.hex()+ str(rtj)+str(tcur)+GIDz.hex()))
                m_prime_2b = int.from_bytes(H(RIDk.hex() + restik.hex() + str(rtj) + str(tj)+ GIDz.hex()+str(stp)), byteorder='big')  

                # print()
                # print(str(stp))
                # print(m2b)
                # print(m_prime_2b)
                # print()

                if m_prime_2b != m2b:
                    print("Authentication failed.")
                    return
                

                #Dont close the socket YET!
                
                tu=int(time.time())
                stu=RandNum(tu)
                chetuk=H(stu.hex()+str(s_prime_tp))
                restuk = Fpuf(chetuk)
                PIDtk = H(RIDk.hex() + restuk.hex()) 
                m3a=int.from_bytes(stu, byteorder='big')^int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex() + restik.hex()), byteorder='big')
                m3b=int.from_bytes(chetuk) ^ int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex() + restik.hex()+str(tu)), byteorder='big')
                m3c=int.from_bytes(restuk) ^ int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex() + restik.hex()+str(tu)+chetuk.hex()), byteorder='big')
                m3d=int.from_bytes(H(GIDz.hex() + str(tu) + RIDk.hex()+restik.hex()+str(tu)+chetuk.hex()+restuk.hex()+PIDtk.hex()),byteorder='big')

                stu=RandNum(tu)
                M3 = {
                    "GIDz": GIDz.hex(),           # Convert GIDz to hex string
                    "tu": tu,                     # Keep tu as is (it's an integer)
                    "PIDtk": PIDtk.hex(),         # Convert PIDtk to hex string
                    "m3a": hex(m3a),              # m3a is already an integer
                    "m3b": hex(m3b),              # m3b is already an integer
                    "m3c": hex(m3c),              # m3c is already an integer
                    "m3d": hex(m3d),              # m3d is already an integer
                    "stu": stu.hex(),             # Convert stu to hex string
                    "s_prime_tp": hex(s_prime_tp),   # Convert sprime to hex string if it's bytes
                    "restuk": restuk.hex(),       # Convert restuk to hex string
                    "DTk": tasks,                 # Include the received tasks
                    "chetuk": chetuk.hex(),       # Convert chetuk to hex string
                    "restik": restik.hex(),       # Convert restik to hex string
                    "RIDk": RIDk.hex(),           # Convert RIDk to hex string
                }

                # Send to Control Center
                print("Drone: Sending M3 to Control Center")
                SecureSend(drone_socket, M3)


# Example usage
if __name__ == "__main__":
    DroneRegistration_Authenticationplus()
