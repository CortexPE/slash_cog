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

import logging
import typing
from datetime import datetime

import discord
from discord.ext import commands
from discord.http import Route
from discord.types.user import User as UserPayload

from . import InteractMessage, InteractContext, command_map, ApplicationCommandType


class SlashCommands(commands.Cog):
    # TODO: Map commands / subcommand parsing => callback with conversion support to prevent hackily faking a message
    SLASH_INVOKE_PREFIX = "/"

    def __init__(self, bot: commands.Bot):
        self.registered = set()
        self.bot = bot
        self.orig_prefix_callback = bot.get_prefix
        bot.get_prefix = self.get_prefix_wrapper

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

    def cog_unload(self):
        self.bot.get_prefix = self.orig_prefix_callback

    async def get_prefix_wrapper(self, msg: discord.Message) -> typing.Union[list, str]:
        if not isinstance(msg, InteractMessage):
            return await self.orig_prefix_callback(msg)
        return f"{self.SLASH_INVOKE_PREFIX}"

    async def generate_command_map(self, _commands: typing.Set[commands.Command] = None) -> typing.List[typing.Dict]:
        if _commands is None:
            _commands = self.bot.commands

        cmd_map = []
        for cmd in _commands:
            cmd_data = await command_map.index_command(self.bot, cmd)
            if cmd_data is None:
                continue
            cmd_map.append(cmd_data)
        return cmd_map

    async def register_commands(self, endpoint: str = "/", cmd_list: list = None) -> None:
        if cmd_list is None:
            cmd_list = await self.generate_command_map()

        self.logger.debug("Sending command list...")
        await self.__internal_ep_req("PUT", endpoint, cmd_list)
        self.registered.add(endpoint)
        self.logger.info(f"Registered {len(cmd_list)} top-level commands to {endpoint} !")

        # TODO: Check registered discord-side permissions, compare with permissions we've just registered,
        #  update discord-side if outdated

    async def unregister_commands(self, endpoint: str) -> None:
        self.logger.info(f"Unregistering commands ({endpoint})...")
        await self.__internal_ep_req("PUT", endpoint, [])

        try:
            self.registered.remove(endpoint)
        except KeyError:
            pass

    async def clear_commands(self) -> None:
        for endpoint in self.registered:
            await self.unregister_commands(endpoint)

    async def __internal_ep_req(self, method: str, endpoint: str, data: list = None, suffix: str = "") -> typing.Any:
        route = Route(method=method, path=f"/applications/{self.bot.application_id}{endpoint}/commands{suffix}")
        if data is not None:
            return await self.bot.http.request(route, json=data)
        else:
            return await self.bot.http.request(route)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        data = interaction.data
        if "type" not in data:
            return
        if data["type"] != ApplicationCommandType.CHAT_INPUT:
            return
        cmd = self.bot.get_command(data["name"])
        if cmd is None:
            return

        try:
            ch = self.bot.get_channel(interaction.channel.id) or await self.bot.fetch_channel(interaction.channel.id)
        except discord.HTTPException:
            return await interaction.response.send_message(
                "\N{WARNING SIGN} I cannot access the current channel you are on, please check permissions", ephemeral=True
            )
        if not isinstance(ch, (discord.TextChannel, discord.Thread, discord.DMChannel, discord.GroupChannel, discord.PartialMessageable)):
            return

        if not ch.permissions_for(ch.guild.me if ch.guild is not None else self.bot.user).read_messages:
            # somehow replying is possible even without perms based on my tests, cuz interactions use webhooks instead of actual channel messages,
            # but this might be unwanted behavior.
            return await interaction.response.send_message(
                "\N{WARNING SIGN} I cannot access the current channel you are on, please check permissions", ephemeral=True
            )

        args = []
        for opt in data.get("options", []):
            if opt.get("type", None) == ApplicationCommandType.CHAT_INPUT:
                args.append(opt["name"])
                for sub_opt in opt.get("options", []):  # type: dict
                    args.append(sub_opt["value"])
                continue
            args.append(opt["value"])

        user = interaction.user

        await interaction.response.defer()

        # fake message, invoke a command as the user
        ctx = await self.bot.get_context(cls=InteractContext, message=InteractMessage(channel=ch, data={
            "content": f"{self.SLASH_INVOKE_PREFIX}{data['name']} {' '.join(args)}".strip(),
            "author": UserPayload(id=user.id, username=user.name, discriminator=user.discriminator, avatar=None),
            "id": 0,
            "attachments": [],
            "embeds": [],
            "edited_timestamp": datetime.isoformat(datetime.utcnow()),
            "type": discord.MessageType.default,
            "pinned": False,
            "mention_everyone": False,
            "tts": False,
        }, state=self.bot._connection, parent_interaction=interaction))
        await self.bot.invoke(ctx)
