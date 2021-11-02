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
import discord


class InteractContext(commands.Context):
    """Wrapper around InteractionRespone"""

    def __init__(self, **attrs):
        super().__init__(**attrs)
        self.parent_interaction = self.message.parent_interaction  # type: discord.Interaction
        self.response = discord.InteractionResponse(self.message.parent_interaction)

    async def send(self, *args, **kwargs):
        delete_after = None
        if "delete_after" in kwargs:
            delete_after = kwargs["delete_after"]
            kwargs.pop("delete_after")
        # if not self.response.is_done() and False:
        #     await self.response.send_message(ephemeral=False, *args, **kwargs)
        # else:
        await self.parent_interaction.followup.send(*args, **kwargs)
        msg = await self.parent_interaction.original_message()

        if delete_after is not None:
            await msg.delete(delay=delete_after)

        return msg

    async def reply(self, *args, **kwargs):
        if "mention_author" in kwargs:
            kwargs.pop("mention_author")
        return await self.send(*args, **kwargs)
