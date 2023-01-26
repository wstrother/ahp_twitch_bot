from twitch_bot import TwitchBot, BotLoader

if __name__ == "__main__":
  USER_NAME = "ahp_twitch_bot"
  CHANNEL = "#athenshorseparty_"
  TOKEN = "oauth.token"
  SETTINGS = "bot_settings.json"
  JOIN_MESSAGE = "Logging on..."

  BotLoader.load_bot(
      SETTINGS, TwitchBot, (USER_NAME, TOKEN)
  ).run(CHANNEL, JOIN_MESSAGE)
