"""
Server Program
server.py

S11
CSNETWK MP | File Exchange System
Lapuz, Salvador Mari
Roco, Gwen Kathleen
Tabadero, Audrea Arjaemi
"""

import socket
import threading
import os
from datetime import datetime
import keyboard
import sys
import tqdm

# dictionary to store connected clients and their handles
connected_clients = {}


# main function to start the server
def main():
    global server_socket
    global server_ip
    global server_port
    global server_files_directory
    global server_files
    server_files = {}
    server_ip = 'localhost'
    server_port = 9999
    server_files_directory = serverFilesDir()
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((server_ip, server_port))
    server_socket.listen(5)

    print(f"File Exchange Server is listening on {server_ip}:{server_port}")

    # server force shutdown (ESC)
    def on_key_press(event):
        if event.name == 'esc':
            print("User has pressed Escape. Force Shutting Down Server...")
            server_socket.close()
            sys.exit()

    keyboard.on_press(on_key_press)

    try:
        while True:
            client_socket, client_address = server_socket.accept()
            client_handler = threading.Thread(target=handle_client, args=(client_socket, client_address))
            client_handler.start()

    except (KeyboardInterrupt, OSError) as e:
        if isinstance(e, KeyboardInterrupt):
            pass
        elif isinstance(e, OSError):
            if e.errno == 10038:
                pass
            else:
                # Handle other OSError cases
                print(f"OSError: {e}")
        else:
            # Handle other exceptions
            print(f"Unexpected error: {e}")

    server_socket.close()
    keyboard.unhook_all()


# function to handle client connections
def handle_client(client_socket, client_address):
    try:
        print(f"New connection from {client_address}")
        
        while True:
            initial_msg = client_socket.recv(1024).decode()
            if not initial_msg:
                break 
            process_command(client_socket, initial_msg)

    except socket.error:
        print(f"Error: Connection to the Server has failed! Please check IP Address and Port Number")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

def process_command(client_socket, initial_msg):
    try:
        command_type = initial_msg.split()[0]

        if command_type == "/join":
            join(client_socket)

        if command_type == "/leave":
            leave(client_socket)

        elif command_type == "/register":
            register(client_socket, initial_msg)

        elif command_type == "/store":
            store(client_socket)

        elif command_type == "/dir":
            send_dir_list(client_socket)

        elif command_type == "/get":
            download_files(client_socket, initial_msg)

        elif command_type == "/broadcast":
            pass

        elif command_type == "/unicast":
            pass

        else:
            pass
        
        client_add = client_socket.getpeername()
        print(f"{client_add}: [{command_type}]")

    except socket.error:
        print("Error: Failed to receive command response.")
    except Exception as e:
        print(f"Error: {e}")

    
# /join
def join(client_socket):
    client_address = client_socket.getpeername()
    connected_clients[client_address] = "" # adds client to list of connected clients

# initializes ServerFilesDirectory -> used for /dir
def serverFilesDir():
    current_directory = os.getcwd()
    folder_name = 'ServerFiles-' + server_ip + "-" + str(server_port)
    folder_path = os.path.join(current_directory, folder_name)
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    
    return folder_path

# /dir
def send_dir_list(client_socket):
    try:
        file_list = os.listdir(server_files_directory)
        server_files = {index+1: filename for index, filename in enumerate(file_list)}

        file_list_with_numbers = ""
        for index, filename in server_files.items(): # updates server_files {}
            file_list_with_numbers += f"{index}. {os.path.basename(filename)}\n"

        client_socket.send(f"Server Directory\n\n{file_list_with_numbers}\n".encode())

    except Exception as e:
        send_error_message(client_socket, f"Error getting directory list: {e} [/dir]")

def send_error_message(client_socket, error_message):
    client_socket.send(f"Error: {error_message}\n".encode())

def send_success_message(client_socket, message):
    client_socket.send(f"Success: {message}\n".encode())

# /store
def store(client_socket):
    client = client_socket
    file_info = client.recv(1024).decode()
    # print(file_info)

    file_name, file_size = file_info.split("<DELIMITER>")
    file_size = int(file_size)

    current_directory = os.getcwd()
    folder_name = 'ServerFiles-' + server_ip + "-" + str(server_port)
    folder_path = os.path.join(current_directory, folder_name)
    os.makedirs(folder_path, exist_ok=True)
    file_path = os.path.join(folder_path, file_name)

    file = open(file_path, "wb")
    file_bytes = b""

    done = False

    progress = tqdm.tqdm(unit="B", unit_scale=True, unit_divisor=1000, total=int(file_size))

    while not done:
        data = client.recv(1024)
        if not data:
            done = True
            break
        file_bytes += data
        progress.update(len(data))

        if len(file_bytes) >= file_size:
            done = True
    
    server_files[len(server_files) + 1] = file_name
    file.write(file_bytes)
    file.close()

# /get
def download_files(client_socket, initial_msg):
    file_name = initial_msg[len("/get "):]
    try:
        file_path = os.path.join(serverFilesDir(), file_name)
        # print(file_path)

        if os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                file_content = file.read()

                file_size = os.path.getsize(file_path)
                client_socket.send(str(file_size).encode())

                client_socket.sendall(file_content)
        else:
            # file not found
            client_socket.send('File not found'.encode())
    except ValueError as ve:
        print(f"Error downloading file: {ve}")
        client_socket.send('File not found'.encode())

    except Exception as e:
        print(f"Error downloading file: {e}")
        client_socket.send('File not found'.encode())

# /register
def register(client_socket, initial_msg):
    client_address = client_socket.getpeername()
    handle = initial_msg.split()[1]
    handle_exists = False
    for value in connected_clients.values():
        if value == handle:
            handle_exists = True
            break

    if handle_exists:
        client_socket.send("taken".encode())
        print(f"Error: {client_address} | Handle {handle} already taken.")
    else:
        client_socket.send("good".encode())
        connected_clients[client_address] = handle
        # print(handle)
        # for client_address, handle in connected_clients.items():
        #     print("Client Address:", client_address)
        #     print("Handle:", handle)

# /leave
def leave(client_socket):
    client_address = client_socket.getpeername()
    handle = connected_clients[client_address]
    print(f"Connection from {client_address} closed.")
    client_socket.close()
    # client_socket.send("{handle} has left the room.".encode())
    del connected_clients[client_address]

    # if no more connected users = server shuts down
    if len(connected_clients) == 0:
        print("No clients connected. Server is shutting down.")
        server_socket.close()
        sys.exit()
    else:
        print("Remaining clients:")
        for client_address, handle in connected_clients.items():
            print(f"Client Address: {client_address}, Handle: {handle}")


if __name__ == "__main__":
    main()
