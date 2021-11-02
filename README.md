# discord.py `/slash` cog
**A drop-in vanilla discord.py cog that acts as a translation layer to add slash command support with little to no code modifications, no forks needed**

![PyPI - License](https://img.shields.io/pypi/l/slash_cog) ![PyPI](https://img.shields.io/pypi/v/slash_cog) ![PyPI - Status](https://img.shields.io/pypi/status/slash_cog) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/slash_cog)

### Features:

 - Automatically generates a command map with argument listing for the entire bot
 - Wraps around existing discord.py `Context`, almost no code modifications needed
 - Automatic Multi-Instance bot detection (currently, it will only register if there is no shards or the bot runs *shard `0`*)

### General TO-DOs & RFCs:

 - [ ] Make the cog more modular in order to support more customizations
 - [ ] Allow registering guild-specific commands
 - [ ] Allow preventing the cog from automatically registering global commands

### Unsupported Features (Unsupported by Discord):

 - [ ] Translation for Custom checks
 - [ ] Translation for `@commands.check_any()`
 - [ ] `is_owner` (commands currently hidden)
 - [ ] `is_nsfw` (commands currently hidden)
 - [ ] `*has_permissions` (only roles and user IDs are accepted)
 - [ ] `bot_has_(any)?_role`
 - [ ] `guild_only`
 - [ ] `dm_only`

### Fork Support:
I personally won't provide support for forks as for simplicity's sake I will be basing this cog on [Rapptz/discord.py `master` v2.0.0a](https://github.com/Rapptz/discord.py/tree/master). However, fork-specific pull requests are allowed.

A word though, because everyone is making their own forks of discord.py, I would suggest changing up the readme to include what changes and features the fork has added apart from API parity and maintenance just to make everybody's lives easier.

### Usage:
Simply install the pip package with:
```shell script
pip install -U slash_cog
```

Then in your bot's cog loader, load the cog (**CRITICAL:** Load it as the first extension as the cog needs to monkey patch command checks):
```python
bot.load_extension("slash_cog")
```

---
#### P.S. If this project / POC has been useful [sponsor me](https://www.patreon.com/CortexPE) pls, iambroke