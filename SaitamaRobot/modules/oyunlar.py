from telethon.tl.types import InputMediaDice

from SaitamaRobot.events import register


@register(pattern="^/dice(?: |$)(.*)")
async def _(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1)
    r = await event.reply(file=InputMediaDice(""))
    input_int = int(input_str)
    if input_int > 6:
        await event.reply("Yalnız 1-dən 6-dək bir rəqəm yaza bilərsiniz")
    
    else:
        try:
            required_number = input_int
            while r.media.value != required_number:
                await r.delete()
                r = await event.reply(file=InputMediaDice(""))
        except BaseException:
            pass


@register(pattern="^/dart(?: |$)(.*)")
async def _(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1)
    r = await event.reply(file=InputMediaDice("🎯"))
    input_int = int(input_str)
    if input_int > 6:
        await event.reply("Yalnız 1-dən 6-dək bir rəqəm yaza bilərsiniz")
    
    else:
        try:
            required_number = input_int
            while r.media.value != required_number:
                await r.delete()
                r = await event.reply(file=InputMediaDice("🎯"))
        except BaseException:
            pass


@register(pattern="^/ball(?: |$)(.*)")
async def _(event):
    if event.fwd_from:
        return
    input_str = event.pattern_match.group(1)
    r = await event.reply(file=InputMediaDice("🏀"))
    input_int = int(input_str)
    if input_int > 5:
        await event.reply("Yalnız 1-dən 6-dək bir rəqəm yaza bilərsiniz")
    
    else:
        try:
            required_number = input_int
            while r.media.value != required_number:
                await r.delete()
                r = await event.reply(file=InputMediaDice("🏀"))
        except BaseException:
            pass



__help__ = """
 *Play Game With Emojis:*
  - /dice or /dice 1 to 6 any value
  - /ball or /ball 1 to 5 any value
  - /dart or /dart 1 to 6 any value
 Usage: hahaha just a magic.
 warning: you would be in trouble if you input any other value than mentioned.
"""

__mod_name__ = "Game"
