from twitch_chat import TwitchChat
import listeners as listeners
import commands as commands

import json
import inspect
import requests

#   The twitch_bot.py module defines a TwitchBot class that manages a set of
# commands, listeners, and approved users that can use certain restricted
# commands. The bot should have a valid Twitch account associated with it and
# will need an oauth token associated with that account to log into chat
# channels on the Twitch IRC server.
#   The bot account should typically be given mod powers in the chat room it
# is to be used in, to prevent the server from timing out from sending too many
# messages too close together.

#   The BotLoader class is also defined, which defines a JSON data interface
# that allows for the programmatic creation of Command and Listener objects,
# defined in the commands.py, and listeners.py modules respectively. The JSON
# file provided can also provide a list of approved users who have access to
# additional restricted bot commands.


class TwitchBot:
    def __init__(self, user_name, token_file):
        """
        Creates an object representing a TwitchBot that allows for various
        commands as well as listener routines that respond to certain trigger
        strings within the chat. Also contains a list of user names for approved
        users who can use special restricted commands
        :param user_name: str, user name of a valid Twitch account
        :param token_file: str, file name cotaining a valid oauth
            token for that account
        """
        self.user_name = user_name
        self.token_file = token_file
        self.chat = None

        self.approved_users = []
        self.commands = {}
        self.state = {}
        self.listeners = []

    def run(self, channel, join_msg):
        """
        Method creates a TwitchChat object to establish a connection
        to the Twitch IRC server and then joins a specific channel,
        representing the Twitch chat room of a specific user
        Upon successfully connecting to the server and joining the
        channel, this method runs a loop of the TwitchChat.update_chat()
        method, which in turn passes messages from the chat to the
        TwitchBot's 'handle_message()' method
        :param channel: str, name of the Twitch chat to join
        :param join_msg: str, optional chat messsage to send after
            successfully joining the chat room
        """
        host_name = channel[1:]
        self.approved_users.append(host_name)
        self.approved_users.append(self.user_name)

        self.chat = TwitchChat(
            self.user_name,
            self.token_file,
            channel,
            bot=self
        ).join_chat(join_msg)

        while True:
            try:
                self.chat.update_chat()

            except BaseException as e:
                msg = "Runtime error occurred '{}: {}'".format(
                    e.__class__.__name__, e)
                self.send_chat(msg)

                raise e

    def send_chat(self, message):
        """
        Sends a message to the Twitch chat
        :param message: str, message for chat
        """
        self.chat.send_chat(message)

    def handle_message(self, user, msg):
        """
        Parses messages sent to the chat to detect commands
        and pass to any active chat listeners.
        :param user: str, name of user who sent message
        :param msg: str, message sent to chat
        """
        msg = msg.replace("\r", "")
        msg = msg.replace("\n", "")

        if msg[0] == "!":
            msg = msg.split(" ")
            command = msg[0][1:]
            args = msg[1:]

            self.do_command(command, user, *args)

        else:
            for listener in self.listeners:
                listener.hear_message(user, msg)

    def do_command(self, command, user, *args):
        """
        Checks for command name in commands dict and passes
        the user and args to the 'do' method of the associated
        command object
        :param command: str, command name
        :param user: str, name of user that used command
        :param args: tuple(str, str...), generic arguments exploded by
            space characters chat message after the command "!name" str
        """
        if command in self.commands:
            self.commands[command].do(user, *args)

    def add_command(self, cls, *args):
        """
        Instantiates a command object from a class and args then
        adds that command to the commands dict under the key of
        the command.name attribute
        :param cls: Command class or subclass
        :param args: initialization args for Command class
        """
        command = cls(self, *args)
        self.commands[command.name] = command

    def set_commands(self, *coms):
        """
        This method takes an arbitrary amount of argument entries,
        each taking the form of some iterable to be passed as
        arguments to 'add_command()'
            (Command class or subclass, *args)
        :param coms: sets of arguments for 'add_command'
            method.
        """
        for c in coms:
            self.add_command(*c)

    def get_state(self, key):
        if key not in self.state:
            self.state[key] = ""

        return self.state[key]

    def set_state(self, key, value, log=False):
        """
        Alters the 'state' dict to store a variable
        :param key: str, name of the state variable
        :param value: any value to be stored as variable
        :param log: bool, determines if a log message should
            be sent to the Twitch chat
        """
        self.state[key] = value
        if log:
            self.send_chat("variable '{}' set to '{}'".format(
                key, value
            ))

    def get_state_variable(self, key):
        """
        Returns the value of some state variable stored
        in 'state' dict under the 'key' name
        :param key: str, name of state variable
        :return: value of the state variable, or None
        """
        return self.state.get(key)

    def add_listener(self, listener):
        """
        Adds some chat listener to TwitchBot's list of active
        listeners if that listener hasn't already been added.
        Prints a log message to the console when listener is added
        :param listener: Listener object
        """
        if listener not in self.listeners:
            self.listeners.append(listener)

            print("\nadded listener \n\tuser: {}\n\ttrigger: {}\n".format(
                listener.user, listener.trigger
            ))

    def remove_listener(self, listener):
        """
        Removes listener from TwitchBot's list of active listeners
        :param listener: Listener object
        """
        if listener in self.listeners:
            self.listeners.pop(
                self.listeners.index(listener)
            )

    @staticmethod
    def post_to_api(command_name, url, msg):
        try:
            data = json.loads(msg)
        except ValueError:
            print("bad data passed to {}: \n{}".format(
                command_name, msg
            ))
            return False

        p = None
        response = "\nRESPONSE FROM SERVER:\n {}"

        try:
            p = requests.post(
                url, data=data, headers={'Content-type': 'application/json'}
            )
        except requests.ConnectionError:
            error = "API POST request to {} failed to connect to server".format(url)
            print(response.format(error))

        if p:
            print(response.format(p.text))


