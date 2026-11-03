#!/usr/bin/env python3
# Developer: Hamdy Abou El Anein
# Contact: hamdy.aea@protonmail.com
# SPDX-License-Identifier: GPL-3.0-or-later
"""Offline protocol, configuration and client tests."""
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from irc_core import Settings, load_settings, outgoing, parse_line
from ircpython import IRCClient


class ProtocolTests(unittest.TestCase):
    def test_fragmented_tcp_lines_are_parsed_individually(self):
        self.assertEqual(parse_line(":nick!u@h PRIVMSG #linux :hello world\r\n"),
                         ("nick!u@h", "PRIVMSG", ["#linux", "hello world"]))
        self.assertEqual(parse_line("PING :server.example\r\n"),
                         (None, "PING", ["server.example"]))

    def test_outgoing_frames(self):
        self.assertEqual(outgoing("PRIVMSG", "#linux", trailing="hello"),
                         b"PRIVMSG #linux :hello\r\n")
        for text in ("a\r\nQUIT :oops", "a" * 600):
            with self.subTest(text=text[:8]), self.assertRaises(ValueError):
                outgoing("PRIVMSG", "#linux", trailing=text)

    def test_configuration(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.ini"
            path.write_text("[IRC]\nserver=irc.example.net\nnick=tester\nchannel=#linux\n")
            settings = load_settings(path)
            self.assertTrue(settings.tls)
            self.assertEqual(settings.port, 6697)
            path.write_text("[IRC]\nserver=irc.example.net\nnick=tester\nchannel=#linux\nport=99999\n")
            with self.assertRaises(ValueError):
                load_settings(path)

    def test_commands_do_not_inject_newlines(self):
        client = IRCClient(Settings("example.net", 6697, "tester", "#linux", "tester"), Mock())
        client.socket = Mock()
        client.handle_input("/msg other hello there")
        client.socket.sendall.assert_called_with(b"PRIVMSG other :hello there\r\n")
        with self.assertRaises(ValueError):
            client.handle_input("hello\nQUIT :injected")

    def test_ping_pong_and_join_after_welcome(self):
        client = IRCClient(Settings("example.net", 6697, "tester", "#linux", "tester"), Mock())
        sock = MagicMock()
        sock.makefile.return_value.__enter__.return_value = iter([
            "PING :irc.example.net\r\n",
            ":server 001 tester :Welcome\r\n",
            ":nick!u@h PRIVMSG #linux :Hello\r\n",
        ])
        client.socket = sock
        client.receive()
        sent = [args[0][0] for args in sock.sendall.call_args_list]
        self.assertIn(b"PONG :irc.example.net\r\n", sent)
        self.assertIn(b"JOIN #linux\r\n", sent)


if __name__ == "__main__":
    unittest.main()
