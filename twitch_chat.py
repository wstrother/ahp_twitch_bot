from socket import socket


class TwitchChat:
    HOST = "irc.twitch.tv"
    PORT = 6667
    CHAT_BUFFER_SIZE = 1000
    RECV_BUFFER_SIZE = 1024

    def __init__(self, user_name, token_file, channel, bot=None):
        self.user_name = user_name
        self.token_file = token_file
        self.channel = channel
        self.bot = bot
        self.socket = self.get_socket()
        self.chat_buffer = []

    @property
    def chat_text(self):
        return "\n".join(self.chat_buffer)

    @classmethod
    def set_chat_buffer(cls, n):
        cls.CHAT_BUFFER_SIZE = n

    @classmethod
    def set_recv_buffer(cls, n):
        cls.RECV_BUFFER_SIZE = n

    @classmethod
    def get_socket(cls):
        s = socket()
        s.connect((
            cls.HOST,
            cls.PORT
        ))

        return s

    def get_password(self):
        file = open(self.token_file, "r")
        token = file.read()
        file.close()

        return token

    def send(self, msg):
        msg += "\r\n"
        self.socket.send(
            msg.encode("utf-8")
        )

    def send_chat(self, msg):
        self.send("PRIVMSG {} :{}".format(
            self.channel, msg
        ))
        self.print_chat_message(self.user_name, msg)

    def join_chat(self, join_msg=None):
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
        lines = self.chat_buffer

        chat_text = self.socket.recv(
            self.RECV_BUFFER_SIZE
        ).decode("utf-8").split("\r\n")[:-1]

        for line in chat_text:
            if not self.check_for_ping(line):
                self.print_line(line)

            lines.append(line)
            if len(lines) >= self.CHAT_BUFFER_SIZE:
                lines.pop(0)

    def check_for_ping(self, line):
        ping = line == "PING :tmi.twitch.tv"
        if ping:
            self.send(line.replace("PING", "PONG"))
            print("\t PING'd by the server!")

        return ping

    def print_line(self, line):
        if "PRIVMSG" not in line:
            print(line)

        else:
            user = line.split("!")[0][1:]
            delimiter = "PRIVMSG {} :".format(self.channel)
            line = line.split(delimiter)
            msg = delimiter.join(line[1:])
            self.handle_message(user, msg)

    @staticmethod
    def print_chat_message(user, msg):
        msg = msg.replace("\r", "")
        print("{:>25}: {}".format(user, msg))

    def handle_message(self, user, msg):
        self.print_chat_message(user, msg)

        if self.bot:
            self.bot.handle_message(user, msg)


if __name__ == "__main__":
    chat = TwitchChat(
        "your_bot_name",
        "oauth.token",
        "#your_twitch_name"
    )

    chat.join_chat()

    while True:
        chat.update_chat()

