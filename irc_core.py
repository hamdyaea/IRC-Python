#!/usr/bin/env python3
# Developer: Hamdy Abou El Anein
# Contact: hamdy.aea@protonmail.com
# Copyright (C) 2026 Hamdy Abou El Anein
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pure IRC protocol and configuration helpers; safe to import offline."""
from __future__ import annotations

from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass(frozen=True)
class Settings:
    server: str
    port: int
    nick: str
    channel: str
    realname: str
    tls: bool = True


_TOKEN = re.compile(r"^[A-Za-z0-9_\[\]\\^{}|\x60-]+$")
_CHANNEL = re.compile(r"^[#&][^\x00\r\n ,:]{1,199}$")


def valid_token(token: str) -> str:
    if not _TOKEN.fullmatch(token):
        raise ValueError("Invalid IRC nickname/target.")
    return token


def valid_channel(channel: str) -> str:
    if not _CHANNEL.fullmatch(channel):
        raise ValueError("Invalid IRC channel.")
    return channel


def safe_text(text: str) -> str:
    if any(char in text for char in ("\r", "\n", "\x00")):
        raise ValueError("IRC text must not contain CR, LF or NUL.")
    return text


def load_settings(path: Path) -> Settings:
    config = ConfigParser(interpolation=None)
    if not config.read(path, encoding="utf-8") or not config.has_section("IRC"):
        raise ValueError(f"Missing [IRC] configuration: {path}")
    section = config["IRC"]
    server = section.get("server", "").strip()
    if not server or any(c.isspace() for c in server) or any(c in server for c in "\r\n\x00/"):
        raise ValueError("Invalid IRC server hostname.")
    port = section.getint("port", fallback=6697)
    if not 1 <= port <= 65535:
        raise ValueError("IRC port must be 1–65535.")
    nick = valid_token(section.get("nick", "").strip())
    channel = valid_channel(section.get("channel", "").strip())
    realname = safe_text(section.get("realname", nick).strip())
    tls = section.getboolean("tls", fallback=True)
    return Settings(server, port, nick, channel, realname, tls)


def parse_line(line: str) -> tuple[str | None, str, list[str]]:
    """Parse one RFC1459 line; preserve trailing parameter spaces."""
    line = line.rstrip("\r\n")
    prefix = None
    if line.startswith(":"):
        prefix, sep, line = line[1:].partition(" ")
        if not sep:
            return prefix, "", []
    if " :" in line:
        head, trailing = line.split(" :", 1)
        parts = head.split()
        if not parts:
            return prefix, "", [trailing]
        return prefix, parts[0].upper(), parts[1:] + [trailing]
    parts = line.split()
    return (prefix, parts[0].upper(), parts[1:]) if parts else (prefix, "", [])


def outgoing(command: str, *params: str, trailing: str | None = None) -> bytes:
    if not re.fullmatch(r"[A-Z]+", command):
        raise ValueError("Invalid IRC command.")
    for param in params:
        safe_text(param)
        if not param or " " in param or param.startswith(":"):
            raise ValueError("Invalid IRC parameter.")
    payload = " ".join((command, *params))
    if trailing is not None:
        payload += " :" + safe_text(trailing)
    encoded = payload.encode("utf-8")
    if len(encoded) > 510:
        raise ValueError("IRC message exceeds the 512-byte protocol limit.")
    return encoded + b"\r\n"
