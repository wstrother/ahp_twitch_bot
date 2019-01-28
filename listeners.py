from time import sleep


class ChatListener:
    def __init__(self, bot, trigger, user=None, temp=False):
        self.bot = bot
        self.user = user
        self.trigger = trigger
        self.temp = temp

    def hear_message(self, user, msg):
        u, t = False, self.trigger in msg
        if user is None:
            u = True
        elif user == user:
            u = True

        if u and t:
            self.do(user, msg)

    def do(self, user, msg):
        if self.temp:
            self.bot.remove_listener(self)


class TitleTagListener(ChatListener):
    def __init__(self, bot):
        trigger = "The stream title has been updated to: "
        user = "nightbot"
        super(TitleTagListener, self).__init__(bot, trigger, user)

    def do(self, user, msg):
        super(TitleTagListener, self).do(user, msg)

        tag = self.bot.get_state_variable("title_tag")
        if tag and (tag not in msg):
            title = msg.split(self.trigger)[-1]
            title += " {}".format(tag)
            sleep(2)
            self.bot.send_chat("!title {}".format(title))
