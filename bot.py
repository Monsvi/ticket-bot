import discord
from discord import ui, app_commands
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

class TicketBot(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        self.add_view(TicketView()) 
        await self.tree.sync()

bot = TicketBot()


class TicketView(ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @ui.button(label="📩 Open Ticket", style=discord.ButtonStyle.green, custom_id="open_ticket")
    async def open_ticket(self, interaction: discord.Interaction, button: ui.Button):
        await create_ticket(interaction)

async def create_ticket(interaction: discord.Interaction):
    guild = interaction.guild
    member = interaction.user


    category = discord.utils.get(guild.categories, name="📂 Tickets")
    if not category:
        category = await guild.create_category("📂 Tickets")

  
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(read_messages=False),
        member: discord.PermissionOverwrite(read_messages=True, send_messages=True, view_channel=True),
    }

    ticket_channel = await category.create_text_channel(
        f"ticket-{member.name}", 
        overwrites=overwrites
    )

    embed = discord.Embed(
        title="🎟️ Support Ticket",
        description=f"**User:** {member.mention}\n**Opened at:** {discord.utils.format_dt(datetime.now())}\n\nHow can we help you today?",
        color=discord.Color.blurple()
    )

    await ticket_channel.send(embed=embed, view=TicketManagementView(ticket_channel, member))
    
    await interaction.response.send_message(
        f"✅ Your ticket has been created! {ticket_channel.mention}", 
        ephemeral=True
    )


class TicketManagementView(ui.View):
    def __init__(self, channel: discord.TextChannel, owner: discord.Member):
        super().__init__(timeout=None)
        self.channel = channel
        self.owner = owner

    @ui.button(label="🔒 Close Ticket", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: ui.Button):
        if not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ You don't have permission to close tickets.", ephemeral=True)

        await interaction.response.defer()

        
        transcript_file = await create_transcript(self.channel)

      
        log_channel = discord.utils.get(interaction.guild.text_channels, name="ticket-logs")
        if log_channel:
            await log_channel.send(
                f"📝 Ticket closed by {interaction.user.mention}\n**Ticket:** {self.channel.name}",
                file=transcript_file
            )

        await self.channel.delete()

async def create_transcript(channel: discord.TextChannel):
    messages = [msg async for msg in channel.history(limit=1000, oldest_first=True)]
    
    content = f"Transcript for {channel.name}\n{'='*50}\n\n"
    for msg in messages:
        content += f"[{msg.created_at.strftime('%Y-%m-%d %H:%M:%S')}] {msg.author}: {msg.content}\n"
    
    filename = f"{channel.name}-transcript.txt"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    
    return discord.File(filename)

# ====================== SETUP COMMAND ======================
@bot.tree.command(name="setup", description="Create the ticket opening panel")
@app_commands.default_permissions(administrator=True)
async def setup(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Support System",
        description="Click the button below to open a support ticket.\nOur team will help you as soon as possible.",
        color=discord.Color.green()
    )
    await interaction.channel.send(embed=embed, view=TicketView())
    await interaction.response.send_message("✅ Ticket panel has been created!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"✅ {bot.user} is online and ready!")

bot.run(os.getenv("TOKEN"))