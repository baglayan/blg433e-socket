# Meriç Bağlayan
# 150190056
# Server for BLG 433E Socket Programming assignmnet

# Requires Python 3.10 or higher

from socket import *
import hashlib
import secrets
import string
import random
import sys
import threading
import time

number: int
remaining_time: int = 30

in_game: bool = False
parity_guessed: bool = False
points: int = 0

timer_start_event: threading.Event = threading.Event()

def init_game() -> None:
    global remaining_time, in_game, parity_guessed, points, timer_start_event
    
    remaining_time = 30
    in_game = True
    parity_guessed = False
    points = 0
    timer_start_event.set()
    
    log('Game initalized')
    
def finalize_game() -> None:
    global in_game, parity_guessed, points, timer_start_event
    
    in_game = False
    parity_guessed = False
    timer_start_event.clear()
    
    log('Game finalized')

def wait_start(sock: socket) -> None:
    global in_game
    log('Waiting for client to initiate game start')
    while True:
        message_type: bytes = sock.recv(1)
        if message_type:
            match message_type:
                case b'\x00':
                    log('Client initiated game start')
                    if not in_game:
                        start_game(sock)
                    else:
                        log('Client tried to start game while already in game. Ignoring')
                case b'\x01':
                    log('Client quit before the game was even started')
                    break
                case _:
                    raise RuntimeError('Unknown packet type received. Aborting')
                
def timer_async(sock: socket) -> None:
    global remaining_time, in_game, points, timer_start_event
    
    timer_start_event.wait()
    
    log('Timer started')
    
    while True:
        if not in_game:
            continue
        remaining_time_str = str(remaining_time)
        send_server_message(sock, bytearray(b'\x01'), bytearray(remaining_time_str, 'utf-8'))
        remaining_time -= 3
        if remaining_time <= 0:
            points -= 1
            game_log('1 point deducted from client')
            game_log(f'Client now has {points} points')
            send_server_message(sock, bytearray(b'\x02'), bytearray("Your time is up! Be quicker next time.", 'utf-8'))
            send_server_message(sock, bytearray(b'\x02'), bytearray(f"You have {points} points.", 'utf-8'))
            finalize_game()
            return
        time.sleep(3)
        timer_start_event.clear()

def start_game(sock: socket) -> None:
    global remaining_time, parity_guessed, timer_start_event
    
    init_game()

    global number
    number = random.randint(0, 36)
    game_log('Number is ' + str(number))
    
    update_game(sock)
    
    
