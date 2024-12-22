# Holocorp Rewrite
AGRF's Favorite Bot, but Better!
## What is this?
The Thallium+Beat projects provides an API which returns the current lobby listing and player count in the XML format. Holocorp Overview fetches and parses these XML files to display them in a friendly format over in the #online-status channel in our [Discord server](https://discord.gg/cBeSdgXs9X).
## How does it work?
The bot pulls configuration data from the `external` directory. 
- `credentials.txt` contains the API key with no newlines or other characters;
- `config.json` contains configuration data for the bot and the initial config file is created upon first start;
- Finally, `holocorp.workspace` is the cache file for the bot which is initialized upon each startup. 

Run `holocorp.py` and it will ask you to fill the `config.json` file before exiting. Supply the `credentials.txt` file.
## Should I use Holocorp Overview on my server?
Not really. This Git repository exists mostly for educational purposes only. You are free to reuse code from here, open issues and submit pull requests, however.
