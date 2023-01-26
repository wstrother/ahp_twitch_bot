from twitch_bot import TwitchBot, BotLoader
import atexit

if __name__ == "__main__":
  USER_NAME = "ahp_twitch_bot"
  CHANNEL = "#athenshorseparty_"
  TOKEN = "oauth.token"
  SETTINGS = "bot_settings.json"
  JOIN_MESSAGE = "Logging on..."

  with BotLoader.load_bot(SETTINGS, TwitchBot, (USER_NAME, TOKEN)) as bot:
    bot.run(CHANNEL, JOIN_MESSAGE)
