# 'ahp_twitch_bot'

Welcome to my new repository for a simple little
Python package that will help anyone make a helpful,
fun Twitch bot! 

Right out of the box it supports a ton of functionality including
modifying/storing state variables, contacting third party APIs,
and sequencing, branching, and chaining commands together in
powerful and flexible ways to acheive more functionality.

#### Requirements

* Python3
* [Requests](https://pypi.org/project/requests/)
* A separate Twitch account for your bot

--

## Usage

You can now consult my [dedicated documentation page](https://wstrother.github.io/ahp_twitch_bot_site/) for full instructions on getting set up and creating commands. No programming knowledge required!

---

## Documentation

Full docstrings are provided with the modules in this package. A brief
rundown of each module:

### twitch_chat.py

Defines a **TwitchChat** class which creates a connection to the
Twitch IRC server and a specified Twitch channel's chat room. Parses
messages from the server and passes any chat messages to the bot.

### twitch_bot.py

Defines a **TwitchBot** class that has commands, listeners, and a
list of approved users that can use certain restricted commands. The
bot object can be instantiated programmatically by the **BotLoader**
class based on JSON data, allowing for easy customization of commands
and other functionality.

### commands.py

Defines a **Command** class and set of standard subclasses that can
be used and combined in various ways for a wide range of behavior out
of the box.

---

## FUTURE:

The following are features that I plan on implementing at some point, listed
in their approximate order of likeliness for me to get them done.

* **Modular Bot Data** - The BotLoader class should be refactored to provide
a more flexible data loading routine. The goal should be that any number of
JSON files in a specified directory can be combined in a logical way. The
JSON data that specifies bot settings should also be able to specify URI's
for potential API end-points that would also provide state data for initialization so certain state changes can persist when the bot disconnects.


* **OBS Websocket API integration** - Support for integration with the OBS
websocket API should eventually be able to extend functionality for bot
commands that can automatically control OBS features such as scene transitions
and more.

## Related Projects

Some plans for possible related projects to be developed in the future.

* **Static HTML Form Components** - A set of HTML web components with JS functionality
to create a simple web front end for generating bot commands as JSON data.

* **Web App with API Endpoints** - A simple web application to be set up with
end points for generating bot command data which can then integrate with the
bot program as it's running.

* **Web App with live bot instances (VERY FUTURE)** - A potential web 
application that could run bot instances and handle system changes directly
through the OBS web socket, so that the end user can run an AHP_Twitch_Bot
instance without installing it on their system
