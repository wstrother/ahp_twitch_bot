from twitch_chat import TwitchChat
import listeners
import commands

import json
import inspect


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

    def set_commands(self, *coms):
        for c in coms:
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


class BotLoader:
    def __init__(self, file_name, bot_class, user_name, token_file, *args):
        self.bot = self.make_bot(bot_class, user_name, token_file, *args)

        file = open(file_name, "r")
        self.json = json.load(file)
        file.close()

        self.class_dict = {
            c[0]: c[1] for c in inspect.getmembers(commands) if inspect.isclass(c[1])
        }
        self.class_dict.update({
            c[0]: c[1] for c in inspect.getmembers(listeners) if inspect.isclass(c[1])
        })

    @staticmethod
    def load_bot(json_file, bot_class, user_name, token_file, *args):
        loader = BotLoader(
            json_file, bot_class, user_name, token_file, *args
        )
        loader.add_approved_users()
        loader.set_commands()

        return loader.bot

    @staticmethod
    def make_bot(bot_class, user_name, token_file, *args):
        return bot_class(user_name, token_file, *args)

    def add_approved_users(self):
        self.bot.approved_users += self.json["approved_users"]

    def get_class(self, key):
        if type(key) in (tuple, list):
            return [self.get_class(i) for i in key]

        else:
            cd = self.class_dict
            if key in cd:
                return cd[key]

            else:
                aliases = self.json["classes"]
                if key in aliases:
                    return cd[aliases[key]]

                else:
                    return key

    def get_command(self, restricted, entry):
        cls, *args = entry
        cls = self.get_class(cls)

        if type(cls) is str:
            raise ValueError("Key or Class name '{}' not found".format(cls))

        new = []
        for arg in args:
            arg = self.get_class(arg)

            new.append(arg)

        name, *args = new

        return tuple([cls, name, restricted] + args)

    def set_commands(self):
        entries = []

        for entry in self.json["restricted"]:
            entries.append(
                self.get_command(True, entry)
            )

        for entry in self.json["public"]:
            entries.append(
                self.get_command(False, entry)
            )

        self.bot.set_commands(*entries)


if __name__ == "__main__":
    USER_NAME = "ahp_helper_bot"
    CHANNEL = "#athenshorseparty420"
    TOKEN = "oauth.token"

    BotLoader.load_bot(
        "bot_settings.json", TwitchBot, USER_NAME, TOKEN
    ).run(CHANNEL, "Logging on...")
