import json
from typing import Type
from twitch_bot import TwitchBot

"""  
    The commands.py module defines a Command class and collection of
subclasses that provide various functions for the TwitchBot class
that can be invoked through the Twitch chat. Commands are invoked
through chat messages that have the form:
      "![command_name] arg1 arg2 arg3..."
  Any number of arguments can be passed (including none) and should
be separated by spaces. Various commands can invoke other commands
directly, passing the arguments passed to them or predefined arguments
set by the Command object at initialization, either in sequence or
based on conditional values.
"""


class Command:
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool):
        """
        Creates a Command object which the bot object will call based
        on input from Twitch chat messages

        :param bot:TwitchBot object
        :param name:str, name for command
        :param restricted:bool, determines whether the command is
            invokable by all users in chat or only users in the bot's
            'approved_users' list
        """
        self.bot = bot
        self.name = name
        self.restricted = restricted

    def do(self, user, msg):
        """
        This method simply checks whether the user invoking the command
        has sufficient privileges. Command subclasses should make a
        super() call to this method to determine whether or not to
        execute their associated functionality.

        :param user:str, name of user invoking the command
        :param args:(str, str...), arbitrary arguments passed after
            invocation of the command
        """
        pass

    def do_other(self, name, user, msg):
        """
        This method allows one command to invoke another

        :param command:str, name of other command to invoke
        :param args:(str, str...), arbitrary arguments to be
            passed to other commmand
        """
        self.bot.do_command(name, user, msg)

    def get_other(self, name, msg=''):
        """
        This method returns an anonymous function that invokes a separate
        command with certain specified arguments passed to it, before
        any of the arguments passed to the initial invoking command

        :param name:str, name of other command to be invoked
        :param args:arguments for other command
        :return:anonymous function, invoking other command with
            specified args passed to it
        """
        if not msg:
            return lambda user, msg: self.do_other(name, user, msg)

        else:
            return lambda user, fake: self.do_other(name, user, msg)    # smells like code spirit

    def get_step_function(self, entry):
        """
        This method generates a function from an 'entry' that can
        have various forms in order to generate anonymous functions
        that give commands more flexibility in what effects they
        can cause

        :param entry:
                str, the name of another command to be invoked,
                    with the SequenceCommands additional arguments
                    passed

                list [Command class, *args], An anonymous Command
                    (i.e. a command that cannot be invoked separately)
                    object whose 'do' method will be invoked as a
                    step of the sequence command. The args will be
                    passed to the Command class's '__init__' method
                    along with the Sequence command's 'bot' and
                    'restricted' values. (It's name will be an empty
                    string and it will not be stored in the bot
                    object's 'commands' dict attribute)

                list [str, *args], the name of another command to be
                    invoked, along with additional specified arguments
                    that are passed to it's 'do' method. (Any arguments
                    passed to the SequenceCommand's 'do' method are
                    appended after these arguments)

        :return:method, a 'step' function to be used as part of a
            sequence or option branch
        """
        if type(entry) is str:
            return self.get_other(entry)

        else:
            if type(entry[0]) is type(Command):
                cls, *params = entry
                command = cls(self.bot, "", self.restricted, *params)

                return command.do

            else:
                name, msg = entry
                return self.get_other(name, msg)


"""  
    The following Command subclasses represent common functions
for the Twitch bot. Usage is documented in the 'do(*args)'
method for each subclass.
"""


class TextCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, text:str):
        """
        :param info:str, message for bot to send to the chat
        """
        super(TextCommand, self).__init__(bot, name, restricted)
        self.text = text

    def do(self, user, msg):
        """
        The InfoCommand causes the bot to send a message to the
        chat, as defined by its 'info' parameter.
        """
        # self.bot.send_chat(self.text)
        return self.text


class FormatCommand(TextCommand):
    def do(self, user, msg):
        """
        The FormatCommand takes a formatting string and sends a message
        to the chat of the form str.format(**keys), where the keys
        correspond to state variables
        """
        # self.bot.send_chat(
        #     self.text.format(**self.bot.state)
        # )
        return self.text.format(**self.bot.state)


class JsonCommand(TextCommand):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, data:dict|list):
        text = json.dumps(data)
        super(JsonCommand, self).__init__(bot, name, restricted, text)

    def format_json(self) -> str:
        data = json.loads(self.text)
        for (key, value) in data.items():
            data[key] = self.format_item(value)
        
        return json.dumps(data)

    def format_item(self, item:object) -> object:
        if type(item) is str:
            return item.format(**self.bot.state)
        
        if type(item) is dict:
            for (key, value) in item.items():
                item[key] = self.format_item(value)
            return item
        
        if type(item) is list:
            return [self.format_item(i) for i in item]

        return item

    def do(self, user, msg):
        # self.bot.send_chat(
        #     self.format_json()
        # )
        return self.format_json()


class ParseCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool):
        super(ParseCommand, self).__init__(bot, name, restricted)
        # self.key = key
        # self.sub_key = sub_key
    
    def do(self, user, msg):
        data = json.loads(msg)

        # state = self.bot.state
        # k, s = self.key, self.sub_key
        # if self.sub_key:
        #     state[k][s] = data
        # else:
        #     state[k] = data

        return data


class ChainCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, out_command:str, in_command:str):
        super(ChainCommand, self).__init__(bot, name, restricted)
        self.out_command = out_command
        self.in_command = in_command

    def do(self, user, msg):       
        self.bot.set_output_buffer()
        self.do_other(self.out_command, user, msg)

        output = self.bot.get_output_buffer()

        # output should be able to be either a str (chat message with interpolated arguments: "!cmd arg1 arg2")
        #           OR an arbitrary object
        #   need a way to keep straight various use cases when bot commands invoke other commands
        return self.do_other(self.in_command, user, output)


class AliasCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, other:str, msg:str|object):
        """
        :param other:str, name of other command to be invoked
        :param msg:str, message string to be used as 'arguments'
            for the other command
        """
        super(AliasCommand, self).__init__(bot, name, restricted)
        self.command_func = self.get_step_function(other)
        self.msg = msg

    def do(self, user, msg):
        """
        The AliasCommand is used to invoke another command with a
        specific set of arguments defined by the 'other' and 'msg'
        attributes.
        """
        return self.command_func(user, self.msg)


class SequenceCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, *sequence):
        """
        :param sequence:list, a list of 'entries' that define
            steps to be executed when the command is invoked.
        """
        super(SequenceCommand, self).__init__(bot, name, restricted)
        self.steps = []

        for entry in sequence:
            self.steps.append(self.get_step_function(entry))

    def do(self, user, msg):
        """
        The SequenceCommand is used to link a number of different commands
        together. The initialization arguments passed to this class can take
        a number of different forms allowing various ways to invoke other
        commands, or create an anonymous command step from a given Command
        subclass
        """
        for step in self.steps:
            step(user, msg)


class OptionCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, *options):
        """
        :param options:list, [str (option name), 'entry']
            the 'entry' value can have a variety of forms,
            see the Command.get_step_function() method for
            full documentation
        """
        super(OptionCommand, self).__init__(bot, name, restricted)
        self.options = {}

        for option in options:
            key = option[0]
            self.options[key] = self.get_step_function(option[1])

    def do(self, user, msg):
        """
        The OptionCommand creates a command that uses the first argument
        passed to it as a key for it's 'options' dict, invoking the command
        stored in that dict[key]
        """
        option, *msg = msg.split(" ")
        msg = " ".join(msg)

        if option in self.options:
            return self.options[option](user, msg)

        else:
            # self.bot.send_chat(
            #     "Option '{}' not recognized".format(option)
            # )
            return "Option '{}' not recognized".format(option)


class StateCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, key:str|int=None):
        """
        :param key:str, optional the name of the key in
            bot.state dict where variable is stored. If
            key is None then the command name will be used
            for state variable key
        """
        super(StateCommand, self).__init__(bot, name, restricted)
        if key is None:
            key = name

        self.state_key = key

    def do(self, user, msg):
        """
        The StateCommand allows the bot to set so called
        'state variables' that are stored in a 'state' dict
        attribute of the bot object. By default, all the args
        passed to this command are concatenated into a string
        (i.e. the string of the chat message after the command
        is invoked)
        """
        self.bot.set_state_variable(self.state_key, msg)


# class PostCommand(Command):
#     def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, url:str):
#         super(PostCommand, self).__init__(bot, name, restricted)
#         self.url = url.format(**bot.state)

#     def do(self, *args):
#         """
#         PostCommand sends a POST request to a URL defined by its 'url'
#         parameter. The contents passed to this command represent the
#         request body and typically should be properly formatted JSON.
#         """
#         user, *msg = args
#         msg = " ".join(msg)
#         self.bot.post_to_api(self.name, self.url, msg)


# class GetCommand(Command):
#     def __init__(self, bot: Type[TwitchBot], name: str, restricted: bool, url:str):
#         super(GetCommand, self).__init__(bot, name, restricted)
#         self.url = url.format(**bot.state)
    
#     def do(self, *args):
#         data = self.bot.get_from_api(self.url)

#         self.bot.send_chat(data)
