from commands import EchoCommand, AliasCommand, SequenceCommand, OptionCommand, StateCommand, ListenerCommand
from listeners import TitleTagListener
from twitch_chat import TwitchChat


class TwitchBot:
    def __init__(self, user_name, token_file):
        self.user_name = user_name
        self.token_file = token_file
        self.chat = None

        self.approved_users = []
        self.commands = {}
        self.state = {}
        self.listeners = []

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

        else:
            for listener in self.listeners:
                listener.hear_message(user, msg)

    def do_command(self, command, user, *args):
        if command in self.commands:
            self.commands[command].do(user, *args)

    def add_command(self, cls, *args):
        command = cls(self, *args)
        self.commands[command.name] = command

    def set_commands(self, *commands):
        for c in commands:
            self.add_command(*c)

    def set_state(self, key, value):
        self.state[key] = value
        self.send_chat("variable '{}' set to '{}'".format(
            key, value
        ))

    def get_state_variable(self, key):
        return self.state.get(key)

    def add_listener(self, listener):
        if listener not in self.listeners:
            self.listeners.append(listener)

            print("\nadded listener \n\tuser: {}\n\ttrigger: {}\n".format(
                listener.user, listener.trigger
            ))

    def remove_listener(self, listener):
        if listener in self.listeners:
            self.listeners.pop(
                self.listeners.index(listener)
            )


if __name__ == "__main__":
    ahp_bot = TwitchBot("ahp_helper_bot", "oauth.token")

    ahp_bot.set_commands(
        (EchoCommand, "st", True, "title"),
        (EchoCommand, "sg", True, "game"),
        (AliasCommand, "pkmn", True, "sg", "Pokémon Ruby/Sapphire"),
        (AliasCommand, "ssb", True, "sg", "Super Smash Bros."),
        (SequenceCommand, "ssb_speedrun", True,
            (AliasCommand, "st", "Super Smash Bros Speedruns"),
            "ssb"
         ),
        (SequenceCommand, "lttp_ms", True,
            ("st", "LTTP Master Sword Speedruns"),
            "pkmn"
         ),
        (OptionCommand, "speedrun", True,
            ("ssb", "ssb_speedrun"),
            ("ms", "lttp_ms"),
            ("joke", "st", "It's a joke title...")
         ),
        (StateCommand, "tag", True, "title_tag"),
        (ListenerCommand, "set_tag", True, (
            TitleTagListener, "The stream title has been updated to:", "nightbot"
        )),
        (SequenceCommand, "tag_seq", True,
            "tag",
            "set_tag"
         )
    )

    ahp_bot.run("#athenshorseparty420", "Hello there")
