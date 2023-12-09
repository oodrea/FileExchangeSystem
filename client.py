"""
Client Program
client.py

S11
CSNETWK MP | File Exchange System
Lapuz, Salvador Mari
Roco, Gwen Kathleen
Tabadero, Audrea Arjaemi
"""

import queue
import threading
import tkinter as tk
from tkinter import filedialog
import socket
import os
import time
from datetime import datetime
from tkinter import messagebox
from tkinter.scrolledtext import ScrolledText


class CustomException(Exception):
    def __init__(self, message="A custom exception occurred"):
        self.message = message
        super().__init__(self.message)

class FileSenderGUI(tk.Tk):
    def __init__(self):
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.root = tk.Tk()
        iconpath = os.path.join(os.getcwd(), 'misc', 'icon.ico')
        self.root.iconbitmap(iconpath)
        self.root.title("CSNETWK MP | File Exchange System")
        self.receive_thread = None
        self.server_address = tk.StringVar()
        self.server_port = tk.StringVar()
        self.handle = tk.StringVar()
        self.server_files_directory = ""
        self.receive_loop = True
        self.joined_server = False  # flag to track whether the user has joined the server
        self.join_button_hidden = False  # flag to track whether the "Join Server" button should be hidden
        self.download_window = None
        self.create_widgets()

    def create_widgets(self):
        # GUI Components
        label_server = tk.Label(self.root, text="Server Address:")
        label_server.pack(padx=10, pady=10)

        self.server_address_entry = tk.Entry(self.root, textvariable=self.server_address, state=tk.NORMAL)
        self.server_address_entry.pack(padx=10, pady=10)

        label_port = tk.Label(self.root, text="Server Port:")
        label_port.pack(padx=10, pady=10)

        self.server_port_entry = tk.Entry(self.root, textvariable=self.server_port, state=tk.NORMAL)
        self.server_port_entry.pack(padx=10, pady=10)

        self.message_textbox = ScrolledText(self.root, state=tk.DISABLED)

        self.join_button = tk.Button(self.root, text="Join Server", command=self.join_server)
        self.join_button.pack(pady=10)

        self.store_button = tk.Button(self.root, text="Store File", command=self.send_file, state=tk.NORMAL, height=1, width=10)
        self.get_button = tk.Button(self.root, text="Get File", command=self.open_download_window, state=tk.NORMAL, height=1, width=10)
        self.leave_button = tk.Button(self.root, text="Leave", command=self.leave, state=tk.NORMAL, height=1, width=20)
        self.listfiles_button = tk.Button(self.root, text="List Files", command=self.req_dir_list, state=tk.NORMAL, height=1, width=10)
        self.help_button = tk.Button(self.root, text="?", command=self.helpcommands, bg="blue")
        self.help_button.configure(foreground='white')
        self.handle_label = tk.Label(self.root, text="Handle:")
        self.register_entry = tk.Entry(self.root, textvariable=self.handle, state=tk.NORMAL)
        self.register_button = tk.Button(self.root, text="Register", command=self.register, state=tk.NORMAL)
        self.input_field = tk.Entry(self.root, width=110)
        self.send_button = tk.Button(self.root, text="Send", command=self.send_message)
        self.status_label = tk.Label(self.root, text="")

        self.top_frame = tk.Frame(self.root)

        self.status_label.pack(side= tk.BOTTOM, pady=10)

    # /?
    def helpcommands(self):
        messagebox.showinfo("Help", "Commands:\n\n"
                                    "Store File: Save Files to the Server\n"
                                    "Get File: Download Files from the Server\n"
                                    "List Files: Show Server Files Directory\n"
                                    "Leave: Disconnect from Server\n")
    
    # /join
    def join_server(self):
        try:
            server_port = int(self.server_port.get())
            server_address = str(self.server_address.get())
            self.server_address.set(self.server_address.get()) 
            self.server_port.set(self.server_port.get())  
            
            self.client_socket.connect((server_address, server_port))
            self.receive_thread = threading.Thread(target=self.receive_messages)
            self.receive_thread.start()
            self.client_socket.send("/join".encode())
            time.sleep(0.1)

        except (ValueError, ConnectionRefusedError) as e:
            if isinstance(e, ValueError):
                error_message = "Invalid port number. Please enter a valid port."
            elif isinstance(e, ConnectionRefusedError):
                error_message = "Connection refused. Please check the server address and port number."

            messagebox.showerror("Error", error_message)
    
    def handle_join(self):
        self.joined_server = True
        self.join_button_hidden = True
        self.server_address_entry.config(state=tk.DISABLED)
        self.server_port_entry.config(state=tk.DISABLED)
        self.join_button.pack_forget()  # Hide the "Join Server" button
            
        # Show the "handle" text field
        self.handle_label.pack(padx=10, pady=10)
        self.register_entry.pack(padx=10, pady=10)
        self.register_button.pack(pady=10)

        joinmsg = "Joined server " + self.server_address.get() + ":" + self.server_port.get() + " successfully!"
        messagebox.showinfo("wow!", "Connection to the File Exchange Server is Successful!")
        self.status_label.config(text=joinmsg)

    # /send message (for chatting WIP)
    def send_message(self):
        message = self.input_field.get()
        self.client_socket.send(message.encode())
        self.input_field.delete(0, tk.END)
    
    def handle_unicast(self, msg):
        self.displaymsg_withtime(msg[len("/unicast "):])

    # /register
    def register(self):
        try:
            if self.handle.get() == "":
                messagebox.showerror(">:(((", "Please enter a handle or alias.")
                return
            reg = "/register " + self.handle.get()
            self.client_socket.send(reg.encode())

        except CustomException as ce:
            self.status_label.config(text="Handle already exists! Please try again.")
    
    def handle_register(self, msg):
        check = msg.split()[1]
        if check == "taken":
            messagebox.showerror("Registration Failed", "Handle or alias already exists. Please try again.")
            
        elif check == "good":
            self.register_entry.config(state=tk.DISABLED)
            self.register_button.pack_forget()
                
            self.leave_button.pack(side=tk.TOP,anchor=tk.N, pady=10)

            self.store_button.pack(side=tk.LEFT, padx=10)
            self.get_button.pack(side=tk.LEFT, padx=10)
            self.listfiles_button.pack(side=tk.LEFT, padx=10)

            self.message_textbox.pack(side=tk.TOP, fill=tk.X, pady=10)
                
            self.input_field.pack(side=tk.LEFT,fill=tk.X, anchor=tk.W, pady=5)
            self.send_button.pack(side=tk.LEFT, padx=5, pady=5)
            self.help_button.pack(side=tk.LEFT, anchor=tk.E)

            registered = "Welcome " + self.handle.get() + "!"
            self.status_label.config(text=registered)

    # /leave
    def leave(self):
        answer = messagebox.askquestion("loh bat k aalis <//3", "Are you sure you want to quit?")
        if answer == "yes":
            self.client_socket.send("/leave".encode())
            self.root.destroy()
            
    
    def handle_leave(self):
        self.client_socket.close()
        self.receive_loop = False
        self.destroy()
    
    def reset_state(self):
        # Reset your application state here
        self.joined_server = False
        self.join_button_hidden = False
        self.server_address.set("")
        self.server_port.set("")
        self.destroy()
        file_sender_gui = FileSenderGUI()
        file_sender_gui.run()

    # displays msg
    def display_message(self, message):
        self.message_textbox.config(state=tk.NORMAL)  
        self.message_textbox.insert(tk.END, message + "\n") 
        self.message_textbox.config(state=tk.DISABLED)  

    # /dir function
    def req_dir_list(self):
        try:
            self.client_socket.send("/dir".encode())
        except socket.error:
            pass
    
    def handle_dir(self, msg):
        result = msg[len("/dir "):].lstrip()
        try:
            self.display_message("____________________________\n")
            self.display_message(result)
            self.display_message("____________________________\n")
        except socket.error:
            pass

    
    # displays msg with timestamp
    def displaymsg_withtime(self, msg):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        finalmsg = "<" + timestamp + "> " + self.handle.get() + ": " + msg
        self.display_message(finalmsg)
    
    # /get
    def open_download_window(self):
        self.client_socket.send("/get".encode())

    def handle_get(self, msg):
        self.download_window = tk.Toplevel(self.root)
        self.download_window.title("Download File")

        result = msg[len("/get "):].lstrip()
        msgbox = ScrolledText(self.download_window, state=tk.DISABLED)
        msgbox.config(state=tk.NORMAL)
        msgbox.insert(tk.END, result + '\n')
        msgbox.config(state=tk.DISABLED)
        msgbox.pack()

        filename_label = tk.Label(self.download_window, text="Enter File Name:")
        filename_label.pack()
    
        filename_entry = tk.Entry(self.download_window, width=50)
        filename_entry.pack()

        download_button = tk.Button(self.download_window, text="Download", command=lambda: download_file(filename_entry.get()))
        download_button.pack()

        def clientFilePathMaker(filename):
            current_directory = os.getcwd()
            folder_name = 'User Downloaded Files'
            folder_path = os.path.join(current_directory, folder_name)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path)

            base_name, extension = os.path.splitext(filename)
            finalname = base_name + "_DL" + extension
            file_path = os.path.join(folder_path, finalname)
            
            return file_path
        
        # function to handle the file download
        def download_file(filename):
            self.client_socket.send(f"/get {filename}".encode())
            try:
                file_path = clientFilePathMaker(filename)
                file = open(file_path, "wb")
                file_bytes = b""
                self.client_socket.send(filename.encode())
                file_size = int(self.client_socket.recv(1024).decode())
                done = False

                if file_size > 0:
                    while not done:
                        file_content = self.client_socket.recv(file_size)
                        if not file_content:
                            done = True
                            break
                        file_bytes += file_content
                        if len(file_bytes) >= file_size:
                            done = True
                    
                    file.write(file_content)
                
                else:
                    messagebox.showerror("loh", "File does not exist. Please try again.")

                msgbox.config(state=tk.NORMAL)
                msgbox.insert(tk.END, f"File received from Server: {filename}" + '\n')
                msgbox.config(state=tk.DISABLED)
                msgbox.pack()

            except Exception as e:
                msgbox.config(state=tk.NORMAL)
                msgbox.insert(tk.END, f"{filename} does not exist. Please try again. " + '\n')
                msgbox.config(state=tk.DISABLED)
                msgbox.pack()


    # /store
    def send_file(self):
        self.client_socket.send("/store".encode())
        time.sleep(0.1)
        file_name = filedialog.askopenfilename(title="Select a file")
        if file_name:
            file_size = os.path.getsize(file_name)
            
            timestamp = datetime.now().strftime("%y-%m-%d_%H%M%S")
            base_name = os.path.basename(file_name)
            result = os.path.splitext(base_name)[0] + "_" + timestamp + os.path.splitext(base_name)[1]
            
            self.client_socket.send(f"{result}<DELIMITER>{file_size}".encode())

            with open(file_name, "rb") as file:
                data = file.read()
                self.client_socket.sendall(data)
            
            # self.displaymsg_withtime(f"Uploaded {base_name}")
            self.status_label.config(text="File sent successfully!")
        
    def receive_messages(self):
        self.client_socket.settimeout(30)
        try:
            while self.receive_loop:
                message = self.client_socket.recv(1024).decode('utf-8')
                print(message.split()[0])
                if message.split()[0]=="/broadcast":
                    self.displaymsg_withtime(message[len("/broadcast /broadcast"):])
                elif message.startswith("/unicast"):
                    self.handle_unicast(message[len("/unicast "):])
                elif message.split()[0]== "/broadcastactions":
                    self.display_message(message[len("/broadcastactions "):])
                elif message.startswith("/join"):
                    self.handle_join()
                elif message.startswith("/dir"):
                    # Handle "/dir" message
                    self.handle_dir(message)
                elif message.startswith("/get"):
                    # Handle "/get" message
                    self.handle_get(message)
                elif message.startswith("/store"):
                    # Handle "/store" message
                    self.handle_store_message(message)
                elif message.startswith("/register"):
                    # Handle "/register" message
                    self.handle_register(message)
        except Exception as e:
            print(e)
        finally:
            self.client_socket.close()
            print("Connection closed.")

        

    def run(self):
        if self.join_button_hidden:
            self.join_button.pack_forget()
            
            
        self.root.mainloop()
        

file_sender_gui = FileSenderGUI()
file_sender_gui.run()

