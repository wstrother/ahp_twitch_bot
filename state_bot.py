import json
from ahp_twitch_bot.twitch_bot import TwitchBot

LAYOUT_KEY = "layout"
LAYOUT_COMMAND = "post_layout"

TITLE_KEY = "title"
TAG_KEY = "title_tag"
TITLE_COMMAND = "st"

GAME_KEY = "game"
GAME_COMMAND = "sg"


class StateBot(TwitchBot):
    def __init__(self, *args):
        super(StateBot, self).__init__(*args)

        self.state[LAYOUT_KEY] = {}

    def set_state(self, key, value, log=False):
        old = self.get_state(key)
        if old != value:
            super(StateBot, self).set_state(key, value, log=log)
            # self.do_command("change_" + key, self.user_name)

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


# if __name__ == "__main__":
#     USER_NAME = "ahp_helper_bot"
#     CHANNEL = "#athenshorseparty_"
#     TOKEN = "oauth.token"
#     SETTINGS = "bot_settings.json"
#
#
#     BotLoader.load_bot(
#         SETTINGS, StateBot, (USER_NAME, TOKEN)
#     ).run(CHANNEL, "Logging on...")
