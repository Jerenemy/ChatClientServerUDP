# YEHOR MISHCHYRIAK (debugged by JEREMY ZAY)

'''
File containing utility functions necessary for the work of chat_server and chat_client
'''

import socket
from enum import Enum

'''
CONSTANTS
'''

class State(Enum):
    CONNECTING = 0 # client
    TRANSMITTING = 1 # client / server
    DISCONNECTING = 2 # client
    ACKNOWLEDGING = 3 # server

_HEADER_START = '{'  # Start of header
_HEADER_FIELDS_DELIMITER = '|'  # Delimiter between header fields
_HEADER_END = '}'  # End of header
_PAYLOAD_SEPARATOR = "~"  # Separator between header and payload

'''
UTILITY FUNCTIONS
'''

def header(state: State, sender_id: int, sender_nick_name: str, payload_size: int) -> str:
    """
    Constructs a header string with the provided information.

    Args:
        state (State): Current state.
        sender_id (int): The ID of the sender.
        sender_nick_name (str): The nickname of the sender.
        payload_size (int): The size of the payload.

    Returns:
        str: The constructed header string.
    """

    try:
        header_fields = _HEADER_FIELDS_DELIMITER.join(map(str, [state.value, sender_id, sender_nick_name, payload_size]))
        header = f"{_HEADER_START}{header_fields}{_HEADER_END}"
        header += "0" * (127-len(header)) + _PAYLOAD_SEPARATOR  # Padding the header to 128 characters
        return header
    except Exception as e:
        print(f"An unexpected error occurred in header function: {e}")
        return None
# print(header(State.CONNECTING, 2, "Yehor", 1245)) # test

def parse_message(message: str) -> tuple:
    """
    Parses the message string and extracts header and payload.

    Args:
        message (str): The message string containing header and payload.

    Returns:
        tuple: A tuple containing state, sender_id, sender_nick_name, payload_size, and payload.
    """

    try:
        message = message.decode("utf-8")
    except AttributeError:
        pass

    try:
        header_end = message.find(_HEADER_END)
        header = message[1:header_end]
        state, sender_id, sender_nick_name, payload_size = header.split(_HEADER_FIELDS_DELIMITER)
        payload_start = message.find(_PAYLOAD_SEPARATOR) + 1
        payload = message[payload_start:]
        return State(int(state)), int(sender_id), str(sender_nick_name), int(payload_size), str(payload)
    except Exception as e:
        print(f"An unexpected error occurred in parse_message function: {e}")
        return None
# print(parse_message(header(State.CONNECTING, 2, "Yehor", 1245)+"Hi, I am Yehor")) # test

'''
SOCKET HELPER FUNCTIONS
'''

class receive_data:
    """
    Callable class to receive data from a socket.

    Args:
        sock (socket): The socket object to receive data from.

    Returns:
        tuple: A tuple containing state, sender_id, sender_ip, sender_port, sender_nick_name, payload_size, and payload.
    """
    def __init__(self, sock: socket) -> None:
        self.sock = sock
        self.receiving = True

    def __call__(self, decode=True) -> None:
        try:
            while self.receiving:
                # data, addr_port = self.sock.recvfrom(128)  # read header
                data, addr_port = self.sock.recvfrom(1024)
                # print("received data: ", data)
                header_bin = data[:128]
                # print("header_bin: ", header_bin)
                state, sender_id, sender_nick_name, payload_size, _ = parse_message(header_bin)
                sender_ip, sender_port = addr_port
                # print(f"payload size = {payload_size}")
                payload = data[128:128+payload_size]
                # payload, _ = self.sock.recvfrom(payload_size)
                # print("received payload: ", payload)
                return (state, sender_id, sender_ip, sender_port, sender_nick_name, payload_size), payload.decode("utf-8") if decode else payload
        
        # except socket.error as e:
        #     print(f"Socket error occurred while receiving data: {e}")
        #     return None
        except Exception as e:
            if isinstance(e, socket.timeout):
                raise socket.timeout
            print(f"An unexpected error occurred while receiving data: {e}")
            return None
            
# SERVER END

def listening_socket(host: str, port: int):
    """
    Creates and binds a UDP listening socket to the specified host and port.

    Args:
        host (str): The host IP address or hostname to bind the socket to.
        port (int): The port number to bind the socket to.

    Returns:
        socket: The created UDP socket.
    """
    try:
        # Create a UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to the address and port
        udp_socket.bind((host, port))
        return udp_socket
    except socket.error as e:
        print(f"Error creating UDP listening socket: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred when attempting to create a listening socket: {e}")
        return None


class server_sender_function:
    """
    Callable class to send data from the server.

    Args:
        sock (socket): The socket object to send data from.
    """
    def __init__(self, sock: socket) -> None:
        self.sock = sock
    
    def __call__(self, state, sender_id, sender_nick_name, dest_ip, dest_port, message, encode=True) -> None:
        """
        Sends data from the server to the specified destination.

        Args:
            state (State): Current state.
            sender_id (int): The ID of the sender.
            sender_nick_name (str): The nickname of the sender.
            dest_ip (str): The IP address of the destination.
            dest_port (int): The port number of the destination.
            message (str): The message to send.
            encode (bool): Flag indicating whether to encode the message.

        Returns:
            None
        """
        try:
            payload = message
            payload_size = len(message)
            header_bin = header(state, sender_id, sender_nick_name, payload_size).encode("utf-8")
            if encode:
                message_bin = header_bin + payload.encode("utf-8")
            else:
                message_bin = header_bin + payload

            self.sock.sendto(message_bin, (dest_ip, dest_port))
        except socket.error as e:
            print(f"Socket error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while transmitting the data from the server: {e}")

# CLIENT END

def transmitting_socket():
    """
    Creates a UDP transmitting socket.

    Returns:
        socket: The created UDP socket.
    """
    try:
        # Create a UDP socket
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        return udp_socket
    except socket.error as e:
        print(f"Error creating UDP transmitting socket: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred when attempting to create a transmitting socket: {e}")


class client_sender_function:
    """
    Callable class to send data from the client.

    Args:
        sock (socket): The socket object to send data from.
        sender_id (int): The ID of the sender.
        sender_nick_name (str): The nickname of the sender.
        dest_ip (str): The IP address of the destination.
        dest_port (int): The port number of the destination.
    """
    def __init__(self, sock: socket, sender_id: int, sender_nick_name: str, dest_ip: str, dest_port: int) -> None:
        self.sock = sock
        self.sender_id = sender_id
        self.sender_nick_name = sender_nick_name
        self.dest_ip = dest_ip
        self.dest_port = dest_port
    
    def set_id(self, new_id):
        self.id = new_id

    def __call__(self, state, message, encode=True) -> None:
        """
        Sends data from the client to the specified destination.

        Args:
            message (str): The message to send.
            state (State): Current state.
            ack (bool): Acknowledgement flag.
            encode (bool): Flag indicating whether to encode the message.

        Returns:
            None
        """
        try:
            payload = message
            payload_size = len(message)
            header_str = header(state, self.sender_id, self.sender_nick_name, payload_size)
            header_bin = header_str.encode("utf-8")
            if encode:
                message_bin = header_bin + payload.encode("utf-8")
            else:
                message_bin = header_bin + payload
            # print(f"sending payload: {payload} with header: {header_str} with state: {state}\nbin_msg: ")
            # print(message_bin)
            
            self.sock.sendto(message_bin, (self.dest_ip, self.dest_port))
        except socket.error as e:
            print(f"Socket error occurred: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while transmitting the data from the client: {e}")
