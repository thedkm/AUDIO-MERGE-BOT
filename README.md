# MP3 MERGE-BOT
### PR's welcomed

An Telegram Bot To Merge multiple MP3s in Telegram into single Audio.

Whats NEW!!:
1. Preserve all Metadata of MP3 including Cover art shown on Uploaded MP3 on Telegram.
2. Supports upto 50 files.



## Deploy(at your own risk) :
<p><a href="https://heroku.com/deploy?template=https://github.com/thedkm/MP3-MERGE-BOT"><img src="https://img.shields.io/badge/Deploy%20To%20Heroku-blueviolet?style=for-the-badge&logo=heroku" width="200""/></a></p>

## Config Variables :
1. `API_ID` : User Account Telegram API_ID, get it from my.telegram.org
2. `API_HASH` : User Account Telegram API_HASH, get it from my.telegram.org
3. `BOT_TOKEN` : Your Telegram Bot Token, get it from @Botfather XD
4. `OWNER`: Enter bot owner's ID
5. `OWNER_USERNAME`: User name of bot owner
6. `DATABASE_URL`: Enter your mongodb URI
7. `PASSWORD`: Enter password to login bot

## Commands (add via @botfather) :
```sh
start - Start The Bot
showthumbnail - Shows your thumbnail
deletethumbnail - Delete your thumbnail
help - How to use Bot
login - Access bot
broadcast - (admin) Broadcast message to bot users
stats - check bots stats
```

## Self Host
```sh
$ git clone https://github.com/yashoswalyo/MERGE-BOT.git
$ cd MERGE-BOT
$ sudo apt-get install python3-pip ffmpeg
$ pip3 install -U pip
$ pip3 install -U -r requirements.txt
# <fill config.py correctly>
$ python3 bot.py
```

## License
```sh
MP3 Merge Bot, Telegram MP3 Merge Bot
Copyright (c) 2021 

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
```

## Credits

- [Me](https://github.com/thedkm) for [Nothing](https://github.com/thedkm/MP3-MERGE-BOT) 😬
- [Dan](https://github.com/delivrance) for [Pyrogram](https://github.com/pyrogram/pyrogram) ❤️
- [PropheC](https://github.com/akshettrj) for help in  fixing some stuff  ❤️
- [yashoswalyo](https://github.com/yashoswalyo) for [repo](https://github.com/yashoswalyo/MERGE-BOT) ❤️                                                                               

