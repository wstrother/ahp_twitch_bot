from commands import EchoCommand, AliasCommand, SequenceCommand
from twitch_chat import TwitchChat


class TwitchBot:
    def __init__(self, user_name, token_file):
        self.user_name = user_name
        self.token_file = token_file
        self.chat = None

        self.approved_users = []
        self.commands = {}

    def run(self, channel, join_msg):
        host_name = channel[1:]
        self.approved_users.append(host_name)

        self.chat = TwitchChat(
            self.user_name,
            self.token_file,
            channel,
            bot=self
        ).join_chat(join_msg)

        while True:
            self.chat.update_chat()

    def send_chat(self, message):
        self.chat.send_chat(message)

    def handle_message(self, user, msg):
        msg = msg.replace("\r", "")

        if msg[0] == "!":
            msg = msg.split(" ")
            command = msg[0][1:]
            args = msg[1:]

            self.do_command(command, user, *args)

    def do_command(self, command, user, *args):
        if command in self.commands:
            self.commands[command].do(user, *args)

    def add_command(self, cls, *args):
        command = cls(self, *args)
        self.commands[command.name] = command

    def set_commands(self, *commands):
        for c in commands:
            self.add_command(*c)

    def get_users_from_file(self, file_name):
        file = open(file_name, "r")
        self.approved_users += [
            l for l in file.readlines() if l
        ]
        file.close()


if __name__ == "__main__":
    ahp_bot = TwitchBot("ahp_helper_bot", "oauth.token")
    ahp_bot.get_users_from_file("users.txt")

    ahp_bot.set_commands(
        (EchoCommand, "st", True, "title"),
        (EchoCommand, "sg", True, "game"),
        (AliasCommand, "pkmn", True, "sg", "Pokémon Ruby/Sapphire"),
        (SequenceCommand, "ssb_speedrun", True,
            (AliasCommand, "st", "Super Smash Bros Speedruns"),
            (AliasCommand, "sg", "Super Smash Bros.")
         )
    )

    ahp_bot.run("#athenshorseparty420", "Hello there")
