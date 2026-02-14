#!/usr/bin/env python3
'''
Name: Hamdy Abou El Anein
Email: hamdy.aea@protonmail.com 
Date of creation:  14-02-2026
Last update: 14-02-2026
Version: 1.0
Description: A IRC client in Python  
'''

import socket
import threading
import sys
import configparser
import signal
from rich.console import Console
from rich.markup import escape
from rich.prompt import Prompt
from datetime import datetime

# ---------------------------
# Global variables
# ---------------------------
console = Console()
running = True
CHANNEL = None  # will be set from config
irc = None

# ---------------------------
# Handle Ctrl+C
# ---------------------------
def signal_handler(sig, frame):
    global running, irc
    console.print("\n[bold red]Graceful disconnect...[/bold red]")
    running = False
    try:
        if irc:
            irc.send("QUIT :Client closed\r\n".encode())
            irc.close()
    except:
        pass
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# ---------------------------
# Read config
# ---------------------------
config = configparser.ConfigParser()
config.read("config.ini")

SERVER = config["IRC"]["server"]
PORT = int(config["IRC"]["port"])
NICK = config["IRC"]["nick"]
CHANNEL = config["IRC"]["channel"]
REALNAME = config["IRC"]["realname"]

# ---------------------------
# Connect to IRC server
# ---------------------------
irc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
irc.connect((SERVER, PORT))
irc.send(f"NICK {NICK}\r\n".encode())
irc.send(f"USER {NICK} 0 * :{REALNAME}\r\n".encode())

# ---------------------------
# Display messages with Rich
# ---------------------------
def display_message(msg):
    msg = msg.strip()
    timestamp = datetime.now().strftime("%H:%M:%S")

    if "PRIVMSG" in msg:
        try:
            parts = msg.split(":", 2)
            if len(parts) >= 3:
                prefix = parts[1].split("!")[0]  # nick
                message = parts[2]
                channel = msg.split()[2]
                console.print(f"[bold blue][{channel}][/bold blue] [green]{prefix}[/green]: {escape(message)} [{timestamp}]")
        except:
            console.print(f"[yellow]{escape(msg)} [{timestamp}][/yellow]")
    else:
        # System messages
        console.print(f"[yellow]{escape(msg)} [{timestamp}][/yellow]")

# ---------------------------
# Receive messages
# ---------------------------
def receive_messages():
    global running
    while running:
        try:
            msg = irc.recv(4096).decode("utf-8", errors="ignore")
            if not msg:
                break
            if msg.startswith("PING"):
                irc.send(f"PONG {msg.split()[1]}\r\n".encode())
            else:
                display_message(msg)
        except:
            break

# ---------------------------
# Send messages
# ---------------------------
def send_messages():
    global running, CHANNEL
    while running:
        try:
            msg = Prompt.ask(f"[bold magenta]{CHANNEL}[/bold magenta] >")
            if msg.startswith("/"):
                handle_command(msg)
            else:
                irc.send(f"PRIVMSG {CHANNEL} :{msg}\r\n".encode())
        except EOFError:
            break
        except Exception:
            break

# ---------------------------
# Handle IRC commands
# ---------------------------
def handle_command(cmd):
    global CHANNEL, running
    parts = cmd.split()
    if len(parts) == 0:
        return

    if parts[0] == "/join" and len(parts) > 1:
        CHANNEL = parts[1]
        irc.send(f"JOIN {CHANNEL}\r\n".encode())
    elif parts[0] == "/part":
        irc.send(f"PART {CHANNEL}\r\n".encode())
    elif parts[0] == "/list":
        irc.send("LIST\r\n".encode())
    elif parts[0] == "/nick" and len(parts) > 1:
        irc.send(f"NICK {parts[1]}\r\n".encode())
    elif parts[0] == "/msg" and len(parts) > 2:
        target = parts[1]
        message = " ".join(parts[2:])
        irc.send(f"PRIVMSG {target} :{message}\r\n".encode())
    elif parts[0] == "/quit":
        irc.send("QUIT :Client closed\r\n".encode())
        running = False
    elif parts[0] == "/nickserv" and len(parts) > 1:
        irc.send(f"PRIVMSG NickServ :{' '.join(parts[1:])}\r\n".encode())
    else:
        console.print("[red]Unknown command[/red]")

# ---------------------------
# Start threads
# ---------------------------
recv_thread = threading.Thread(target=receive_messages)
recv_thread.daemon = True
recv_thread.start()

send_thread = threading.Thread(target=send_messages)
send_thread.daemon = True
send_thread.start()

# ---------------------------
# Keep program alive
# ---------------------------
try:
    recv_thread.join()
    send_thread.join()
except KeyboardInterrupt:
    signal_handler(None, None)

irc.close()
sys.exit(0)

