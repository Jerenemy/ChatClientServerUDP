# YEHOR MISHCHYRIAK

'''
COMP 332
Chat server
Usage:
    python3 chat_server.py <host> <port>
'''

import util
from random import random
from sys import exit, argv

class ChatServer:

    def __init__(self, server_host, server_port, pkt_loss_chance):
        # Simulating pkt loss: pkt_loss_chance value must be in the range from 0.0 to 1.0
        # the server will drop the each message it receives with the specified probability
        self.pkt_loss_chance = pkt_loss_chance

        self.server_host = server_host
        self.server_port = server_port
        self.running = True
        self.connected_users = dict()  # currently connected users
        self.chat_id = 0  # next user's ID

    def is_lost(self) -> bool:
        return random() < self.pkt_loss_chance

    def add_user(self, nick_name, user_ip, user_port) -> int:
        id = self.chat_id
        self.chat_id += 1
        self.connected_users[id] = (nick_name, user_ip, user_port)
        return id

    def delete_user(self, user_id):
        """
        Deletes a user from the connected users list.

        Args:
            user_id (int): The ID of the user to delete.

        Returns:
            None
        """
        try:
            del self.connected_users[user_id]
        except KeyError as e:
            print(f"Error: No user with ID {user_id} was found. Details: {e}")
        except Exception as e:
            print(f"An unexpected error occurred while deleting the user: {e}")

    def distribute_message(self, message, sender_id=-1, sender_nick_name=None) -> None:
        """
        Distributes a message to all connected users except the sender.

        Args:
            message (str): The message to distribute.
            sender_id (int, optional): The ID of the sender. Defaults to -1.
            sender_nick_name (str, optional): The nickname of the sender. Defaults to None.

        Returns:
            None
        """
        for user_id, info in self.connected_users.items():
            if user_id == sender_id:
                continue
            user_name, user_ip, user_port = info
            if not sender_nick_name and sender_id == -1:
                self.send(util.State.TRANSMITTING, user_id, user_name, user_ip, user_port, f"{message}")
            else: self.send(util.State.TRANSMITTING, user_id, user_name, user_ip, user_port, f"{sender_nick_name} ({sender_id}) says: \"{message}\"")

    def run_server(self):
        """
        Runs the chat server.

        Returns:
            None
        """
        # Initialize server socket on which to listen for connections
        self.sock = util.listening_socket(self.server_host, self.server_port)
        if not self.sock:
            exit(1)

        self.receive = util.receive_data(self.sock)
        self.send = util.server_sender_function(self.sock)

        try:
            while self.running: 
                # print("about to receive")
                meta_data, payload = self.receive()
                if self.is_lost(): # drop the message with the prior specified probability to simulate pkt loss
                    print("\nPACKET LOST\n")
                    continue
                # meta data is state, sender_id, sender_ip, sender_port, sender_nick_name, payload_size
                state, sender_id, sender_ip, sender_port, sender_nick_name, _ = meta_data
                # acknowledge having received the message
                print(f"Message recved from: {sender_id}, {state}\nMessage: {payload}\n")
                self.send(util.State.ACKNOWLEDGING, sender_id, sender_nick_name, sender_ip, sender_port, "")
                if state == util.State.CONNECTING:
                    user_id = self.add_user(sender_nick_name, sender_ip, sender_port) # add the user to the users dict
                    # self.send(util.State.TRANSMITTING, user_id, sender_nick_name, sender_ip, sender_port, "") # send them their ID
                    self.distribute_message(f"{sender_nick_name} ({user_id}) has connected to the server!")
                elif state == util.State.TRANSMITTING:
                    self.distribute_message(payload, sender_id, sender_nick_name)
                elif state == util.State.DISCONNECTING:
                    self.delete_user(sender_id)
                    self.distribute_message(f"{sender_nick_name}({user_id}) has disconnected from the server!")

        except KeyboardInterrupt:
            print("\nStopping the server")
            self.running = False
            self.sock.close()
            exit(0)

        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self.running = False
            self.sock.close()
            exit(1)

def main():
    server_host = 'localhost'
    server_port = 50008
    if len(argv) > 1:
        server_host = argv[1]
        server_port = int(argv[2])

    chat_server = ChatServer(server_host, server_port, 0.1)
    chat_server.run_server()

if __name__ == '__main__':
    main()
