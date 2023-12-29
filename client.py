# Meriç Bağlayan
# 150190056
# BLG 433E 2023-2024 Fall Socket Programming assignment
# Client

# Requires Python 3.10 or higher

# Usage: python3 client.py [<private string> <server address:port>]

from socket import *
import hashlib
import time
import threading
import sys
import os

in_game: bool = False

def init_game() -> None:
    global in_game
    
    in_game = True
    
def finalize_game() -> None:
    global in_game
    
    in_game = False
    
def create_socket(serverName: str, serverPort: int) -> socket:
    clientSocket: socket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    return clientSocket

def receive_async(sock: socket) -> None:
    payload_size: int
    payload: bytes
    while True:
        message_type: bytes = sock.recv(1)
        if message_type:
            match message_type:
                case b'\x00':
                    payload_size: int = int.from_bytes(sock.recv(1))
                    payload: bytes = sock.recv(payload_size)
                    message: str = payload.decode()
                    print('[SERVER] ' + message)
                case b'\x01':
                    payload_size: int = int.from_bytes(sock.recv(1), 'big')
                    payload = sock.recv(payload_size)
                    print('[SERVER] ' + payload.decode())
                case b'\x02':
                    payload_size: int = int.from_bytes(sock.recv(1), 'big')
                    payload = sock.recv(payload_size)
                    print('[SERVER] ' + payload.decode())
                    finalize_game()
                case _:
                    print('Unknown message type received. Aborting...')
                    break

def send_async(sock: socket) -> None:
    global in_game
    while True:
        if in_game:
            print('Available commands: end, time, <guess>')
            print("Guess types: 'even', 'odd', number")
            
            
            command: str = input()
            
            match command.lower():
                case 'end':
                    send_command(sock, bytearray(b'\x01'), None)
                case 'time':
                    send_command(sock, bytearray(b'\x02'), None)
                case 'even':
                    send_command(sock, bytearray(b'\x03'), bytearray(command.encode()))
                case 'odd':
                    send_command(sock, bytearray(b'\x03'), bytearray(command.encode()))
                case _:
                    send_command(sock, bytearray(b'\x03'), bytearray(command.encode()))
        if not in_game:
            print('Available commands: start, exit')
            command: str = input()
            
            match command.lower():
                case 'start':
                    init_game()
                    send_command(sock, bytearray(b'\x00'), None)
                case 'exit':
                    send_command(sock, bytearray(b'\x01'), None)
                    close_socket(sock)
                    os._exit(1)
                case _:
                    print('Unknown command.')

def send_message(sock: socket, message: str) -> None:
    sock.send(message.encode())
    
def send_command(sock: socket, type: bytearray, data: bytearray | None) -> None:
    command: bytearray = bytearray(type)
    
    if data:
        payload_size: bytes = len(data).to_bytes(1, 'big')
        command.extend(payload_size)
        command.extend(data)

    sock.send(command)

def authenticate(sock: socket, privateString: str) -> None:
    randomString: str = sock.recv(32).decode()
    if len(randomString) != 32:
        raise RuntimeError('Non-standard random string received. Aborting...')
    concatString: str = privateString + randomString

    if len(concatString) != 64:
        raise RuntimeError('Non-standard auth string detected. Aborting...')

    sha1Result: str = hashlib.sha1(concatString.encode()).hexdigest()

    send_message(sock, sha1Result)

    postShaMessage: str = sock.recv(1024).decode()
    print('[SERVER] ' + postShaMessage)

    if postShaMessage == 'Authentication succesful. Do you wish to proceed?' or postShaMessage == 'Authentication successful. Do you wish to proceed?':
        print('Y or N?')
        proper_response: bool = False
        
        while not proper_response:
            proceedResponse: str = input()
            match proceedResponse.capitalize():
                case 'Y':
                    proper_response = True
                    send_message(sock, 'Y')
                    return
                case 'N':
                    proper_response = True
                    send_message(sock, 'N')
                    close_socket(sock)
                    os._exit(1)
                case _:
                    print('Unknown response received. Y or N?')
    else:
        print('Unknown message received. Aborting...')
        close_socket(sock)
        os._exit(1)

def close_socket(sock: socket) -> None:
    sock.close()

def main() -> None:
    if len(sys.argv) > 1:
        privateString = sys.argv[1]
    if len(sys.argv) > 2:
        serverName = sys.argv[2].split(':')[0]
        serverPort = int(sys.argv[2].split(':')[1])
    else:
        print('No arguments provided. Using default values for private string and server address.')
        print('To use custom values, run the program in this format: python3 client.py <private string> <server address:port>')

        privateString: str = '43d48a355933d4964751cd8c3d1f4ffe'
        serverName: str = 'localhost'
        serverPort: int = 12000
        
    clientSocket: socket
    print('Attempting to connect to server...')
    
    for connection_attempt in range(3):
        try:
            clientSocket = create_socket(serverName, serverPort)
            break
        except ConnectionRefusedError:
            if connection_attempt < 2:
                print('Connection to server refused. Retrying...')
                time.sleep(2)
            else:
                print('Could not connect to the server. Aborting...')
                os._exit(1)

    startConnectionString: str = 'Start_Connection'
    
    send_message(clientSocket, startConnectionString)
    authenticate(clientSocket, privateString)
    
    receive_thread: threading.Thread = threading.Thread(target=receive_async, args=(clientSocket,))
    receive_thread.start()

    send_thread: threading.Thread = threading.Thread(target=send_async, args=(clientSocket,))
    send_thread.start()
    
    receive_thread.join()
    send_thread.join()

if __name__ == '__main__':
    main()