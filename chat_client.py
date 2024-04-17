# JEREMY ZAY

'''
COMP 332
Chat server
Usage:
    python3 chat_client.py <host> <port> <name>
'''

import util
import socket
import sys
from inputimeout import inputimeout, TimeoutOccurred


class ChatClient:
    """
    A chat client to connect to a server, send, and receive messages.
    """
    def __init__(self, server_ip: str, server_port: int, nick_name: str):
        """
        Initializes a new ChatClient instance with the server IP, port, and user's nickname.
        
        Args:
            server_ip (str): IP address of the server.
            server_port (int): Port number of the server.
            nick_name (str): Nickname of the user.
        """
        self.server_ip = server_ip
        self.server_port = server_port
        self.nick_name = nick_name
        self.sender_id = None  # To be assigned upon connection
        self.client_sending_window = 8 # Timeout window for sending messages
        self.server_receiving_window = 2.0 # Timeout window for receiving messages
        self.start()
        
    def start(self) -> None:
        """
        Initializes the client's socket and begins the send/receive process.
        """
        self.sock = util.transmitting_socket()
        
        if not self.sock:
            print("Could not create a socket")
            exit(1)
            
        self.send = util.client_sender_function(self.sock, -1, self.nick_name, self.server_ip, self.server_port)
        self.receive = util.receive_data(self.sock)
        
        self.sock.settimeout(self.server_receiving_window)
        self.write_and_receive()


    def write_and_receive(self) -> None:
        """
        Handles the main loop for connecting, writing, and receiving messages.
        """
        try:
            self.connect()

            running = True
            while running: 
                self.write_window() 
                self.receive_window()
        except (StopIteration, KeyboardInterrupt, Exception) as e:
            print(f"User {self.nick_name} disconnected: {e}")
            self.disconnect()
            
    
    def write_window(self) -> None:
        """
        Manages user input for sending messages with a timeout.
        """
        try:
            msg = inputimeout(prompt='', timeout=self.client_sending_window)
            if msg == "q":
                raise StopIteration
            self.transmit(msg)
        except TimeoutOccurred:
            pass

    
    def receive_window(self) -> None:
        """
        Listens for incoming messages from the server.
        """
        try:
            while True:
                meta_data, payload = self.receive()
                state, _, _, _, _, _ = meta_data
                if state == util.State.TRANSMITTING:
                    ChatClient.display_msg(payload)
        except socket.timeout:
            pass

    
    def receive_id(self) -> None:
        """
        Receives a unique ID from the server upon connecting.
        """
        meta_data, _ = self.receive()
        _, sender_id, _, _, _, _ = meta_data
        self.sender_id = sender_id
        self.send.sender_id = sender_id

    
    def ack(self) -> bool:
        """
        Receives acknowledgement from the server.
        
        Returns:
            bool: True if ACK received, False otherwise.
        """
        try:
            meta_data, _ = self.receive()
            state, _, _, _, _, _ = meta_data
            if state == util.State.ACKNOWLEDGING:
                return True
            print("Received non-ACK message while waiting for ACK")
            # ChatClient.display_msg(payload)
            return False # resend to re-initialize socket timeout
        except socket.timeout:
            print("ACK timed out: packet lost")
            return False
            

    def send_generic(self, state: util.State, msg: str) -> None:
        """
        Sends a message with the specified state and handles acknowledgements.
        
        Args:
            state (util.State): The state to send the message in.
            msg (str): The message to send.
        """
        while True:
            self.send(state, msg)
            if self.ack():
                # if received ack in time, break, else retransmit.
                break
                
            
    
    def connect(self) -> None:
        """
        Connects to the server.
        """
        self.send_generic(util.State.CONNECTING, "")
        self.receive_id()

    
    def transmit(self, msg: str) -> None:
        """
        Transmits a message to the server.
        
        Args:
            msg (str): The message to transmit.
        """
        self.send_generic(util.State.TRANSMITTING, msg)

        
    def disconnect(self) -> None:
        """
        Disconnects from the server.
        """
        self.send_generic(util.State.DISCONNECTING, "")


    @staticmethod          
    def display_msg(msg: str) -> None:
        """
        Formats and prints a received message.
        
        Args:
            msg (str): The message to display.
        """
        formatted_msg = f"{msg}"
        print(formatted_msg)
        
 
def main():
    """
    Main function to handle command-line arguments and start the chat client.
    """
    print (sys.argv, len(sys.argv))
    chat_host = 'localhost'
    chat_port = 50008
    nick_name = 'Vicky'

    if len(sys.argv) > 1:
        chat_host = sys.argv[1]
        chat_port = int(sys.argv[2])
        nick_name = sys.argv[3]

    try:
        chat_client = ChatClient(chat_host, chat_port, nick_name)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()