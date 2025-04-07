import discord
import random
from discord.ext import commands
from discord import app_commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
from datetime import datetime, timedelta, timezone
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_ID = 1340815073748189204  # Replace with your channel ID
EMBED_MESSAGE_ID = 123456789012345678  # Replace with actual message ID from /embed

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

moon_phases = [
    ("🌑 New Moon", 20),
    ("🌒 Waxing Crescent", 15),
    ("🌓 First Quarter", 10),
    ("🌔 Waxing Gibbous", 10),
    ("🌕 Full Moon", 2),
    ("🌖 Waning Gibbous", 10),
    ("🌗 Last Quarter", 10),
    ("🌘 Waning Crescent", 15)
]

weather_by_season = {
    "spring": [
        ("🌧️ Light Rain", "A steady drizzle dampens the earth and silences the wind."),
        ("☁️ Overcast", "The sky is cloaked in a heavy layer of grey, muting the daylight."),
        ("🌥️ Cloudy", "The sun is veiled, casting the world in muted tones."),
        ("🌬️ Windy", "Cold gusts sweep through the trees, stirring dead leaves."),
        ("🌫️ Drizzle", "A faint mist clings to surfaces, chilling to the bone."),
        ("🌫️ Fog", "A thick mist blankets the ground, distorting sight and sound."),
        ("🌌 Clear Skies", "The air is still, and the sky is unbroken by cloud."),
    ],
    "summer": [
        ("🌌 Clear Skies", "The air is still, and the sky is unbroken by cloud."),
        ("🌧️ Light Rain", "A steady drizzle dampens the earth and silences the wind."),
        ("🌥️ Cloudy", "The sun is veiled, casting the world in muted tones."),
        ("☁️ Overcast", "The sky is cloaked in a heavy layer of grey, muting the daylight."),
        ("🌬️ Windy", "Warm gusts stir dry leaves along the roads."),
        ("⛈️ Thunderstorm", "Distant thunder rolls beneath dark, swollen clouds."),
    ],
    "autumn": [
        ("🌫️ Fog", "A thick mist blankets the ground, distorting sight and sound."),
        ("🌧️ Light Rain", "A steady drizzle dampens the earth and silences the wind."),
        ("🌥️ Cloudy", "The sun is veiled, casting the world in muted tones."),
        ("☁️ Overcast", "The sky is cloaked in a heavy layer of grey, muting the daylight."),
        ("🌬️ Windy", "Cold gusts sweep through the trees, stirring dead leaves."),
        ("🌫️ Drizzle", "A faint mist clings to surfaces, chilling to the bone."),
        ("🌌 Clear Skies", "The air is still, and the sky is unbroken by cloud."),
    ],
    "winter": [
        ("🌨️ Light Snow", "Snowflakes drift quietly down, cloaking the world in white."),
        ("🌧️ Heavy Rain", "Relentless rainfall hammers rooftops and fills the streets."),
        ("🌧️ Light Rain", "A steady drizzle dampens the earth and silences the wind."),
        ("☁️ Overcast", "The sky is cloaked in a heavy layer of grey, muting the daylight."),
        ("🌫️ Fog", "A thick mist blankets the ground, distorting sight and sound."),
        ("🌬️ Windy", "Freezing gusts cut through the silence."),
    ],
}

magical_surge_events = [
    ("🩸 Magical Surge Detected", "Residual dark energy pulses beneath the surface. Witches who choose to channel this surge may gain **+1 Prestige** through direct connection to the surge."),
    ("🔥 Ley Lines Unstable", "Localized fluctuations in power suggest a shift in arcane flow. Witches may attune to this instability and absorb its force to gain **+1 Prestige**."),
    ("🕯️ Ancestral Disturbance", "Whispers echo from the Other Side. Ancestral magic is agitated. Witches in tune with ancestral magic may draw on it for **+1 Prestige**."),
    ("🌑 Veil Weakening", "The boundary between life and death feels thinner than usual. Witches daring enough to tap into this thinning veil can claim **+1 Prestige**."),
]

def weighted_choice(choices):
    total = sum(weight for _, weight in choices)
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
        if upto + weight >= r:
            return choice
        upto += weight

def get_current_season():
    month = datetime.now(timezone.utc).month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

def get_next_midnight_timestamp():
    now = datetime.now(timezone.utc)
    next_midnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return int(next_midnight.timestamp())

async def build_forecast_embed():
    season = get_current_season()
    weather, description = random.choice(weather_by_season[season])
    moon = weighted_choice(moon_phases)

    embed = discord.Embed(
        title="⛅ Daily Weather Forecast",
        description=f"{weather}  —  *{description}*",
        color=0x1c1c1c
    )

    embed.add_field(name="🌙 Moon Phase", value=moon, inline=False)

    if random.random() < 0.10:
        surge_title, surge_description = random.choice(magical_surge_events)
        embed.add_field(name=surge_title, value=surge_description, inline=False)

    embed.set_thumbnail(url="https://i.imgur.com/WxNkKkP.png")
    embed.set_footer(text=f"Next forecast: <t:{get_next_midnight_timestamp()}:F>")
    return embed

async def update_weather_embed():
    channel = bot.get_channel(CHANNEL_ID)
    try:
        message = await channel.fetch_message(EMBED_MESSAGE_ID)
        embed = await build_forecast_embed()
        await message.edit(embed=embed)
    except Exception as e:
        print(f"Failed to update embed: {e}")

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(f"Slash command sync failed: {e}")

    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: asyncio.create_task(update_weather_embed()), 'cron', hour=0, minute=0)
    scheduler.start()

@tree.command(name="weather", description="Force update the weather embed.")
@app_commands.checks.has_permissions(administrator=True)
async def weather(interaction: discord.Interaction):
    await update_weather_embed()
    await interaction.response.send_message("🌒 Forecast embed updated.", ephemeral=True)

@tree.command(name="embed", description="Send the first forecast embed manually.")
@app_commands.checks.has_permissions(administrator=True)
async def embed(interaction: discord.Interaction):
    channel = interaction.channel
    embed = await build_forecast_embed()
    message = await channel.send(embed=embed)
    await interaction.response.send_message(f"📩 Embed sent! Set `EMBED_MESSAGE_ID = {message.id}` in your code.", ephemeral=True)

bot.run(TOKEN)
