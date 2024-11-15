import socket
import threading
import os
import logging
import sys
import signal

SERVER_HOST          = '127.0.0.1'
SERVER_PORT          = 6368
CURRENT_FILE_DIR     = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR           = os.path.join(CURRENT_FILE_DIR, 'uploads')
LOG_FILE_DIR         = os.path.join(CURRENT_FILE_DIR, 'log')
LOG_FILE_NAME        = os.path.join(LOG_FILE_DIR, 'server.log')
BUFFER_SIZE          = 4096

if not os.path.exists(LOG_FILE_DIR):
    os.makedirs(LOG_FILE_DIR)

# Setting up logging
logging.basicConfig(
    filename=LOG_FILE_NAME,
    level=logging.INFO,
    format='%(asctime)s:%(levelname)s:%(message)s',
    filemode='a'  # append mode
)

if not os.path.exists(UPLOAD_DIR):
    logging.info(f'Upload directory created at {UPLOAD_DIR}')
    os.makedirs(UPLOAD_DIR)

# Create an Event object that will be used to signal threads to exit
exit_event = threading.Event()
client_threads = []  # Keep track of client handler threads

def handle_client(client_socket, client_addr, exit_event):
    logging.info(f'[+] Accept connection from {client_addr}')
    client_socket.settimeout(1)  # Set a timeout for blocking operations
    try:
        while not exit_event.is_set():
            try:
                logging.info(f'Receive message from {client_addr}')
                data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
                if not data:
                    break  # Connection closed by client
                if data == 'quit':
                    break
                print(f'Client {client_addr}: {data}')
                msg = input('Server: ')
                client_socket.sendall(bytes(msg, 'utf-8'))
                logging.info(f'Sending message to {client_addr}')
            except socket.timeout:
                continue  # Timeout occurred, loop back and check exit_event
            except ConnectionResetError:
                break  # Client disconnected
    finally:
        client_socket.close()
        print(f'Connection with {client_addr} closed.')

def sigint_handler(sig, frame):
    print("[*] 😴 Shutting down server.")
    logging.info("Server shutting down.")
    exit_event.set()  # Signal all threads to exit
    sys.exit(0)

def start_server():
    signal.signal(signal.SIGINT, sigint_handler)  # Register SIGINT handler
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind((SERVER_HOST, SERVER_PORT))
    server_socket.listen(5)

    server_socket.settimeout(1.0)
    logging.info(f'Server started on {SERVER_HOST}:{SERVER_PORT}')
    print(f'[*] 👂 Listening on {SERVER_HOST}:{SERVER_PORT}')

    try:
        while not exit_event.is_set():
            try:
                client_socket, client_address = server_socket.accept()
                print(f'Accepted connection from {client_address}')
                client_handler = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_address, exit_event)
                )
                client_handler.start()
                client_threads.append(client_handler)
            except socket.timeout:
                continue  # Loop back and check exit_event
            except Exception as e:
                logging.error(f"Error accepting connections: {e}")
                break
    finally:
        server_socket.close()
        print("[*] Server socket closed.")
        # Wait for all client threads to finish
        for t in client_threads:
            t.join()
        print("[*] All client threads have been terminated.")

if __name__ == '__main__':
    logging.info('Starting server')
    start_server()
    logging.info('Server stopped')
