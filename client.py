from socket import *
import hashlib
import threading
import struct

def create_socket(serverName, serverPort):
    clientSocket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    return clientSocket

def receive_async(sock):
    print('Start receive_async')
    while True:
            message_type = sock.recv(1)
            match message_type:
                case b'\x00':
                    payload_size = sock.recv(1)
                    payload = sock.recv(payload_size[0]).decode()
                    print('[SERVER] ' + payload)
                case b'\x01':
                    payload_size = sock.recv(1)
                    payload = sock.recv(payload_size[0])
                    print('[SERVER] Remaining time: ' + struct.unpack('>H', payload)[0])
                case b'\x02':
                    payload_size = sock.recv(1)
                    payload = sock.recv(payload_size[0])
                    print('[SERVER] Game over: ' + struct.unpack('>h', payload)[0])
                case _:
                    print('Unknown message type received. Aborting...')
                    break
        
def send_async(sock):
    print('Available commands: start, end, time, <guess>')
    while True:
        command = input()
        match command:
            case 'start':
                send_command(sock, 0, None)
            case 'end':
                send_command(sock, 1, None)
            case 'time':
                send_command(sock, 2, None)
            case _:
                send_command(sock, 3, command.encode())

def send_message(sock, message):
    sock.send(message.encode())
    
def send_command(sock, type, data):
    command = bytearray()
    command.append(type & 0xff) # ensure it's a byte
    
    if data:
        payload_size = len(data)
        command.append(payload_size & 0xff)
    
    match type:
        case 0, 1, 2:
            pass
        case 3:
            command.extend(data.encode())
            
    sock.send(command)

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

    receive_thread = threading.Thread(target=receive_async, args=(clientSocket,))
    receive_thread.start()

    send_thread = threading.Thread(target=send_async, args=(clientSocket,))
    send_thread.start()

    receive_thread.join()
    send_thread.join()

    close_socket(clientSocket)

if __name__ == '__main__':
    main()
