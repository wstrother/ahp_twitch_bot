from time import sleep

# the listeners.py module defines a ChatListener class that
# executes some code whenever a 'trigger' string is detected
# in the chat. Individual listener objects can also have a
# specified user name associated with them, so that only messages
# sent by that user will trigger the ChatListener


class ChatListener:
    def __init__(self, bot, trigger, user=None, temp=False):
        """
        :param bot: TwitchBot object
        :param trigger: str, the string that causes the chat
            listener to execute it's 'do' method when it is
            detected in a chat message
        :param user: str, optional user name if trigger should
            only be caused by one specific user
        :param temp: bool, flag that determines whether the
            listener should remove itself once it has been
            triggered
        """
        self.bot = bot
        self.user = user
        self.trigger = trigger
        self.temp = temp

    def hear_message(self, user, msg):
        """
        Checks a chat message to see whether the trigger string
        is present, and if a user name is specified, whether the
        message was sent by the specified user

        :param user: str, name of user who sent chat message
        :param msg: str, message sent to the chat
        """
        u, t = False, self.trigger in msg
        if user is None:
            u = True
        elif user == user:
            u = True

        if u and t:
            self.do(user, msg)

    def do(self, user, msg):
        """
        Subclass hook method, defines whatever code should be
        executed when the trigger string is detected in chat.

        Subclass methods should invoke this method through super
        calls to preserve the 'temp' flag functionality.

        :param user: str, name of user who sent trigger message
        :param msg: str, message containing the trigger string
        :return:
        """
        if self.temp:
            self.bot.remove_listener(self)


# An example ChatListener subclass that activates whenever the user
# 'nightbot' sends a message to the chat that it has changed the
# stream's title. If the bot's 'title_tag' state variable is set,
# and the title of the stream does not contain the 'title_tag' string,
# the bot changes the title of the stream to append the 'title_tag'
# string.


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
            sleep(5)
            self.bot.send_chat("!title {}".format(title))
