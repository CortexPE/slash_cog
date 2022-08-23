"""
MIT License

Copyright (c) 2021-Present CortexPE

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from discord.ext import commands
from discord.ext.commands import Bot

from slash_cog.api_constants import *
from slash_cog.cog import SlashCommands
from slash_cog.command_map import index_command
from slash_cog.context import InteractContext
from slash_cog.decorator import inject_extracted


async def setup(bot: Bot):
    checks = [
        "bot_has_guild_permissions", "has_guild_permissions",
        "bot_has_permissions", "has_permissions",
        "bot_has_any_role", "has_any_role",
        "bot_has_role", "has_role",
        "is_nsfw",
        "is_owner",
        "guild_only", "dm_only",
    ]
    for check_name in checks:
        setattr(commands, check_name, inject_extracted(getattr(commands, check_name)))
    await bot.add_cog(SlashCommands(bot))
