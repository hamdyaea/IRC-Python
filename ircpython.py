#!/usr/bin/env python3
# Developer: Hamdy Abou El Anein
# Contact: hamdy.aea@protonmail.com
# Copyright (C) 2026 Hamdy Abou El Anein
# SPDX-License-Identifier: GPL-3.0-or-later
"""Interactive IRC client with TLS, proper line framing and safe commands."""
from __future__ import annotations

import argparse
from datetime import datetime
import getpass
from pathlib import Path
import socket
import ssl
import sys
import threading

from irc_core import load_settings, outgoing, parse_line, safe_text, valid_channel, valid_token

DEFAULT_CONFIG = Path(__file__).resolve().with_name("config.ini")


class IRCClient:
    def __init__(self, settings, console):
        self.settings = settings
        self.console = console
        self.channel = settings.channel
        self.socket = None
        self.lock = threading.Lock()
        self.stop = threading.Event()

    def connect(self):
        raw = socket.create_connection((self.settings.server, self.settings.port), timeout=15)
        try:
            if self.settings.tls:
                raw = ssl.create_default_context().wrap_socket(
                    raw, server_hostname=self.settings.server
                )
            raw.settimeout(None)
            self.socket = raw
        except Exception:
            raw.close()
            raise
        self.send("NICK", self.settings.nick)
        self.send("USER", self.settings.nick, "0", "*",
                  trailing=self.settings.realname)

    def send(self, command, *params, trailing=None):
        packet = outgoing(command, *params, trailing=trailing)
        with self.lock:
            if self.socket is None:
                raise ConnectionError("Not connected.")
            self.socket.sendall(packet)

    def receive(self):
        try:
            # File iterator buffers partial/multiple TCP messages correctly.
            with self.socket.makefile("r", encoding="utf-8", errors="replace", newline="\n") as reader:
                for line in reader:
                    if self.stop.is_set():
                        break
                    prefix, command, params = parse_line(line)
                    if command == "PING":
                        self.send("PONG", trailing=params[-1] if params else "")
                    elif command == "001":
                        self.send("JOIN", self.channel)
                    elif command == "PRIVMSG" and len(params) >= 2:
                        sender = (prefix or "").split("!", 1)[0]
                        self.show(f"[{params[0]}] {sender}: {params[1]}")
                    elif command:
                        self.show(line.strip())
        except (OSError, ConnectionError) as exc:
            if not self.stop.is_set():
                self.show(f"Connection closed: {type(exc).__name__}")
        finally:
            self.stop.set()

    def show(self, message):
        from rich.markup import escape
        stamp = datetime.now().strftime("%H:%M:%S")
        self.console.print(f"[dim]{stamp}[/dim] {escape(message)}")

    def handle_input(self, line):
        line = safe_text(line)
        if not line:
            return
        if not line.startswith("/"):
            self.send("PRIVMSG", self.channel, trailing=line)
            return
        command, _, rest = line[1:].partition(" ")
        cmd = command.lower()
        rest = rest.strip()
        if cmd == "join" and rest:
            self.channel = valid_channel(rest)
            self.send("JOIN", self.channel)
        elif cmd == "part":
            self.send("PART", self.channel)
        elif cmd == "list":
            self.send("LIST")
        elif cmd == "nick" and rest:
            self.send("NICK", valid_token(rest))
        elif cmd == "msg" and " " in rest:
            target, message = rest.split(" ", 1)
            if target.startswith(("#", "&")):
                valid_channel(target)
            else:
                valid_token(target)
            self.send("PRIVMSG", target, trailing=message)
        elif cmd == "nickserv":
            # Never echo a password to the terminal or store it in config.ini.
            password = getpass.getpass("NickServ password: ")
            if password:
                self.send("PRIVMSG", "NickServ", trailing="IDENTIFY " + safe_text(password))
        elif cmd == "quit":
            self.close()
        else:
            self.show("Commands: /join #channel, /part, /list, /nick N, /msg N text, /nickserv, /quit")

    def close(self):
        already_stopped = self.stop.is_set()
        self.stop.set()
        if not already_stopped:
            try:
                self.send("QUIT", trailing="Client closed")
            except (OSError, ConnectionError):
                pass
        if self.socket:
            try:
                self.socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            self.socket.close()
            self.socket = None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args(argv)
    try:
        from rich.console import Console
        from rich.prompt import Prompt
    except ImportError:
        print("Install dependencies with: python -m pip install -r requirements.txt", file=sys.stderr)
        return 2
    console = Console()
    try:
        settings = load_settings(args.config)
        client = IRCClient(settings, console)
        client.connect()
    except (OSError, ValueError, ssl.SSLError) as exc:
        console.print(f"[red]Unable to connect: {type(exc).__name__}[/red]")
        return 1
    receiver = threading.Thread(target=client.receive, daemon=True)
    receiver.start()
    console.print(f"Connected to {settings.server}:{settings.port} (TLS={settings.tls}).")
    try:
        while not client.stop.is_set():
            try:
                client.handle_input(Prompt.ask(f"[magenta]{client.channel}[/magenta]"))
            except ValueError as exc:
                client.show(f"Invalid input: {exc}")
            except (OSError, ConnectionError):
                break
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        client.close()
        receiver.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
