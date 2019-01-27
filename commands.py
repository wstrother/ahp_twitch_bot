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

        if ok:
            for step in self.steps:
                self.do_step(step, user, *args)

    def do_other(self, command, *args):
        self.bot.do_command(command, *args)

    @staticmethod
    def do_step(step, user, *args):
        step(user, *args)


class EchoCommand(Command):
    def __init__(self, bot, name, approved, alias):
        super(EchoCommand, self).__init__(bot, name, approved)
        self.alias = alias
        self.steps.append(self.call_alias)

    def call_alias(self, *args):
        user, msg = args[0], " ".join(args[1:])
        self.bot.send_chat("!{} {}".format(self.alias, msg))


class AliasCommand(Command):
    def __init__(self, bot, name, approved, other, msg):
        super(AliasCommand, self).__init__(bot, name, approved)
        self.other = other

        msg = msg.split(" ")
        self.steps.append(lambda *args: self.do_other(
            other, *list(args) + msg
        ))


class SequenceCommand(Command):
    def __init__(self, bot, name, approved, *sequence):
        super(SequenceCommand, self).__init__(bot, name, approved)

        for entry in sequence:
            cls, entry = entry[0], entry[1:]
            command = cls(bot, "", self.approved_only, *entry)

            self.steps.append(command.do)
