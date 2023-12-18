from socket import *
import hashlib
import secrets
import string
import random

def create_socket():
    serverSocket = socket(AF_INET, SOCK_STREAM)
    return serverSocket

def bind_socket(serverSocket, serverPort):
    serverSocket.bind(('', serverPort))

def start_listening(serverSocket):
    serverSocket.listen(1)

def accept_connection(serverSocket):
    connectionSocket = serverSocket.accept()
    return connectionSocket

def send_packet(connectionSocket, message):
    connectionSocket.send(message.encode())

def receive_packet(connectionSocket, buffer_size):
    received_data = connectionSocket.recv(buffer_size).decode()
    return received_data

def close_connection(connectionSocket):
    connectionSocket.close()

def start_game(sock):
    print('Game started.')

    number = random.randint(0, 36)
    print('Number is ' + str(number))
    send_packet(sock, str(number))

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
        connectionSocket = accept_connection(serverSocket)
        message = receive_packet(connectionSocket, 1024)
        if message == 'Start_Connection':
            print('Beginning auth process...')
            if not authenticate(privateString, connectionSocket):
                break
        close_connection(connectionSocket)

if __name__ == "__main__":
    main()
