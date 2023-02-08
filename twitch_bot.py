from twitch_chat import TwitchChat
import traceback

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
        
    def run(self, channel, join_msg, output=None):
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
            bot=self,
            output=output
        ).join_chat(join_msg)

        while True:
            try:
                self.chat.update_chat()

            except BaseException as e:
                msg = "Runtime error occurred '{}: {}'".format(
                    e.__class__.__name__, e)
                self.send_chat(msg)
                print(traceback.format_exc())

    def set_output_buffer(self):
        self._buffer_flag = True
    
    def get_output_buffer(self):
        self._buffer_flag = False

        return self._output_buffer

    def send_chat(self, msg:str|object):
        """
        Sends a message to the Twitch chat
        :param message: str, message for chat
        """
        if not self._buffer_flag:
            # str conversion
            if type(msg) is not str:
                msg = str(msg)
            
            if len(msg) > 500:
                msg = msg[:496] + "..."

            self.chat.send_chat(msg)

        else:
            # if buffer flag set, store unconverted object
            self._output_buffer = msg

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
            msg = " ".join(msg[1:])

            self.do_command(command, user, msg)

    def user_approved(self, command, user):
        authorized = user.upper() in [u.upper() for u in self.approved_users]

        return authorized if command.restricted else True

    def do_command(self, command, user, msg):
        """
        Checks for command name in commands dict and passes
        the user and args to the 'do' method of the associated
        command object
        :param command: str, command name
        :param user: str, name of user that used command
        :param args: tuple(str, str...), generic arguments exploded by
            space characters chat message after the command "!name" str
        """

        ##      REMOVE LATER!
        ## dev breakpoint
        if command == "bp" and user == "athenshorseparty_":
            breakpoint()
        
        if type(command) is str:
            command = self.commands.get(command)

        if command and self.user_approved(command, user):
            output = command.do(user, msg)
            if output is not None:
              self.send_chat(output)

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

    def set_state_variable(self, key, value, *sub_keys):
        """
        Alters the 'state' dict to store a variable
        :param key: str, name of the state variable
        :param value: any value to be stored as variable
        """
        state = self.state
        if sub_keys:
            state = state[key]
            for sk in sub_keys[:-1]:
                state = state[sk]
            key = sub_keys[-1]

        state[key] = value

    def get_state_variable(self, key):
        """
        Returns the value of some state variable stored
        in 'state' dict under the 'key' name
        :param key: str, name of state variable
        :return: value of the state variable, or None
        """
        return self.state.get(key)
