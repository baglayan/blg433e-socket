from socket import *
import hashlib
import secrets
import string
import random
import struct

def create_socket():
    return socket(AF_INET, SOCK_STREAM)

def bind_socket(sock, port):
    sock.bind(('', port))

def start_listening(sock):
    sock.listen(1)

def accept_connection(sock):
    return sock.accept()

def send_packet(sock, message):
    sock.send(message.encode())
    
def send_server_message(sock, type, data):
    message = bytearray()
    message.append(type & 0xff) # ensure it's a byte
    
    payload_size = len(data)
    message.append(payload_size & 0xff)
    
    match type:
        case 0:
            message.extend(data.encode())
        case 1:
            message.extend(struct.pack('>H', data))
        case 2:
            message.extend(struct.pack('>h', data))
        case _:
            raise RuntimeError('Unknown packet type specified. Aborting...')
            
    send_packet(sock, message)

def receive_packet(sock, buffer_size):
    return sock.recv(buffer_size).decode()

def close_connection(sock):
    sock.close()

def start_game(sock):
    print('Game started.')

    number = random.randint(0, 36)
    print('Number is ' + str(number))
    send_server_message(sock, 0, "What is your guess? Number, even, odd?")

def update_game(sock):
    print('Update')

def authenticate(privateString, connectionSocket):
    randomString = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(32))
    send_packet(connectionSocket, randomString)
    
    concatString = privateString + randomString
    calculatedHash = hashlib.sha1(concatString.encode()).hexdigest()
    
    receivedHash = receive_packet(connectionSocket, 40)
    
    if len(receivedHash) != 40:
        raise RuntimeError('Non-standard auth string received. Aborting...')
    
    if calculatedHash == receivedHash:
        print('Authentication successful!')
        successMessage = 'Authentication succesful. Do you wish to proceed?'
        send_packet(connectionSocket, successMessage)
        proceed = receive_packet(connectionSocket, 1)
        
        if proceed.capitalize() == 'Y':
            start_game(connectionSocket)
        elif proceed.capitalize() == 'N':
            close_connection(connectionSocket)
            return False
    else:
        print('Authentication failed.')
        unauthorizedMessage = 'Unauthorized access.'
        send_packet(connectionSocket, unauthorizedMessage)
    return True

def main():
    privateString = '43d48a355933d4964751cd8c3d1f4ffe'

    serverPort = 12000
    serverSocket = create_socket()
    bind_socket(serverSocket, serverPort)
    start_listening(serverSocket)

    print('Awaiting Start_Connection message...')

    while True:
        connectionSocket, addr = accept_connection(serverSocket)
        message = receive_packet(connectionSocket, 1024)
        if message == 'Start_Connection':
            print('Beginning auth process...')
            if not authenticate(privateString, connectionSocket):
                break
        close_connection(connectionSocket)

if __name__ == "__main__":
    main()
