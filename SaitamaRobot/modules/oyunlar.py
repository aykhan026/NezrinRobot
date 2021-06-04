from telethon.tl.types import InputMediaDice

from SaitamaRobot.events import register


@register(pattern="^/zer(?: |$)(.*)")
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


@register(pattern="^/ox(?: |$)(.*)")
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


@register(pattern="^/basket(?: |$)(.*)")
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
 *Şansını yoxla* 😉
  - `/zer` 🎲 Bir zər at
  - `/ox` 🎯 Bir ox at
  - `/basket` 🏀 Bir basket at

"""

__mod_name__ = "🎮Oyunlar"
