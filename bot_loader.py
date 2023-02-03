from twitch_bot import TwitchBot
import inspect
import commands
import json
from typing import Type


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