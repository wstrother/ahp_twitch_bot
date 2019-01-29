# 'ahp_twitch_bot'

Welcome to my new repository for a simple little
Python package that will help anyone make a helpful,
fun Twitch bot! The bot you make with this package will
allow you to make simple commands to interface with
other popular bots like Nightbot, as well as leverage
the power of Python (and the tons of existing libraries)
to make your own cool features. Another useful feature
is the ability to modify/store variables and change
files on your system that can be used to alter your
stream layout directly from your own Twitch chat.

### Requirements

* Python 3
* A Twitch account for your bot (and oauth token)

---

## Usage

Any of the classes defined in the four core modules can
be subclassed to define more specific functionality, but the
**BotLoader** class in **twitch_bot.py** helps define a
JSON based data interface that can be used to automatically
customize the implementation of your Twitch bot.

Here's a typical example:

### **stream.py**

```python
from ahp_twitch_bot.twitch_bot import TwitchBot, BotLoader

if __name__ == "__main__":
  USER_NAME = "your_bot_user_name"
  CHANNEL = "#your_twitch_channel"
  TOKEN = "oauth.token"
  SETTINGS = "bot_settings.json"
  JOIN_MESSAGE = "Logging on..."

  BotLoader.load_bot(
      SETTINGS, TwitchBot, (USER_NAME, TOKEN)
  ).run(CHANNEL, JOIN_MESSAGE)
```

Be sure to create a file for your oauth token (obtainable
[here](https://twitchapps.com/tmi/)).

### **bot_settings.json**

To define attributes and behaviors for your bot, you'll need to
create a JSON data file and provide some instuctions. The following
keys should always be present in your bot data file to ensure that
**BotLoader.load_bot()** doesn't raise an error:

```python
{
  "classes": {
      "alias": "ClassName"
    },
  "approved_users": [
      "user_1",
      "user_2"
    ],
  "restricted": [
      :command1,
      :command2
    ],
  "public": [
      :command3,
      :command4
    ]  
}
```

* **"classes":** defines alias keys for different classes that can be
used elsewhere in your JSON data

* **"approved_users":** defines user names for users that are allowed
to use restricted commands

* **"restricted":** defines commands that can only be used by approved
users

* **"public":** defines commands that anyone in chat can use

### Defining commands

Commands defined within your JSON data will need to be expressed as a
list (in Python terms) / array (in JS terms) that contain an arbitrary
series of arguments but will always begin by specifying a Class, then
the *'name'* of the command, and then any additional arguments.

Commands are invoked in chat by sending a message that begins with
*'!name'* and then specifies any additional arguments, separated
from the command name by spaces, such as: *'!name arg1 arg2'.*

The Class argument can be either the name of the Class (i.e. the
**CommandClass.__name__** attribute in Python) or some alias as
defined in your JSON data's **"classes": {}"** value.

Some common usage examples (for each of the **CommandClass**
subclasses) sepcified in **commands.py** include:

#### EchoCommand

```python
["EchoCommand", "name", "other_command"]
```

These commands will take some argument and cause your bot to echo
that input in the chat as arguments of some other command name.
Typically, this is so your bot can send commands to other common bots,
such as Nightbot's *"!title"* command. Thus, they're not really useful
on their own, but in combination with other commands, they give you
useful ways to leverage the functionality of other common bots.

#### AliasCommand

```python
["AliasCommand", "name", "other_command", "arg1", "arg2"...]
```

These commands do not take any arguments, instead they invoke some other
command with a specified set of arguments passed to it. They are useful
for creating a shorthand for a common command/argument pair such as
typing *"!ssb"* to invoke *"!game Super Smash Bros."*.

#### SequenceCommand

```python
["SequenceCommand", "name",
  :command_entry1,
  :command_entry2...
]
```

These commands will invoke a series of other commands, passing any arguments
they receive to each command in the series they invoke. Each ':command_entry'
item can be expressed in a number of ways:

* **["ClassName", "init_arg1", "init_arg2"...]:** an "anonymous" command,
which will not have a name or be invokable on it's own, and a set
of initialization arguments for that class
* **"command_name":** the name of some other command to invoke
* **["command_name", "arg1", "arg2"...]:** the name of some other
command to invoke and a set of arguments to pass to it before the
arguments invoked with the original SequenceCommand

Because usage of these expressions is so flexible, it's important to be
clear on the way arguments specified in these expressions interact with
the arguments passed from the chat as the SequenceCommand is invoked.

In the first case, the *'init_args'* are used to instantiate the anonymous
command, and arguments passed to the SequenceCommand will also be passed to
that anonymous command.

In the second case, the same arguments passed to the SequenceCommand are
passed to the named comman specified for that step.

In the third case, the arguments specified in the *':command_entry'* step
expression are passed *before* the arguments invoked with the SequenceCommand
in the chat. So typing *'!sequence_command arg3 arg4'* where *'sequence_command'*
has some step expressed as **['other_command', 'arg1', 'arg2']** would be the
same as typing *'!other_command arg1 arg2 arg3 arg4'*.

#### OptionCommand

```python
["OptionCommand", "name"
  :command_entry1,
  :command_entry2...
]
```

These commands take some argument and use it to determine which from a
series of other commands to invoke, passing all arguments after the first
to that other command. Here, any *':command_entry'* expression can have
any of the same formats specified for **SequenceCommand**, including
'anonymous' commands and other commands invoked with specified arguments.

The same rules apply for passing arguments as with **SequenceCommand**
except that the first argument passed to the initial **OptionCommand**
will not be passed to the option selected. So *'!option_command choice
arg1'* will not pais *'choice'* to the other command specified by that
choice.

#### StateCommand

```python
["StateCommand", "name", (optional)"key"]
```

These commands set some 'state variable' of the bot, stored in the
**TwitchBot.state** dict attribute. The name of the command is used
as the key for the state dict by default, but optionally, the key
can be specified so that the command's name is different from the
name of the state variable.

The arguments passed to a **StateCommand** are concatenated by " "
strings such that *'!state_command some value here'* set's the state
variable to the string *'some value here'*.


#### FileCommand

```python
["FileCommand", "name", "file_name"]
```

These commands specify some file in the current directory to be written
to with the arguments passed to this command. Like the **StateCommand**,
arguments are concatenated together to form a string such that
*'!file_command some text here'* will set the contents of the specified
file to be *'some text here'*.

#### InfoCommand

```python
["InfoCommand", "name", "info"]
```

These commands will simply send any information specified by the "info"
value to the chat anytime the command is invoked.

#### ListenerCommand

```python
["ListenerCommand", "name", :listener_entry]
```

These commands set some **ChatListener** object for the bot. As of the
current version, subclasses for default functionalities haven't been
defined in **listeners.py** like the **commands.py** module, so you
will have to implement your own **ChatListener** subclass to use a
**ListenerCommand**.

The *:listener_entry* expression should have the form:

```python
["ChatListenerClass", "init_arg1", "init_arg2"...]
```

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

### listeners.py

Defines a **ChatListener** subclass that executes some code when it
detects a certain trigger string in a given chat message. Optionally
can specify a single user whose messages should be the only messages
that trigger the listener.

Can be subclassed for custom functionality, but future versions will
incorporate a standard subclass set like the **commands.py** module.
