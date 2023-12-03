from socket import *
import hashlib
import string

def receive_messages(sock):
    while True:
        message = sock.recv(1024).decode()
        print('[SERVER] ' + message)
    
def update_game(sock):
    while True:
        message = input()
        sock.send(message.encode())

privateString = '43d48a355933d4964751cd8c3d1f4ffe'

serverName = 'localhost'
serverPort = 12000

clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect((serverName, serverPort))

startConnectionString = 'Start_Connection'

clientSocket.send(startConnectionString.encode())

randomString = clientSocket.recv(32).decode()
if len(randomString) != 32:
    raise RuntimeError('Non-standard random string received. Aborting...')
concatString = privateString + randomString

if len(concatString) != 64:
    raise RuntimeError('Non-standard auth string detected. Aborting...')

sha1Result = hashlib.sha1(concatString.encode()).hexdigest()

clientSocket.send(sha1Result.encode())

postShaMessage = clientSocket.recv(1024).decode()
print('[SERVER] ' + postShaMessage)

if postShaMessage == 'Authentication succesful. Do you wish to proceed?' or postShaMessage == 'Authentication successful. Do you wish to proceed?':
    clientSocket.send(input().encode())

clientSocket.close()