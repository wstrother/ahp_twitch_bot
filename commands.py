from twitch_bot import TwitchBot
from typing import Type
import json
import requests

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

    def do_other(self, command, user, msg):
        """
        This method allows one command to invoke another

        :param command:str, name of other command to invoke
        :param args:(str, str...), arbitrary arguments to be
            passed to other commmand
        """
        self.bot.do_command(command, user, msg)

    def get_other(self, command, msg=''):
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
            return lambda user, new_msg: self.do_other(command, user, new_msg)

        else:
            return lambda user, new_msg: self.do_other(command, user, msg)    # smells like code spirit

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

                return self.get_other(command)

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
        return self.text


class FormatCommand(TextCommand):
    def do(self, user, msg):
        """
        The FormatCommand takes a formatting string and sends a message
        to the chat of the form str.format(**keys), where the keys
        correspond to state variables
        """
        return self.text.format(**self.bot.state)


class JsonCommand(TextCommand):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, data:dict|list):
        text = json.dumps(data)
        super(JsonCommand, self).__init__(bot, name, restricted, text)

    @staticmethod
    def format_json(text, state:dict) -> str:
        data = json.loads(text)
        for (key, value) in data.items():
            data[key] = JsonCommand.format_item(value, state)
        
        # return json.dumps(data)
        return data

    @staticmethod
    def format_item(item:object, state:dict) -> object:
        if type(item) is str:
            return item.format(**state)
        
        if type(item) is dict:
            for (key, value) in item.items():
                item[key] = JsonCommand.format_item(value)
            return item
        
        if type(item) is list:
            return [JsonCommand.format_item(i) for i in item]

        return item

    def do(self, user, msg):
        state = self.bot.state
        state['user'] = user
        state['msg'] = msg
        return self.format_json(self.text, state)


class ParseCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool):
        super(ParseCommand, self).__init__(bot, name, restricted)
    
    def do(self, user, msg):
        data = json.loads(msg)

        return data


class ChainCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, out_command:str, in_command:str):
        super(ChainCommand, self).__init__(bot, name, restricted)
        self.out_command = self.get_step_function(out_command)
        self.in_command = self.get_step_function(in_command)

    def do(self, user, msg):       
        self.bot.set_output_buffer()
        self.out_command(user, msg)

        output = self.bot.get_output_buffer()

        return self.in_command(user, output)


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
            return "Option '{}' not recognized".format(option)


class StateCommand(Command):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, key:str|int|None=None, *sub_keys):
        """
        :param key:str, optional the name of the key in
            bot.state dict where variable is stored. If
            key is None then the command name will be used
            for state variable key
        :param sub_keys:list, optional arbitrary depth
            sequence of sub keys to be used as index or key values
            for inner objects (dict and list)
        """
        super(StateCommand, self).__init__(bot, name, restricted)
        if key is None:
            key = name

        self.state_key = key
        self.sub_keys = sub_keys

    def do(self, user, msg):
        """
        The StateCommand allows the bot to set so called
        'state variables' that are stored in a 'state' dict
        attribute of the bot object. By default, all the args
        passed to this command are concatenated into a string
        (i.e. the string of the chat message after the command
        is invoked)
        """
        self.bot.set_state_variable(self.state_key, msg, *self.sub_keys)


class MathCommand(Command):
    def __init__(self, bot: type[TwitchBot], name: str, restricted: bool, op: str, value: int|float):
        """
        Args:
            op (str): key of operation type ('add' or 'multiply')
            value (int | float): the value for the right side of operation
        """
        super(MathCommand, self).__init__(bot, name, restricted)
        self.operation = {
            "add": lambda n: n + value,
            "multiply": lambda n: n * value
        }[op]
    
    def do(self, user, msg):
        try:
            msg = int(msg)
        except ValueError:
            try:
                msg = float(msg)
            except ValueError:
                raise ValueError(f'Value passed to MathCommand cannot be cast to numeric type: "{msg}"')
        
        return self.operation(msg)

##
## requests / API calls
def make_request(method:str) -> Type[requests.post]:
    return {
        "POST": requests.post,
        "GET": requests.get,
        "PUT": requests.put,
        "PATCH": requests.patch,
        "DELETE": requests.delete
    }[method]


def api_request(url:str, data:dict, method:str='GET', headers:None|dict=None) -> str|dict:
    if not headers:
        headers = {'Content-type': 'application/json'}

    p:None|requests.Response = None
    try:
        p = make_request(method)(
            url, data=data, headers=headers
        )
    except requests.ConnectionError as e:
        error = "API request to {} failed:\n".format(url)
        return error
    
    if p:
        try:
            return p.json()
        except json.JSONDecodeError:
            return p.text


class RequestCommand(Command):
    def __init__(self, bot: Type[TwitchBot], name: str, restricted: bool, url:str, method:str, headers:None|dict=None):
        super(RequestCommand, self).__init__(bot, name, restricted)
        self.url = url
        self.method = method
        self.headers = json.dumps(headers)

    def do(self, user, msg):
        url = self.url.format(**self.bot.state)
        headers = JsonCommand.format_json(self.headers, self.bot.state)

        return api_request(url, msg, self.method, headers)


class PostCommand(RequestCommand):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, url:str, headers:None|dict=None):
        super(PostCommand, self).__init__(bot, name, restricted, url, 'POST', headers)


class PatchCommand(RequestCommand):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, url:str, headers:None|dict=None):
        super(PatchCommand, self).__init__(bot, name, restricted, url, 'PATCH', headers)


class DeleteCommand(RequestCommand):
    def __init__(self, bot:Type[TwitchBot], name:str, restricted:bool, url:str, headers:None|dict=None):
        super(DeleteCommand, self).__init__(bot, name, restricted, url, 'DELETE', headers)


class GetCommand(RequestCommand):
    def __init__(self, bot: Type[TwitchBot], name: str, restricted: bool, url:str, headers:None|dict=None):
        super(GetCommand, self).__init__(bot, name, restricted, url, 'GET', headers)
