# IRC Python Client

A lightweight command-line IRC client built in **Python** with **Rich** for colorful and formatted output.  
Supports real-time chat, multiple IRC commands, and clean exit handling.  

---

## Features

- Connect to any IRC server with a nickname.
- Colorful and formatted output using [Rich](https://rich.readthedocs.io/).  
- Real-time message reception and sending.  
- Supports common IRC commands:
  - `/join <channel>` — join a channel  
  - `/part` — leave a channel  
  - `/list` — list available channels  
  - `/nick <newnick>` — change your nickname  
  - `/msg <target> <message>` — send a private message  
  - `/nickserv <command>` — interact with NickServ (identify, ghost, etc.)  
  - `/quit` — disconnect gracefully  
- Automatic handling of **JOIN confirmation** before sending messages.  
- Proper handling of **Ctrl+C** to quit Python cleanly.  

---

## Requirements

- Python 3.8+
- [Rich](https://pypi.org/project/rich/) for colored console output  

Dependencies are listed in `requirements.txt`:

```text
rich

## Setup   

Clone this repository:

git clone <repository_url>
cd <repository_folder>


Create a virtual environment:

python3 -m venv myenv


Activate the virtual environment:

On Linux/macOS:

source myenv/bin/activate


On Windows (PowerShell):

.\myenv\Scripts\Activate.ps1


## Install dependencies:   

pip install -r requirements.txt

## Configuration  

Edit config.ini to set your IRC server, port, nickname, channel, and real name:

[IRC]
server = irc.libera.chat
port = 6667
nick = your_nick
channel = #yourchannel
realname = Your Name

## Usage   

Run the client:

python ircpython.py


Once connected:

Type messages to send to the current channel.

Use / commands to interact with IRC.

Example:

/nick NewNick
/join #otherchannel
/msg Friend Hello there!
/quit

Notes

The first message will now always display the channel correctly, thanks to automatic JOIN confirmation handling.

Proper identification with NickServ is recommended on networks like Libera Chat:

/msg NickServ IDENTIFY <nick> <password>


