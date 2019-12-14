import json
from ahp_twitch_bot.twitch_bot import TwitchBot

"""
This module defines a TwitchBot subclass specifically designed to work with the
AHP_stream_layout node app (http://github.com/wstrother/ahp_stream_layout).

It defines a state variable containing a dict for Layout elements as well as
a "title", "title_tag", and "game" value used to easily switch information
between certain presets.
"""
LAYOUT_KEY = "layout"
LAYOUT_COMMAND = "post_layout"

TITLE_KEY = "title"
TAG_KEY = "title_tag"
TITLE_COMMAND = "st"

GAME_KEY = "game"
GAME_COMMAND = "sg"

DEFAULT_URL = "http://127.0.0.1:4000/api/"


class LayoutBot(TwitchBot):
    def __init__(self, *args):
        """
        An optional 'url' parameter can be specified as the api root, if not
        the value '127.0.0.1:/4000/api/' will be used.
        """
        url = None
        if len(args) > 2:
            url = args[2]
            args = args[:2]

        super(LayoutBot, self).__init__(*args)

        self.state[LAYOUT_KEY] = {}
        self.layout_url = DEFAULT_URL

        if url:
            self.layout_url = url

        print(self.layout_url)

    def set_state(self, key, value, log=False):
        """
        Any changes to the LAYOUT_KEY state variable will automatically trigger
        calls to the 'change_layout' method.

        Changes to TITLE_KEY or TAG_KEY will call the 'change_title' method and
        changes to GAME_KEY will call the 'change_game' method.
        """
        old = self.get_state(key)
        if old != value:
            super(LayoutBot, self).set_state(key, value, log=log)

            if key == LAYOUT_KEY:
                self.change_layout(old)

            if key in (TITLE_KEY, TAG_KEY):
                self.change_title()

            if key == GAME_KEY:
                self.change_game()

    def change_layout(self, old):
        """
        Changes to the LAYOUT_KEY state variable automatically check for
        updated values and send api requests (for the ahp_stream_layout
        api)
        """
        layout = self.get_state(LAYOUT_KEY)
        data = {
            k: layout[k] for k in layout if layout[k] != old.get(k)
        }
        self.do_command(
            LAYOUT_COMMAND, self.user_name, json.dumps(data)
        )

    def change_game(self):
        """
        Any changes to the GAME_KEY state variable automatically trigger the
        command to change the stream game
        """
        game = self.get_state(GAME_KEY)
        self.do_command(
            GAME_COMMAND, self.user_name, game
        )

    def change_title(self):
        """
        Changes to the TITLE_KEY or TAG_KEY state variables automatically
        trigger the command to change the stream title
        """
        title = self.get_state(TITLE_KEY)
        tag = self.get_state(TAG_KEY)

        self.do_command(
            TITLE_COMMAND, self.user_name, "{} {}".format(title, tag)
        )

    def post_to_api(self, command_name, url, msg):
        url = self.layout_url + url
        super(LayoutBot, self).post_to_api(command_name, url, msg)
