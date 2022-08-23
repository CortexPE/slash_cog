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

import inspect
import typing
from logging import Logger

import discord
from discord.ext import commands
from docstring_parser import parse as parse_doc

from .api_constants import *


def param_annotation_to_discord_int(annotation: type) -> ApplicationCommandOptionType:
    if annotation == str or annotation == commands.clean_content:
        return ApplicationCommandOptionType.STRING
    elif annotation == int:
        return ApplicationCommandOptionType.INTEGER
    elif annotation == bool:
        return ApplicationCommandOptionType.BOOLEAN
    elif annotation == discord.user.User:
        return ApplicationCommandOptionType.USER
    elif annotation == discord.abc.GuildChannel:
        return ApplicationCommandOptionType.CHANNEL
    elif annotation == discord.Role:
        return ApplicationCommandOptionType.ROLE
    # elif False:
    #     return ApplicationCommandOptionType.MENTIONABLE
    elif annotation == float:
        return ApplicationCommandOptionType.NUMBER

    return ApplicationCommandOptionType.STRING  # fallback to string, discord.py will convert it


def index_callback_parameters(log: Logger, callback: callable) -> typing.List[dict]:
    options = []
    params = inspect.signature(callback).parameters  # type: typing.Mapping[str, inspect.Parameter]
    doc = parse_doc(callback.__doc__)
    i = 0
    for param_name, param in params.items():
        if param_name in ["self"]:
            continue
        i += 1
        if param_name in ["ctx", "cog"]:
            continue
        desc = doc.params[i - 1].description if len(doc.params) >= i else None
        if desc is None:
            log.warning(f"Undocumented argument {param.name} with type {param.annotation} on {callback.__name__}@{inspect.getabsfile(callback)}")
        options.append({
            "name": param.name,
            "description": desc or f"{param.name} argument",
            "type": param_annotation_to_discord_int(param.annotation),
            "required": param.default == param.empty
        })
    return options


async def get_owner_ids(bot: commands.Bot) -> typing.Set[int]:
    ids = set()
    if bot.owner_id:
        ids.add(bot.owner_id)
    elif bot.owner_ids:
        ids = ids.union(set(bot.owner_ids))
    else:
        app = await bot.application_info()  # type: ignore
        if app.team:
            ids = ids.union({m.id for m in app.team.members})
        else:
            ids.add(app.owner.id)
    return ids


async def index_command(log: Logger, bot: commands.Bot, cmd: commands.Command) -> typing.Optional[dict]:
    if cmd.hidden:
        return None

    def trunc(s: str, _l: int):
        if len(s) > _l:
            return s[:_l - 1] + "\N{HORIZONTAL ELLIPSIS}"
        return s

    cmd_data = {
        "name": cmd.name,
        "description": trunc(cmd.description or cmd.help or "Un-described command", 100).split("\n")[0],  # perhaps this needs to be truncated to < 100 chars
        "options": []
    }
    if isinstance(cmd, commands.Group):
        if len(cmd.commands) >= 25:
            log.error(f"Amount of subcommands for the group {cmd.name} exceeds 25 (discord limit)")
            return None
        for sub_cmd in cmd.commands:  # type: commands.Command
            sub_cmd_data = await index_command(log, bot, sub_cmd)
            if sub_cmd_data is None:
                continue
            cmd_data["options"].append(sub_cmd_data)

        if len(cmd_data["options"]) < 1:  # ignore empty subcommands
            return None

        return cmd_data

    for check in cmd.checks:
        # todo: use inspect.getclosurevars(check).nonlocals for *has_permissions instead of monkey patching...
        # print(check_vars, check_vars.globals.keys())
        # I still don't know how to get the wrapper's name or how to unwrap the predicate reee
        extra_data = check.__dict__.get("slash_extras", None)
        if extra_data is None:
            continue
        if "is_nsfw" in extra_data:
            cmd_data["nsfw"] = True
        if "is_owner" in extra_data:
            # todo: add some way to configure this behavior, to hide or permission-gate owner-only commands
            cmd_data["default_permission"] = False
            cmd_data["permissions"] = [
                {
                    "id": str(owr_id),
                    "type": ApplicationCommandPermissionType.USER,
                    "permission": True,
                } for owr_id in await get_owner_ids(bot)
            ]

    cmd_data["type"] = ApplicationCommandType.CHAT_INPUT
    if "default_permission" not in cmd_data:
        cmd_data["default_permission"] = True
    if "permissions" not in cmd_data:
        cmd_data["permissions"] = []
    cmd_data["options"] = index_callback_parameters(log, cmd.callback)

    return cmd_data
