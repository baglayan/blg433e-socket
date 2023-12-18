from socket import *
import hashlib

def create_socket(serverName, serverPort):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    return clientSocket

def receive_message(sock):
    message = sock.recv(1024).decode()
    print('[SERVER] ' + message)

def send_message(sock, message):
    sock.send(message.encode())

def authenticate(sock, privateString):
    randomString = sock.recv(32).decode()
    if len(randomString) != 32:
        raise RuntimeError('Non-standard random string received. Aborting...')
    concatString = privateString + randomString

    if len(concatString) != 64:
        raise RuntimeError('Non-standard auth string detected. Aborting...')

    sha1Result = hashlib.sha1(concatString.encode()).hexdigest()

    send_message(sock, sha1Result)

    postShaMessage = sock.recv(1024).decode()
    print('[SERVER] ' + postShaMessage)

    if postShaMessage == 'Authentication succesful. Do you wish to proceed?' or postShaMessage == 'Authentication successful. Do you wish to proceed?':
        send_message(sock, input())

def close_socket(sock):
    sock.close()

def main():
    privateString = '43d48a355933d4964751cd8c3d1f4ffe'
    serverName = 'localhost'
    serverPort = 12000

    clientSocket = create_socket(serverName, serverPort)

    startConnectionString = 'Start_Connection'
    send_message(clientSocket, startConnectionString)

    authenticate(clientSocket, privateString)

    close_socket(clientSocket)

if __name__ == '__main__':
    main()
