#   The commands.py module defines a Command class and collection of
# subclasses that provide various functions for the TwitchBot class
# that can be invoked through the Twitch chat. Commands are invoked
# through chat messages that have the form:
#       "![command_name] arg1 arg2 arg3..."
#   Any number of arguments can be passed (including none) and should
# be separated by spaces. Various commands can invoke other commands
# directly, passing the arguments passed to them or predefined arguments
# set by the Command object at initialization, either in sequence or
# based on conditional values.
import json
import requests


class Command:
    def __init__(self, bot, name, restricted):
        """
        Creates a Command object which the bot object will call based
        on input from Twitch chat messages

        :param bot: TwitchBot object
        :param name: str, name for command
        :param restricted: bool, determines whether the command is
            invokable by all users in chat or only users in the bot's
            'approved_users' list
        """
        self.bot = bot
        self.name = name
        self.restricted = restricted

    def do(self, user, *args):
        """
        This method simply checks whether the user invoking the command
        has sufficient privileges. Command subclasses should make a
        super() call to this method to determine whether or not to
        execute their associated functionality.

        :param user: str, name of user invoking the command
        :param args: (str, str...), arbitrary arguments passed after
            invocation of the command
        """
        pass

    def do_other(self, command, *args):
        """
        This method allows one command to invoke another

        :param command: str, name of other command to invoke
        :param args: (str, str...), arbitrary arguments to be
            passed to other commmand
        """
        self.bot.do_command(command, *args)

    def get_other(self, name, *args):
        """
        This method returns an anonymous function that invokes a separate
        command with certain specified arguments passed to it, before
        any of the arguments passed to the initial invoking command

        :param name: str, name of other command to be invoked
        :param args: arguments for other command
        :return: anonymous function, invoking other command with
            specified args passed to it
        """
        return lambda user, *rgs: self.do_other(name, user, *list(args) + list(rgs))

    def get_step_function(self, entry):
        """
        This method generates a method from an 'entry' that can
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

        :return: method, a 'step' function to be used as part of a
            sequence or option branch
        """
        if type(entry) is str:
            return self.get_other(entry)

        else:
            if type(entry[0]) is type(Command):
                cls, entry = entry[0], entry[1:]
                command = cls(self.bot, "", self.restricted, *entry)

                return command.do

            else:
                name, args = entry[0], entry[1:]

                return self.get_other(name, *args)


#   The following Command subclasses represent common functions
# for the Twitch bot. Usage is documented in the 'do(*args)'
# method for each subclass.


class EchoCommand(Command):
    def __init__(self, bot, name, restricted, alias):
        """
        :param alias: str, name of other command for bot to invoke
        """
        super(EchoCommand, self).__init__(bot, name, restricted)
        self.alias = alias

    def do(self, *args):
        """
        The EchoCommand takes any arguments passed to it and makes the
        bot send an additional message to the chat invoking another
        command with the same arguments

        It is used to 'alias' commands for other bots, which should then
        be invoked as part of other commands used by the bot
        """
        user, msg = args[0], " ".join(args[1:])
        self.bot.send_chat("!{} {}".format(self.alias, msg))


class InfoCommand(Command):
    def __init__(self, bot, name, restricted, info):
        """
        :param info: str, message for bot to send to the chat
        """
        super(InfoCommand, self).__init__(bot, name, restricted)
        self.info = info

    def do(self, *args):
        """
        The InfoCommand causes the bot to send a message to the
        chat, as defined by its 'info' parameter.
        """
        self.bot.send_chat(self.info)


class FormatCommand(InfoCommand):
    def do(self, *args):
        """
        The FormatCommand takes a formatting string and sends a message
        to the chat of the form str.format(**keys), where the keys
        correspond to state variables
        """
        self.bot.send_chat(
            self.f_str.format(**self.bot.state)
        )


class AliasCommand(Command):
    def __init__(self, bot, name, restricted, other, msg):
        """
        :param other: str, name of other command to be invoked
        :param msg: str, message string to be used as 'arguments'
            for the other command
        """
        super(AliasCommand, self).__init__(bot, name, restricted)
        self.other = other
        self.msg = msg.split(" ")

    def do(self, user, *args):
        """
        The AliasCommand is used to invoke another command with a
        specific set of arguments defined by the 'other' and 'msg'
        attributes.
        """
        self.do_other(self.other, user, *self.msg)


class SequenceCommand(Command):
    def __init__(self, bot, name, restricted, *sequence):
        """
        :param sequence: list, a list of 'entries' that define
            steps to be executed when the command is invoked.
        """
        super(SequenceCommand, self).__init__(bot, name, restricted)
        self.steps = []

        for entry in sequence:
            self.steps.append(self.get_step_function(entry))

    def do(self, *args):
        """
        The SequenceCommand is used to link a number of different commands
        together. The initialization arguments passed to this class can take
        a number of different forms allowing various ways to invoke other
        commands, or create an anonymous command step from a given Command
        subclass
        """
        for step in self.steps:
            step(*args)


class OptionCommand(Command):
    def __init__(self, bot, name, restricted, *options):
        """
        :param options: list, [str (option name), 'entry']
            the 'entry' value can have a variety of forms,
            see the Command.get_step_function() method for
            full documentation
        """
        super(OptionCommand, self).__init__(bot, name, restricted)
        self.options = {}

        for option in options:
            key = option[0]
            self.options[key] = self.get_step_function(option[1:])

    def do(self, *args):
        """
        The OptionCommand creates a command that uses the first argument
        passed to it as a key for it's 'options' dict, invoking the command
        stored in that dict[key]
        """
        args = list(args)
        user = args.pop(0)
        option = args.pop(0)

        if option in self.options:
            self.options[option](user, *args)

        else:
            self.bot.send_chat(
                "Option '{}' not recognized".format(option)
            )


class StateCommand(Command):
    def __init__(self, bot, name, restricted, key=None):
        """
        :param key: str, optional the name of the key in
            bot.state dict where variable is stored. If
            key is None then the command name will be used
            for state variable key
        """
        super(StateCommand, self).__init__(bot, name, restricted)
        if key is None:
            key = name

        self.state_key = key

    def do(self, *args):
        """
        The StateCommand allows the bot to set so called
        'state variables' that are stored in a 'state' dict
        attribute of the bot object. By default, all the args
        passed to this command are concatenated into a string
        (i.e. the string of the chat message after the command
        is invoked)
        """
        user, value = args[0], " ".join(args[1:])
        self.bot.set_state(self.state_key, value)


class SubStateCommand(Command):
    def __init__(self, bot, name, restricted, key, sub_key):
        super(SubStateCommand, self).__init__(bot, name, restricted)

        self.state_key = key
        self.sub_key = sub_key

    def do(self, user, *args):
        """
        SubStateCommand modifies the value of a certain key within
        a state variable that is a dict type object.
        """
        value = " ".join(args)

        d = self.bot.get_state(self.state_key).copy()
        d[self.sub_key] = value
        self.bot.set_state(self.state_key, d)



class PostCommand(Command):
    def __init__(self, bot, name, restricted, url):
        super(PostCommand, self).__init__(bot, name, restricted)
        self.url = url

    def do(self, *args):
        """
        PostCommand sends a POST request to a URL defined by its 'url'
        parameter. The contents passed to this command represent the
        request body and typically should be properly formatted JSON.
        """
        user, *msg = args
        msg = " ".join(msg)
        self.bot.post_to_api(self.name, self.url, msg)
