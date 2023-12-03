from socket import *
import hashlib
import secrets
import string
import random

def start_game(connectionSocket):
    print('Game started.')

    number = random.randint(0, 36)
    print('Number is ' + str(number))
    connectionSocket.send

def update_game(connectionSocket):
    print('Update')

privateString = '43d48a355933d4964751cd8c3d1f4ffe'

serverPort = 12000
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(('', serverPort))
serverSocket.listen(1)

print('Awaiting Start_Connection message...')

while True:
    connectionSocket, addr = serverSocket.accept()
    message = connectionSocket.recv(1024).decode()
    if message == 'Start_Connection':
        print('Beginning auth process...')
        randomString = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(32))
        print(randomString)
        connectionSocket.send(randomString.encode())
        concatString = privateString + randomString
        calculatedHash = hashlib.sha1(concatString.encode()).hexdigest()
        receivedHash = connectionSocket.recv(40).decode()
        if len(receivedHash) != 40:
            raise RuntimeError('Non-standard auth string received. Aborting...')
        if calculatedHash == receivedHash:
            print('Authentication successful!')
            successMessage = 'Authentication succesful. Do you wish to proceed?'
            connectionSocket.send(successMessage.encode())
            proceed = connectionSocket.recv(1).decode()
            if proceed.capitalize() == 'Y':
                start_game(connectionSocket)
            elif proceed.capitalize() == 'N':
                connectionSocket.close()
                break
        else:
            print('Authentication failed.')
            unauthorizedMessage = 'Unauthorized access.'
            connectionSocket.send(unauthorizedMessage.encode())
        connectionSocket.close()
        break
    connectionSocket.close()
    