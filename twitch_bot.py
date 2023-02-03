from twitch_chat import TwitchChat
import commands
import json
import inspect
import requests
from typing import Type

"""
    The twitch_bot.py module defines a TwitchBot class that manages a set of
commands, listeners, and approved users that can use certain restricted
commands. The bot should have a valid Twitch account associated with it and
will need an oauth token associated with that account to log into chat
channels on the Twitch IRC server.

    The bot account should typically be given mod powers in the chat room it
is to be used in, to prevent the server from timing out from sending too many
messages too close together.

    The BotLoader class is also defined, which defines a JSON data interface
that allows for the programmatic creation of Command and Listener objects,
defined in the commands.py, and listeners.py modules respectively. The JSON
file provided can also provide a list of approved users who have access to
additional restricted bot commands.
"""


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

        self._output_buffer = []
        self._buffer_flag = False

        self.approved_users = []
        self.commands = {}
        self.state = {}
    
    def __enter__(self):
        return self

    def __exit__(self, *args):
        if self.chat:
            self.send_chat("Goodbye!")
        
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

    def set_output_buffer(self):
        self._buffer_flag = True
    
    def get_output_buffer(self):
        self._buffer_flag = False

        return self._output_buffer

    def send_chat(self, message):
        """
        Sends a message to the Twitch chat
        :param message: str, message for chat
        """
        if not self._buffer_flag:
            self.chat.send_chat(message)
        else:
            self._output_buffer = message.split(" ")

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

    def user_approved(self, command, user):
        authorized = user.upper() in [u.upper() for u in self.approved_users]

        return authorized if command.restricted else True

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

        ## dev breakpoint
        if command == "bp" and user == "athenshorseparty_":
            print("breakpoint")
            breakpoint()
        
        command = self.commands.get(command)

        if command and self.user_approved(command, user):
            command.do(user, *args)

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

    def set_state_variable(self, key, value, log=False):
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
    RESTRICTED = "restricted"           # restricted commands
    PUBLIC = "public"                   # unrestricted commands
    STATE = "state"                     # state variables

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

        if classes:
            self.class_dict.update({
                c.__name__: c for c in classes
            })

    @property
    def approved_users(self):
        return self.json[self.__class__.APPROVED_USERS]

    @property
    def restricted_commands(self):
        return self.json[self.__class__.RESTRICTED]

    @property
    def public_commands(self):
        return self.json[self.__class__.PUBLIC]

    @property
    def state(self):
        return self.json[self.__class__.STATE]

    @classmethod
    def load_bot(cls, json_file: str, bot_class: Type[TwitchBot], bot_args: tuple, classes:None|dict=None) -> Type[TwitchBot]:
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

        bot.approved_users += loader.approved_users
        bot.state = loader.state

        loader.set_commands(bot)

        return bot

    def get_class(self, key):
        """
        This method helps recursively substitute JSON data values
        with Class objects if they match the name of any Class
        objects found in the 'class_dict'
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

    def set_commands(self, bot: TwitchBot):
        """
        Iterates over the data entries specified within the 'restricted'
        and 'public' lists in the JSON data and generates a list of argument
        tuples to be passed to the bot object's 'set_commands()' method
        :param bot: bot object to have commands set
        """
        entries = []

        for entry in self.restricted_commands:
            entries.append(
                self.get_command(True, entry)
            )

        for entry in self.public_commands:
            entries.append(
                self.get_command(False, entry)
            )

        bot.set_commands(*entries)