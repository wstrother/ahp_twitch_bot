from socket import socket

#   The twitch_chat.py module defines a class called TwitchChat that represents a
# persistent connection to a Twitch chat room, using the IRC protocol with the
# socket module. To connect to Twitch's IRC server you will need:
#       - A Twitch account
#       - A valid oauth token for that account
#           (available at tmi.twitch.com)
#       - The name of a valid Twitch channel
#   The TwitchChat class also accepts a "bot" object as an initialization argument
# which it sets as an attribute and passes chat messages to that bot via the
# 'handle_message(user, msg)' method.
#   The Twitch account should ideally have moderator privileges on the channel that
# it joins, to ensure that automated messages sent to the server don't get
# flagged as spam or abuse which may result in the connection being timed out


class TwitchChat:
    HOST = "irc.twitch.tv"
    PORT = 6667
    CHAT_BUFFER_SIZE = 1000
    RECV_BUFFER_SIZE = 1024

    def __init__(self, user_name, token_file, channel, bot=None):
        """
        Returns a TwitchChat object and initializes a connection to the
        'irc.twitch.tv' server via a socket object imported from the
        socket module.

        Messages from the server are stored as a list of string in the
        'chat_buffer' attribute, with an default max buffer size of
        1000 messages, to aid in debugging.

        :param user_name: str, the name of a valid Twitch account
        :param token_file: str, file name contain oauth token for the
            connecting Twitch account
        :param channel: str, the name of a valid Twitch channel on the
            irc server (should take the form '#channelname'
        :param bot: object, an instance of a TwitchBot or subclass,
            designed to handle and respond to messages from the chat
        """
        self.user_name = user_name
        self.token_file = token_file
        self.channel = channel
        self.bot = bot

        self.socket = self.get_socket()
        self.chat_buffer = []

    @property
    def chat_text(self):
        """
        Returns the full chat buffer as a string, to search for substrings
        within any messages received from the server.

        :return: str, a concatenation of the 'chat_buffer' attribute
        """
        return "\n".join(self.chat_buffer)

    @classmethod
    def set_chat_buffer(cls, n):
        """
        Used to set the size of the 'chat_buffer' list at run time

        :param n: int, new maximum buffer size
        """
        cls.CHAT_BUFFER_SIZE = n

    @classmethod
    def get_socket(cls):
        """
        Used to open a connection to the server

        :return: socket, socket module socket object with live
            connection to the Twitch IRC server
        """
        s = socket()
        s.connect((
            cls.HOST,
            cls.PORT
        ))

        return s

    def get_password(self):
        """
        Reads the contents of the oauth token file and returns
        as a string for logging onto the Twitch IRC server

        :return: str, the oauth token for authentication
        """
        file = open(self.token_file, "r")
        token = file.read()
        file.close()

        return token

    def send(self, msg):
        """
        Properly formats and encodes a message to be sent
        through the socket to the IRC server

        :param msg: str, message for server
        """
        msg += "\r\n"
        self.socket.send(
            msg.encode("utf-8")
        )

    def send_chat(self, msg):
        """
        Formats a message to be sent to the IRC server as a chat
        message for the channel that is currently joined, i.e.
        the Twitch chat

        :param msg: str, message to be sent to the IRC channel
        """
        self.send("PRIVMSG {} :{}".format(
            self.channel, msg
        ))
        self.print_chat_message(self.user_name, msg)

    def join_chat(self, join_msg=None):
        """
        Method called to join the specific channel on the IRC server
        that represents the Twitch chat that is being joined.
        Authenticates the user account and sends an optional join
        message to the chat.

        :param join_msg: str, optional message to be sent to
            the Twitch chat upon successfully joining the channel
        :return: TwitchChat object, returns copy of self
        """
        self.send("PASS " + self.get_password())
        self.send("NICK " + self.user_name)
        self.send("JOIN " + self.channel)

        joining = True
        while joining:
            self.update_chat()
            if "End of /NAMES list" in self.chat_text:
                joining = False

        if join_msg:
            self.send_chat(join_msg)

        return self

    def update_chat(self):
        """
        This method is called to check for new messages from the
        IRC server and parse each message, passing them one 'line'
        at a time to the 'handle_server_message(line)' method
        """
        chat_text = self.socket.recv(
            self.RECV_BUFFER_SIZE
        ).decode("utf-8").split("\r\n")[:-1]

        for line in chat_text:
            self.handle_server_message(line)
            self.update_buffer(line)

    def update_buffer(self, line):
        """
        Updates the 'chat_buffer' attribute and limits the size to
        the amount specified by CHAT_BUFFER_SIZE

        :param line: str, message from server to be added to buffer
        """
        self.chat_buffer.append(line)
        if len(self.chat_buffer) > self.CHAT_BUFFER_SIZE:
            self.chat_buffer.pop(0)

    def handle_server_message(self, line):
        """
        This method parses messages from the server and determines
        whether they're an actual IRC server message or chat messages
        for the specific channel.

        Server messages are checked to see whether they are a PING
        message so that the appropriate response can be sent to
        prevent the connection from being timed out. Otherwise they
        are simply printed to the console.

        Chat messages are parsed into a 'user' and 'msg' string and
        then passed to the method 'handle_chat_message(user, msg)'

        :param line: str, message from server to be parsed
        """
        if "PRIVMSG" not in line:
            ping = self.check_for_ping(line)
            if not ping:
                print(line)

        else:
            user = line.split("!")[0][1:]
            delimiter = "PRIVMSG {} :".format(self.channel)
            line = line.split(delimiter)
            msg = delimiter.join(line[1:])

            self.handle_chat_message(user, msg)

    def check_for_ping(self, line):
        """
        Checks a server message to determine if it contains a
        PING from the server, and then sends the appropriate
        response to prevent a connection timeout.

        :param line: str, message from the server
        :return: bool, True if a PING message has been
            received, otherwise False
        """
        ping = line == "PING :tmi.twitch.tv"
        if ping:
            self.send(line.replace("PING", "PONG"))
            print("\t PING'd by the server!")

        return ping

    def handle_chat_message(self, user, msg):
        """
        Passes the chat message to the 'print_chat_message'
        method for formatting as well as the 'bot' object's
        'handle_message()' method if one is set.

        :param user: str, name of user who sent the message
        :param msg: str, message sent to the chat
        """
        self.print_chat_message(user, msg)

        if self.bot:
            self.bot.handle_message(user, msg)

    @staticmethod
    def print_chat_message(user, msg):
        """
        Formats a chat message and prints to the console

        :param user: str, user name
        :param msg: str, message sent to chat
        """
        msg = msg.replace("\r", "")
        print("{:>25}: {}".format(user, msg))


if __name__ == "__main__":
    chat = TwitchChat(
        "ahp_helper_bot",
        "oauth.token",
        "#athenshorseparty420"
    )

    chat.join_chat("I have joined the chat!")

    while True:
        chat.update_chat()

