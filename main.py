import os
import discord
from discord.ext import commands
import subprocess
import aiohttp
import tempfile

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Bot đã online: {bot.user}")

@bot.command(name="piano")
async def transcribe(ctx):
    """Transcribe file audio piano đính kèm thành MIDI"""
    if not ctx.message.attachments:
        await ctx.send("🎹 Vui lòng đính kèm file audio piano (.mp3, .wav, .flac) cùng lệnh `!piano`")
        return
    
    attachment = ctx.message.attachments[0]
    ext = os.path.splitext(attachment.filename)[1].lower()
    
    if ext not in ['.mp3', '.wav', '.flac', '.ogg']:
        await ctx.send("❌ Định dạng không hỗ trợ. Chỉ nhận: .mp3, .wav, .flac, .ogg")
        return
    
    await ctx.send("⏳ Đang xử lý audio với TransKun... (có thể mất 30-60 giây)")
    
    try:
        # Tải file về
        async with aiohttp.ClientSession() as session:
            async with session.get(attachment.url) as resp:
                if resp.status != 200:
                    await ctx.send("❌ Không tải được file.")
                    return
                
                with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp_in:
                    tmp_in.write(await resp.read())
                    input_path = tmp_in.name
        
        output_path = input_path + ".mid"
        
        # Chạy TransKun
        result = subprocess.run(
            ["transkun", input_path, output_path, "--device", "cpu"],
            capture_output=True,
            text=True,
            timeout=300  # 5 phút timeout
        )
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            await ctx.send("✅ Transcribe xong! Đây là file MIDI của bạn:", 
                          file=discord.File(output_path, filename="transcribed.mid"))
        else:
            await ctx.send(f"❌ TransKun lỗi:\n```{result.stderr[:1500]}```")
        
    except subprocess.TimeoutExpired:
        await ctx.send("⏱️ Quá thời gian xử lý. File có thể quá dài.")
    except Exception as e:
        await ctx.send(f"❌ Lỗi: {str(e)[:1000]}")
    finally:
        # Dọn dẹp file tạm
        for p in [input_path, output_path]:
            if 'p' in locals() and os.path.exists(p):
                os.remove(p)

# Lệnh ping kiểm tra bot
@bot.command()
async def ping(ctx):
    await ctx.send(f"🏓 Pong! Latency: {round(bot.latency * 1000)}ms")

if __name__ == "__main__":
    bot.run(os.environ["DISCORD_TOKEN"])
