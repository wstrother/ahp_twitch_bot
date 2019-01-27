class Command:
    def __init__(self, bot, name, approved):
        self.name = name
        self.bot = bot
        self.approved_only = approved
        self.steps = []

    def do(self, user, *args):
        ok = True

        if self.approved_only:
            ok = False

            if user in self.bot.approved_users:
                ok = True

        return ok

    def do_other(self, command, *args):
        self.bot.do_command(command, *args)


class EchoCommand(Command):
    def __init__(self, bot, name, approved, alias):
        super(EchoCommand, self).__init__(bot, name, approved)
        self.alias = alias

    def do(self, *args):
        if super(EchoCommand, self).do(*args):
            user, msg = args[0], " ".join(args[1:])
            self.bot.send_chat("!{} {}".format(self.alias, msg))


class AliasCommand(Command):
    def __init__(self, bot, name, approved, other, msg):
        super(AliasCommand, self).__init__(bot, name, approved)
        self.other = other
        self.msg = msg.split(" ")

    def do(self, *args):
        if super(AliasCommand, self).do(*args):
            args = list(args) + self.msg
            self.do_other(self.other, *args)


class SequenceCommand(Command):
    def __init__(self, bot, name, approved, *sequence):
        super(SequenceCommand, self).__init__(bot, name, approved)
        self.steps = []

        for entry in sequence:
            if type(entry) is str:
                self.steps.append(self.get_other(entry))

            else:
                if type(entry[0]) is type(Command):
                    cls, entry = entry[0], entry[1:]
                    command = cls(bot, "", self.approved_only, *entry)
                    self.steps.append(command.do)

                else:
                    name, args = entry[0], entry[1:]
                    self.steps.append(self.get_other(name, *args))

    def get_other(self, name, *args):
        return lambda *rgs: self.do_other(name, *list(rgs) + list(args))

    def do(self, *args):
        if super(SequenceCommand, self).do(*args):
            for step in self.steps:
                step(*args)


class OptionCommand(Command):
    def __init__(self, bot, name, approved, *options):
        super(OptionCommand, self).__init__(bot, name, approved)
        self.options = {}

        for option in options:
            key = option[0]
            value = option[1:]
            self.options[key] = value

    def do(self, *args):
        if super(OptionCommand, self).do(*args):
            args = list(args)
            user = args.pop(0)
            option = args.pop(0)

            if option in self.options:
                args = self.options[option]
                if len(args) > 1:
                    command, args = args[0], args[1:]
                else:
                    command, args = args[0], []

                self.bot.do_command(command, user, *args)


class StateCommand(Command):
    def __init__(self, bot, name, approved, key=None):
        super(StateCommand, self).__init__(bot, name, approved)
        if key is None:
            key = name

        self.state_key = key

    def do(self, *args):
        if super(StateCommand, self).do(*args):
            user, value = args[0], " ".join(args[1:])
            self.bot.set_state(self.state_key, value)


class ListenerCommand(Command):
    def __init__(self, bot, name, approved, listener):
        super(ListenerCommand, self).__init__(bot, name, approved)
        cls, *args = listener
        self.listener = cls(bot, *args)

    def do(self, *args):
        if super(ListenerCommand, self).do(*args):
            self.bot.add_listener(self.listener)
