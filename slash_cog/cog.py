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

from . import InteractMessage, InteractContext, command_map

import typing
from datetime import datetime

import discord
from discord.ext import commands
from discord.http import Route

from discord.types.user import User as UserPayload


class SlashCommands(commands.Cog):
    # TODO: Map commands / subcommand parsing => callback with conversion support to prevent hackily faking a message
    SLASH_INVOKE_PREFIX = "\N{ZERO WIDTH SPACE}"

    def __init__(self, bot: commands.Bot):
        self.registered = []
        self.bot = bot
        self.orig_prefix_callback = bot.get_prefix
        bot.get_prefix = self.get_prefix_wrapper

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        bot.loop.create_task(self.wait_to_register())

    async def get_prefix_wrapper(self, msg: discord.Message) -> typing.Union[list, str]:
        if not isinstance(msg, InteractMessage):
            return await self.orig_prefix_callback(msg)
        return f"{self.SLASH_INVOKE_PREFIX}/"

    async def wait_to_register(self):
        await self.bot.wait_until_ready()

        if isinstance(self.bot, commands.AutoShardedBot):
            if 0 not in self.bot.shard_ids:  # do not register commands as we are probably running on a separate instance
                return
        elif self.bot.shard_count > 1 and self.bot.shard_id != 0:
            return

        to_send = await self.generate_command_map()
        self.logger.debug("Sending command list...")
        # print(json.dumps(to_send, indent=4))
        await self.register_commands("/", to_send)
        self.logger.info(f"Registered {len(to_send)} top-level commands!")
        # todo: guild-specific commands, refactor this registration code to allow flexible registration
        # await self.register_commands("/guilds/123456789123456789", to_send)

    async def generate_command_map(self) -> typing.List[typing.Dict]:
        cmd_map = []
        for cmd in self.bot.commands:  # type: commands.Command
            cmd_data = await command_map.index_command(self.bot, cmd)
            if cmd_data is None:
                continue
            cmd_map.append(cmd_data)
        return cmd_map

    async def register_commands(self, endpoint: str, cmd_list: list):
        await self.bot.http.request(Route(
            method="PUT", path=f"/applications/{self.bot.application_id}{endpoint}/commands"
        ), json=cmd_list)
        self.registered.append(endpoint)

    def cog_unload(self):
        async def clear_commands():
            self.logger.info(f"Unregistering commands...")
            for endpoint in self.registered:
                await self.bot.http.request(Route(
                    method="PUT", path=f"/applications/{self.bot.application_id}{endpoint}/commands"
                ), json=[])
            self.registered = []

        self.bot.loop.create_task(clear_commands())
        self.bot.get_prefix = self.orig_prefix_callback

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        data = interaction.data
        if "type" not in data:
            return
        if data["type"] != 1:  # chat input cmd type
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
            if opt.get("type", None) == 1:  # chat input cmd type
                args.append(opt["name"])
                for sub_opt in opt.get("options", []):  # type: dict
                    args.append(sub_opt["value"])
                continue
            args.append(opt["value"])

        user = interaction.user

        await interaction.response.defer()

        # fake message, invoke a command as the user
        ctx = await self.bot.get_context(cls=InteractContext, message=InteractMessage(channel=ch, data={
            "content": f"{self.SLASH_INVOKE_PREFIX}/{data['name']} {' '.join(args)}".strip(),
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
