# IRC Python — Secure Terminal Client

Developer: Hamdy Abou El Anein
Contact: hamdy.aea@protonmail.com
License: GNU GPL v3 (see LICENSE).

A small terminal IRC client using Python 3, Rich and the standard library.

## Improvements

- **TLS certificate verification enabled by default**, using port 6697.
- Correct IRC line framing even when TCP splits or combines messages.
- Automatic `PING/PONG`, join channel after server welcome (`001`).
- Explicit command validation and CRLF injection protection.
- Proper socket cleanup and error handling; no connection on module import.
- `/nickserv` prompts privately for a password rather than storing it.
- No global state and no absolute paths; config is relative to the script.
- Protocol and configuration unit tests without a network connection.

## Install and run

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
# Edit config.ini and set your nickname and channel.
python ircpython.py
```

Supported commands: `/join #channel`, `/part`, `/list`,
`/nick nickname`, `/msg nickname text`, `/nickserv`, `/quit`.

To use another config: `python ircpython.py --config /path/to/config.ini`.
If your IRC network requires plaintext (not recommended), set
`tls = false` and use the appropriate server port.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

All tests use fake sockets. They do not contact an IRC server.
Live network interoperability must be tested separately.

The historical 2026 version is preserved in Git branch `old`.
