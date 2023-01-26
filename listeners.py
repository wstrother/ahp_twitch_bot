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

# def add_listener(self, listener):
    #     """
    #     Adds some chat listener to TwitchBot's list of active
    #     listeners if that listener hasn't already been added.
    #     Prints a log message to the console when listener is added
    #     :param listener: Listener object
    #     """
    #     if listener not in self.listeners:
    #         self.listeners.append(listener)

    #         print("\nadded listener \n\tuser: {}\n\ttrigger: {}\n".format(
    #             listener.user, listener.trigger
    #         ))

    # def remove_listener(self, listener):
    #     """
    #     Removes listener from TwitchBot's list of active listeners
    #     :param listener: Listener object
    #     """
    #     if listener in self.listeners:
    #         self.listeners.pop(
    #             self.listeners.index(listener)
    #         )


