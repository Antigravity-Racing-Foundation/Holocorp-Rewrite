# Holocorp Rewrite
AGRF's Favorite Bot, but Better!
## What is this?
Holocorp Overview is a custom Discord bot written for the [AGRF Discord server](https://discord.gg/cBeSdgXs9X). Having started as a simple interface for displaying the API status in a friendly format, the project grew to be a useful tool for several other applications, and has now been re-written and open-sourced.
### Features
- Real-time API status listing:
    * Displays the player count of the entire backend;
    * Displays ongoing lobbies in WipEout HD and WipEout Pulse, including all the information available in-game and more!
    * Customization options available for the lobby listing;
- Backend status reporting - see at a glance if Thallium+Beat is down or under maintenance, with staff being able to set arbitrary reasons in the status message (See `Backend status listing` section);
- Randomization tools for event generation:
    * Ability to generate a full list of weekly events with a single command (for ZGR Weekly Time Trials, `/generate_events`);
    * Ability to generate a track or a list of tracks with customization of the track pool (`/gimme_a_track`);
- Two chatbot capability implementations (`/reply_control`):
    * Dumb replies - get random phrases from a pool or rig the game by setting the next reply;
    * LLM-powered replies (OpenAI interface implementation), with a powerful and robust databank system planned for rich and token-efficient lore knowledge!
## Configuration
Configuration data and resources are located in the `external` directory:
```
external
├── config.json
├── databank
│   ├── databank.db
│   └── databank_schema.sql
├── llm_resources
│   ├── example_messages.json
│   ├── system_message.md
│   └── system_message.md.bak
├── message_templates
│   ├── event_gen_template.md
│   ├── lobby_formats
│   │   ├── block_templates
│   │   │   ├── hd_eliminator.md
│   │   │   ├── hd_single_race.md
│   │   │   ├── hd_tournament.md
│   │   │   ├── hd_zone_battle.md
│   │   │   ├── pulse_single_race.md
│   │   │   └── pulse_tournament.md
│   │   ├── elements.json
│   │   ├── player_entry_hd.md
│   │   └── player_entry_pulse.md
│   ├── ping_reply_list.md
│   ├── status_failure.md
│   ├── status_maintenance.md
│   ├── status_maintenance_with_reason.md
│   ├── status_offline.md
│   ├── status_offline_with_reason.md
│   ├── status_online.md
│   ├── status_standby.md
│   └── status_standby_with_reason.md
└── secrets
    ├── credentials.txt
    ├── credentials.txt.prod
    └── oai_credentialss.txt
```
- `config.json` contains the bot's configuration options. If it is not present on startup, it will be created using the default values defined in `io_handler` -> `configInitial` (class) and execution will be stopped;
- `databank` contains the files used by the LLM lore databank function (the database and the database schema).
- `llm_resources` contains the system message and the example messages used by the LLM in the LLM replies chatbot mode. `system_message.md` doesn't require special formatting and is treated as a plain text file; `example_messages.json` must follow the correct structure (an example of which is included in the respective file in this repository);
- `message_templates` contains various templates for the bot's output:
    * `lobby_formats` contains the templates used by the backend status reporting feature. See `Backend status listing` section for more details.
    * `ping_reply_list.md` is the random reply pool used by the dumb reply chatbot mode. Messages are separated using `|||` for newline support.
    * `status_*.md` are files used by the bot to display the backend status. `!PLAYERCOUNT` and `!LOBBYLISTING` keywords are supported by `status_online.md` and will be replaced with the respective values when displayed.
    * `status_*_with_reason.md` are files used by the bot when a status reason is specified by staff. It supports the `!REASON` keyword which will be replaced with the specified reason when displayed. Each status has a `with_reason` variant, except for `status_online.md`.
    * `event_gen_template.md` is the template used for ZGR Weekly Time Trial event list generation. It supports numerous keywords that are replaced with their respective values (see Event generation keywords section).
- `secrets` contains various API keys and client tokens. Files must contain just the secret with no newlines. Specific file names are requested by the program at runtime. In the current implementation, the program requests:
    * `credentials.txt`, which contains the Discord client token (must be present);
    * `oai_credentials.txt`, which contains the OpenAI API key (if not present, LLM features will be disabled.)
### Event generation keywords
- `!PING`: <@ZGR Tournaments> Discord role ID as specified by `config.json` -> `zgrRolePing`; 
- `!YEAR`: current year;
- `!WEEK`: current week;
- `!DEADLINE`: time left until the end of the current week 
    * Note: all time-related keywords use the host system's timezone;
- `!TRACK2048`: a random track from WipEout 2048's track roster.
- `!SHIP2048`: a random ship from WipEout 2048's ship roster.
- `!CLASS2048`: a random speed class available in WipEout 2048.
- `!TRACKHD`: a random track from WipEout HD's track roster, excluding Zone-specific tracks.
- `!ZONEHD`: a random track from WipEout HD's track roster, including Zone-specific tracks.
- `!SHIPHD`: a random ship from WipEout HD's ship roster.
- `!CLASSHD`: a random speed class available in WipEout HD.
- Notes: 
    * Each keyword will be replaced by a unique random value (e.g. "!ZONEHD !ZONEHD" = "Syncopia Mallavol"); 
    * Each keyword may only be used the maximum of 24 times; 
    * Keywords not specified here or encountered after exceeding the maximum use count will be left intact.
### Backend status listing
Backend status lising uses information fetched from a REST API (presumably, the Thallium+Beat API) to format and present current inforamtion about players and lobbies in a Discord channel.
This feature, besides the `apiLobbiesURL` and `apiPlayersURL` elements of `config.json`, utilizes various templates and elements defined in the `external/message_temapltes/lobby_formats` directory:
- `elements.json` contains elements such as separators and progress indicator strings;
- `hd_[mode].md` and `pulse_[mode].md` define how the final lobby listing blocks will look, replacing !RawValue and @Processed keywords with the appropriate information:
    * !RawValue keys begin with an exlamation mark and are replaced with raw values from the input array, hence a key's name must match the name of a value in the array passed to the lobby assembler function. As the assembler is expected to use the output of the `xmlToValues` function, the up-to-date structure of the array may be viewed in the code for said function.
    * @Processed keys begin with an "at" symbol and are replaced with strings that must've been processed earlier such as weapon lists, player lists or additional lobby property lists. The processed keys that will be replaced with their respective values are @Weapons, @PlayerList, @Progress and @AdditionalProperties (depending on the game; if a key isn't applicable, it won't be replaced.)
- `player_entry_hd.md` and `player_entry_pulse.md` define the patterns for lobbies' player lists, with !Name, !Platform and !Region keywords getting replaced with the appropriate information.
## How to run
1. `$ git clone https://github.com/Antigravity-Racing-Foundation/Holocorp-Rewrite.git`;
2. Provide the required `secrets` (see Configuration -> `secrets`);
3. Run `$ python ./holocorp.py`;
4. Containerize to taste (Podman is used by the AGRF but instructions won't be provided in this document.)
## Should I run it, though?
Not really, since this bot has been purpose-built for the [AGRF Discord server's](https://discord.gg/cBeSdgXs9X) needs. This repository exists mostly for educational purposes only. However, you are free to reuse code from here as per this repository's license, open issues and submit pull requests.