class BotLoader:
    # key names for JSON data
    APPROVED_USERS = "approved_users"   # users with access to restricted commands
    CLASSES = "classes"                 # class name aliases
    RESTRICTED = "restricted"           # restricted commands
    PUBLIC = "public"                   # unrestricted commands

    def __init__(self, json_file, classes=None):
        """
        Creates a loader class the provides an interface to set a Twitch bot's
        attributes, commands, and listeners based on JSON data
        :param json_file: str, file_name for JSON data
        :param classes: list, any additional subclasses needed
        """
        file = open(json_file, "r")
        self.json = json.load(file)
        file.close()

        self.class_dict = {
            c[0]: c[1] for c in inspect.getmembers(commands) if inspect.isclass(c[1])
        }
        self.class_dict.update({
            c[0]: c[1] for c in inspect.getmembers(listeners) if inspect.isclass(c[1])
        })

        if classes:
            self.class_dict.update({
                c.__name__: c for c in classes
            })

    @classmethod
    def load_bot(cls, json_file, bot_class, bot_args, classes=None):
        """
        Method that creates a BotLoader object and instantiates
        a bot object from the 'bot_class' passed.
        The loader then sets attributes and
        :param json_file: str, file_name passed to __init__
        :param bot_class: TwitchBot or subclass used to instantiate bot
        :param bot_args: iterable of args passed to bot_class.__init__
        :param classes: list, additional classes passed to __init__
        :return: bot object with attributes, commands, listeners set
            according to JSON data
        """
        loader = cls(
            json_file, classes=classes
        )

        bot = bot_class(*bot_args)
        loader.set_attributes(bot)
        loader.set_commands(bot)

        return bot

    def set_attributes(self, bot):
        """
        This method provides a subclass hook that defines the routine for
        what bot attributes should be set using the JSON data
        :param bot: bot object to have attributes set
        """
        self.add_approved_users(bot)

    def add_approved_users(self, bot):
        """
        Adds user names for approved users to the bot object
        :param bot: bot object to have approved_users set
        """
        bot.approved_users += self.json[
            self.__class__.APPROVED_USERS
        ]

    def get_class(self, key):
        """
        This method helps recursively substitute JSON data values
        with Class objects if they match the name of any Class
        objects found in the 'class_dict' or aliases thereof as
        defined within the JSON data
        :param key: str, potential class name or alias
        :return: Class, if key corresponds to a Class or
                 str, if key does not
        """
        if type(key) in (tuple, list):
            return [self.get_class(i) for i in key]

        elif type(key) is dict:
            return {k: self.get_class(key[k]) for k in key}

        else:
            cd = self.class_dict
            if key in cd:
                return cd[key]

            else:
                aliases = self.json[
                    self.__class__.CLASSES
                ]

                if key in aliases:
                    return cd[aliases[key]]

                else:
                    return key

    def get_command(self, restricted, entry):
        """
        This method takes a single 'entry' from either the 'public' or
        'restricted' list as defined in the JSON data and parses it for
        Class names and Class name aliases, substituting the associated
        Class objects and returning a tuple that can be used as arguments
        for the 'set_commands()' method
        :param restricted: bool, passed to the Command object
            on initialization
        :param entry: tuple, generic args passed to the Command
            object on initialization
        :return: tuple, args to be passed to the bot object through
            the 'set_commands()' method
        """
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

    def set_commands(self, bot):
        """
        Iterates over the data entries specified within the 'restricted'
        and 'public' lists in the JSON data and generates a list of argument
        tuples to be passed to the bot object's 'set_commands()' method
        :param bot: bot object to have commands set
        """
        entries = []

        for entry in self.json[
            self.__class__.RESTRICTED
        ]:
            entries.append(
                self.get_command(True, entry)
            )

        for entry in self.json[
            self.__class__.PUBLIC
        ]:
            entries.append(
                self.get_command(False, entry)
            )

        bot.set_commands(*entries)