import socket
import threading
import os
import logging
import sys
import signal

class Server:
    def __init__(self, host='127.0.0.1', port=6368):
        self.SERVER_HOST = host
        self.SERVER_PORT = port
        self.CURRENT_FILE_DIR = os.path.dirname(os.path.abspath(__file__))
        self.UPLOAD_DIR = os.path.join(self.CURRENT_FILE_DIR, 'uploads')
        self.LOG_FILE_DIR = os.path.join(self.CURRENT_FILE_DIR, 'log')
        self.LOG_FILE_NAME = os.path.join(self.LOG_FILE_DIR, 'server.log')
        self.BUFFER_SIZE = 4096

        self.exit_event = threading.Event()
        self.client_threads = []

        self.setup_logging()
        self.setup_directories()
        self.server_socket = None

    def setup_logging(self):
        if not os.path.exists(self.LOG_FILE_DIR):
            os.makedirs(self.LOG_FILE_DIR)

        logging.basicConfig(
            filename=self.LOG_FILE_NAME,
            level=logging.INFO,
            format='%(asctime)s:%(levelname)s:%(message)s',
            filemode='a'  # Append mode
        )

    def setup_directories(self):
        if not os.path.exists(self.UPLOAD_DIR):
            os.makedirs(self.UPLOAD_DIR)
            logging.info(f'Upload directory created at {self.UPLOAD_DIR}')

    def sigint_handler(self, sig, frame):
        print("[*] 😴 Shutting down server.")
        logging.info("Server shutting down.")
        self.exit_event.set()
        sys.exit(0)

    def start(self):
        signal.signal(signal.SIGINT, self.sigint_handler)  # Register SIGINT handler

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.SERVER_HOST, self.SERVER_PORT))
        self.server_socket.listen(5)

        self.server_socket.settimeout(1.0)
        logging.info(f'Server started on {self.SERVER_HOST}:{self.SERVER_PORT}')
        print(f'[*] 👂 Listening on {self.SERVER_HOST}:{self.SERVER_PORT}')

        try:
            while not self.exit_event.is_set():
                try:
                    client_socket, client_address = self.server_socket.accept()
                    print(f'Accepted connection from {client_address}')
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.start()
                    self.client_threads.append(client_thread)
                except socket.timeout:
                    continue  # Loop back and check exit_event
                except Exception as e:
                    logging.error(f"Error accepting connections: {e}")
                    break
        finally:
            self.shutdown()

    def handle_client(self, client_socket, client_address):
        logging.info(f'[+] Accepted connection from {client_address}')
        client_socket.settimeout(1)  # Set a timeout for blocking operations
        try:
            while not self.exit_event.is_set():
                try:
                    logging.info(f'Receiving message from {client_address}')
                    data = client_socket.recv(self.BUFFER_SIZE).decode('utf-8')
                    if not data:
                        break  # Connection closed by client
                    if data == 'quit':
                        break
                    print(f'Client {client_address}: {data}')
                    msg = input('Server: ')
                    client_socket.sendall(msg.encode('utf-8'))
                    logging.info(f'Sent message to {client_address}')
                except socket.timeout:
                    continue  # Timeout occurred, loop back and check exit_event
                except ConnectionResetError:
                    break  # Client disconnected
        finally:
            client_socket.close()
            print(f'Connection with {client_address} closed.')

    def shutdown(self):
        if self.server_socket:
            self.server_socket.close()
            print("[*] Server socket closed.")
        # Wait for all client threads to finish
        for t in self.client_threads:
            t.join()
        print("[*] All client threads have been terminated.")

if __name__ == '__main__':
    logging.info('Starting server')
    server = Server()
    server.start()
    logging.info('Server stopped')