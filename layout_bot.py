import json
from ahp_twitch_bot.twitch_bot import TwitchBot

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
        ip = None
        if len(args) > 2:
            ip = args[2]
            args = args[:2]

        super(LayoutBot, self).__init__(*args)

        self.state[LAYOUT_KEY] = {}
        self.layout_url = DEFAULT_URL

        if ip:
            self.layout_url = ip

        print(self.layout_url)

    def set_state(self, key, value, log=False):
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
        layout = self.get_state(LAYOUT_KEY)
        data = {
            k: layout[k] for k in layout if layout[k] != old.get(k)
        }
        self.do_command(
            LAYOUT_COMMAND, self.user_name, json.dumps(data)
        )

    def change_game(self):
        game = self.get_state(GAME_KEY)
        self.do_command(
            GAME_COMMAND, self.user_name, game
        )

    def change_title(self):
        title = self.get_state(TITLE_KEY)
        tag = self.get_state(TAG_KEY)

        self.do_command(
            TITLE_COMMAND, self.user_name, "{} {}".format(title, tag)
        )

    def post_to_api(self, command_name, url, msg):
        url = self.layout_url + url
        super(LayoutBot, self).post_to_api(command_name, url, msg)
