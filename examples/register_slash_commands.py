from discord.ext import commands

from slash_cog import SlashCommands


class RegisterSlashCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        cog = bot.get_cog("SlashCommands")
        if not isinstance(cog, SlashCommands):
            raise RuntimeError("Unable to find slash_cog extension")
        self.s_cog = cog  # type: SlashCommands
        self.bot.loop.create_task(self.wait_to_register())

    async def wait_to_register(self):
        await self.bot.wait_until_ready()

        # do not register commands as we are probably running on a separate instance
        if isinstance(self.bot, commands.AutoShardedBot):
            if 0 not in self.bot.shard_ids:
                return
        elif self.bot.shard_count > 1 and self.bot.shard_id != 0:
            return

        # Filter the commands to only show non-hidden commands, then only show hidden commands on one specific guild
        # shown_commands = await self.s_cog.generate_command_map(set(filter(lambda c: not c.hidden, self.bot.commands)))
        # GLOBAL COMMANDS: await self.s_cog.register_commands("/", shown_commands)

        hidden_commands = await self.s_cog.generate_command_map(set(filter(lambda c: c.hidden, self.bot.commands)))
        await self.s_cog.register_commands("/guilds/123456789123456789", hidden_commands)

    # OPTIONAL:
    # def cog_unload(self):
    #     self.bot.loop.create_task(self.s_cog.unregister_commands("/guilds/123456789123456789"))
    #     OR:
    #     self.bot.loop.create_task(self.s_cog.clear_commands())


def setup(bot: commands.Bot):
    bot.add_cog(RegisterSlashCommands(bot))
