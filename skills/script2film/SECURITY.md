# Security

## What runs where

Script2Film is a set of scripts you run on your own machine. There is no hosted service and nothing listens for
connections from other machines. Two tools open a local port while they run: the TalkingPhotos browser
(`tools/tp/tp_browser.py`, Chrome's debugging port on 127.0.0.1) and the YouTube sign-in (`tools/youtube/yt_upload.py`,
a one-time local page for Google's OAuth flow).

## Keys and logins

- API keys go in `~/.config/script2film/secrets.json` or in the environment; the environment wins. They never go in
  `~/.config/script2film/config.json` or a project folder. `python3 tools/doctor/doctor.py` warns when
  `secrets.json` has any permission other than 600 (fix: `chmod 600 ~/.config/script2film/secrets.json`). The default flow needs
  no key at all.
- YouTube credentials are in `~/.config/script2film/youtube/` (or `S2F_YT_DIR`).
- Browser logins for VideoExpress and TalkingPhotos live in their own browser profile folders
  (`tools/ve-runner/.profile/`, ignored by git, and `~/.config/script2film/tp-profile`). Treat these folders like
  passwords.

## Reporting a vulnerability

Please report it privately through GitHub: on the repository page open **Security**, then **Report a vulnerability**.
Do not open a public issue for it. Include what you found, how to reproduce it, and which files are involved.
