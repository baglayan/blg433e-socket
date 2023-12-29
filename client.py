# Meriç Bağlayan
# 150190056
# Client for BLG 433E Socket Programming assignmnet

# Requires Python 3.10 or higher

# Usage: python3 client.py [<private string> <server address:port>]

from socket import *
import hashlib
import threading
import time
import sys
import os

in_game: bool = False
game_start_event: threading.Event = threading.Event()

def create_socket(serverName: str, serverPort: int) -> socket:
    clientSocket: socket = socket(AF_INET, SOCK_STREAM)
    clientSocket.connect((serverName, serverPort))
    return clientSocket

def receive_async(sock: socket) -> None:
    global in_game, game_start_event
    payload_size: int
    payload: bytes
    while True:
        message_type: bytes = sock.recv(1)
        if message_type:
            match message_type:
                case b'\x00':
                    in_game = True
                    game_start_event.set()
                    payload_size: int = int.from_bytes(sock.recv(1))
                    payload: bytes = sock.recv(payload_size)
                    message: str = payload.decode()
                    print('[SERVER] ' + message)
                case b'\x01':
                    payload_size: int = int.from_bytes(sock.recv(1), 'big')
                    payload = sock.recv(payload_size)
                    print('[SERVER] Remaining time: ' + payload.decode())
                case b'\x02':
                    in_game = False
                    payload_size: int = int.from_bytes(sock.recv(1), 'big')
                    payload = sock.recv(payload_size)
                    print('[SERVER] ' + payload.decode())
                case _:
                    print('Unknown message type received. Aborting...')
                    break

def send_async_in_game(sock: socket) -> None:
    global in_game, game_start_event
    while True:
        while in_game:
            game_start_event.wait()
            print('Available commands: end, time, <guess>')
            print('Available guesses: a number from 0 to 36 (inclusive), \'even\', \'odd\'')
            command: str = input()
            
            match command:
                case 'end':
                    send_command(sock, bytearray(b'\x01'), None)
                case 'time':
                    send_command(sock, bytearray(b'\x02'), None)
                case _:
                    send_command(sock, bytearray(b'\x03'), bytearray(command.encode()))
            game_start_event.clear()
            
def send_async_not_game(sock: socket) -> None:
    global in_game, game_start_event
    while True:
        while not in_game:
            print('Available commands: start, exit')
            command: str = input()
            
            match command:
                case 'start':
                    send_command(sock, bytearray(b'\x00'), None)
                    in_game = True
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

privateString: str = 'TSnYnfiJyMQYZqAbfptOPFfsmpWNMNEx'
serverName: str = '13.48.194.17'
serverPort: int = 3650

def main() -> None:
    if len(sys.argv) > 1:
        privateString = sys.argv[1]
    elif len(sys.argv) > 2:
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

        send_thread_in_game: threading.Thread = threading.Thread(target=send_async_in_game, args=(clientSocket,))
        send_thread_in_game.start()
        
        send_thread_not_game: threading.Thread = threading.Thread(target=send_async_not_game, args=(clientSocket,))
        send_thread_not_game.start()

if __name__ == '__main__':
    main()