def update_game(sock: socket) -> None:
    global number, points, in_game, parity_guessed
    while True:
        if not in_game:
            return
        while in_game:
            send_server_message(sock, bytearray(b'\x00'), bytearray("What is your guess? Number, even, odd?", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray("Available guesses: a number from 0 to 36 (inclusive), \'even\', \'odd\'", 'utf-8'))
            message_type: bytes = receive_packet(sock, 1)
            
            match message_type:
                case b'\x01':
                    finalize_game()
                case b'\x02':
                    log('Client requested time')
                    send_server_message(sock, bytearray(b'\x01'), bytearray(remaining_time))
                case b'\x03':
                    payload_size: int = int.from_bytes(receive_packet(sock, 1))
                    
                    guess_payload: bytes  = receive_packet(sock, payload_size)
                    guess_str = guess_payload.decode()
                    guess = int | str
                    
                    is_guess_number: bool = False
                    
                    if guess_str.isnumeric():
                        guess = int(guess_str)
                        is_guess_number = True
                    elif guess_str.lower() == 'even' or guess_str.lower() == 'odd':
                        guess = guess_str.lower()
                        
                    match is_guess_number:
                        case True:
                            game_log('Number received.')
                            handle_number_guess(sock, guess)
                        case False:
                            if not parity_guessed:
                                handle_word_guess(sock, guess)
                            
def handle_number_guess(sock: socket, guess: int | str | type[int] | type[str]) -> None:
    global points, in_game
    if guess == number:
        game_log('Correct guess')
        points += 35
        game_log('35 points added to client')
        game_log(f'Client now has {points} points')
        send_server_message(sock, bytearray(b'\x02'), bytearray("You won! Congratulations.", 'utf-8'))
        send_server_message(sock, bytearray(b'\x02'), bytearray(f"You have {points} points.", 'utf-8'))
        finalize_game()
    else:
        game_log('Wrong guess')
        points -= 1
        game_log('1 point deducted from client')
        game_log(f'Client now has {points} points')
        send_server_message(sock, bytearray(b'\x02'), bytearray("You lost! Better luck next time.", 'utf-8'))
        send_server_message(sock, bytearray(b'\x02'), bytearray(f"You have {points} points.", 'utf-8'))
        finalize_game()

def handle_word_guess(sock: socket, guess: str | int | type[int] | type[str]) -> None:
    global points, in_game, parity_guessed
    
    if guess == "even":
        game_log('Even received.')
        parity_guessed = True
        if number % 2 == 0:
            game_log('Correct guess')
            points += 1
            game_log('1 point added to client')
            game_log(f'Client now has {points} points')
            send_server_message(sock, bytearray(b'\x00'), bytearray("You guessed correctly! Now guess the number.", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray("Available guesses: a number from 0 to 36 (inclusive)", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray(f"You have {points} points.", 'utf-8'))
        else:
            game_log('Wrong guess')
            points -= 1
            game_log('1 point deducted from client')
            game_log(f'Client now has {points} points')
            send_server_message(sock, bytearray(b'\x00'), bytearray("Your guess is incorrect! But you can still guess the number.", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray("Available guesses: a number from 0 to 36 (inclusive)", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray(f"You have {points} points.", 'utf-8'))
    elif guess == "odd":
        game_log('Odd received.')
        parity_guessed = True
        if number % 2 == 0:
            game_log('Wrong guess')
            points -= 1
            game_log('1 point deducted from client')
            game_log(f'Client now has {points} points')
            send_server_message(sock, bytearray(b'\x00'), bytearray("Your guess is incorrect! But you can still guess the number.", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray("Available guesses: a number from 0 to 36 (inclusive)", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray(f"You have {points} points.", 'utf-8'))
        else:
            game_log('Unknown word guess')
            send_server_message(sock, bytearray(b'\x00'), bytearray("Unknown guess", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray("Available guesses: a number from 0 to 36 (inclusive), \'even\', \'odd\'", 'utf-8'))
            send_server_message(sock, bytearray(b'\x00'), bytearray(f"You have {points} points.", 'utf-8'))          
        
def info_log(message: str) -> None:
    print('[INFO] ' + message)
        
def log(message: str) -> None:
    print('[LOG] ' + message)
    
def game_log(message: str) -> None:
    print('[GAME] ' + message)
    
def auth_log(message: str) -> None:
    print('[AUTH] ' + message)

def create_socket() -> socket:
    return socket(AF_INET, SOCK_STREAM)

def bind_socket(sock: socket, port: int) -> None:
    try:
        sock.bind(('', port))
    except OSError:
        log('Port is already in use. Aborting')
        exit()
        
def start_listening(sock: socket) -> None:
    sock.listen(1)

def accept_connection(sock: socket) -> tuple[socket, tuple[str, int]]:
    return sock.accept()

def send_packet(sock: socket, message: bytearray) -> None:
    try:
        sock.send(message)
    except OSError as e:
        log(f"Error sending data: {e}")
    
def send_bytearray(sock: socket, message: bytearray) -> None:
    try:
        sock.send(message)
    except OSError as e:
        log(f"Error sending data: {e}")
    
def send_server_message(sock: socket, type: bytearray, data: bytearray) -> None:
    message: bytearray = bytearray()
    message.extend(type)
    
    payload_size: int = len(data)
    if 0 > payload_size or payload_size > 255:
        raise RuntimeError('Payload size is beyond limits. Aborting')
    payload_size_bytes: bytes = bytes([payload_size])
    message.extend(payload_size_bytes)
    
    match bytes(type):
        case b'\x00':
            message.extend(data)
        case b'\x01':
            message.extend(data)
        case b'\x02':
            message.extend(data)
        case _:
            raise RuntimeError('Unknown packet type specified. Aborting')
            
    send_bytearray(sock, message)

def receive_message(sock: socket, buffer_size: int) -> str:
    return receive_packet(sock, buffer_size).decode()

def receive_packet(sock: socket, buffer_size: int) -> bytes:
    try:
        return sock.recv(buffer_size)
    except ConnectionResetError or ConnectionRefusedError or ConnectionAbortedError or ConnectionError as e:
        log(f"Error receiving data: {e}")
        return b''


def close_connection(sock: socket) -> None:
    sock.close()

def authenticate(privateString: str, connectionSocket: socket) -> bool:
    randomString: str = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(32))
    send_packet(connectionSocket, bytearray(randomString, 'utf-8'))
    
    concatString: str = privateString + randomString
    calculatedHash: str = hashlib.sha1(concatString.encode()).hexdigest()
    
    receivedHash: str = receive_message(connectionSocket, 40)
    
    if len(receivedHash) != 40:
        raise RuntimeError('Non-standard auth string received. Aborting')
    
    if calculatedHash == receivedHash:
        auth_log('Authentication successful!')
        successMessage: str = 'Authentication succesful. Do you wish to proceed?'
        send_packet(connectionSocket, bytearray(successMessage, 'utf-8'))
        
    else:
        auth_log('Authentication failed.')
        unauthorizedMessage: str = 'Unauthorized access.'
        send_packet(connectionSocket, bytearray(unauthorizedMessage, 'utf-8'))
    return True

def main() -> None:
    if len(sys.argv) > 1:
        privateString = sys.argv[1]
        serverPort: int = 12000
    if len(sys.argv) > 2:
        serverPort = int(sys.argv[2])
    else:
        info_log('No arguments provided. Using default values for private string and server port.')
        info_log('To use custom values, run the program in this format: python3 server.py <private string> <server port>')

        privateString: str = '43d48a355933d4964751cd8c3d1f4ffe'
        serverPort: int = 12000
    
    serverSocket: socket = create_socket()
    bind_socket(serverSocket, serverPort)
    start_listening(serverSocket)

    log('Awaiting Start_Connection message')

    while True:
        connectionSocket, addr = accept_connection(serverSocket)
        print(addr)
        message: str = receive_message(connectionSocket, 1024)
        if message == 'Start_Connection':
            auth_log('Beginning auth process')
            if not authenticate(privateString, connectionSocket):
                break
            
            proceed: str = receive_message(connectionSocket, 1)
        
            if proceed.capitalize() == 'Y':
                log('Game accepted by client')
                
                game_thread = threading.Thread(target=wait_start, args=(connectionSocket,))
                game_thread.start()
                
                timer_thread = threading.Thread(target=timer_async, args=(connectionSocket,))
                timer_thread.start()
                
            elif proceed.capitalize() == 'N':
                log('Game rejected by client')
                # close_connection(connectionSocket)
                continue
        # close_connection(connectionSocket)

if __name__ == "__main__":
    main()
