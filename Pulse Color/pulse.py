import disnake,webcolors,asyncio
from disnake.ext import commands
from disnake import Embed, File
from config import TOKEN
from PIL import Image, ImageDraw,ImageFont
from io import BytesIO

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def get_lighter_shade(rgb, increase_factor=50):
    r, g, b = rgb
    r = int(min(255, r + increase_factor))
    g = int(min(255, g + increase_factor))
    b = int(min(255, b + increase_factor))
    return f"#{r:02x}{g:02x}{b:02x}"

def get_darker_shade(rgb, decrease_factor=50):
    r, g, b = rgb
    r = int(max(0, r - decrease_factor))
    g = int(max(0, g - decrease_factor))
    b = int(max(0, b - decrease_factor))
    return f"#{r:02x}{g:02x}{b:02x}"

# Utility functions: hex_to_rgb, get_lighter_shade, get_darker_shade

def create_color_shades_image(base_color_hex, lighter_shade_hex, darker_shade_hex):
    width, height = 50, 50  # Smaller size for each color box
    image = Image.new("RGB", (width * 3, height), "white")
    draw = ImageDraw.Draw(image)

    draw.rectangle([0, 0, width, height], fill=base_color_hex)
    draw.rectangle([width, 0, width * 2, height], fill=lighter_shade_hex)
    draw.rectangle([width * 2, 0, width * 3, height], fill=darker_shade_hex)

    image_bytes = BytesIO()
    image.save(image_bytes, format='PNG')
    image_bytes.seek(0)
    return image_bytes


intents = disnake.Intents.all()
bot = commands.Bot(command_prefix="/", intents=intents)

# Dictionary to store users who have changed their color
user_color_change = {}
log_channel_id = None

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print(f"Bot is ready: {bot.user.name}")

    funny_status = "/help | Report any Issues to @parthynextdoor"
    truncated_status = (funny_status[:46] + "...") if len(funny_status) > 49 else funny_status
    await bot.change_presence(activity=disnake.Activity(type=disnake.ActivityType.listening, name=truncated_status))

@bot.slash_command()
async def help(ctx):
    embed = Embed(title="Help: Commands List", description="Explore the available commands and learn how to use them.", color=disnake.Color.blue())
    
    commands_description = (
        "**/colorchange [color name or hex code]**\n"
        "- Change your role color.\n"
        "- **Example**: `/colorchange cyan` or `/colorchange #123abc`\n"
        "- Note: Color can be changed only once.\n\n"
        
        "**/color [color name]**\n"
        "- Fetch hex value and shades of a color.\n"
        "- **Example**: `/color lavender`\n\n"
        
        "**/reset [user]**\n"
        "- Admin-only. Resets a user's color change limit.\n"
        "- **Example**: `/reset @username`\n\n"
        
        "**/setlogchannel [channel]**\n"
        "- Admin-only. Set a channel for logging bot activities.\n"
        "- **Example**: `/setlogchannel #logs`\n\n"
        
        "**/admincolorchange [user] [color]**\n"
        "- Admin-only. Change color for another user.\n"
        "- **Example**: `/admincolorchange @user blue`"
    )
    
    embed.description = commands_description
    await ctx.send(embed=embed)


@bot.slash_command()
async def setlog(ctx, channel: disnake.TextChannel):
    global log_channel_id
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You must be an admin to run this command.", ephemeral=True)
        return
    log_channel_id = channel.id
    await ctx.send(f"Log channel set to {channel.mention}", ephemeral=True)

async def send_log(message):
    if log_channel_id:
        channel = bot.get_channel(log_channel_id)
        if channel:
            await channel.send(message)



# Generate a list of valid color names
valid_color_names = list(webcolors.CSS3_HEX_TO_NAMES.values())

@bot.slash_command()
async def colorchange(ctx, color_input: str):
    user_id = ctx.author.id
    if user_id in user_color_change and user_color_change[user_id]:
        await ctx.send("You can only change your color once.", ephemeral=True)
        return

    color_input = color_input.lower().strip()
    role_name = None
    color = None

    if color_input in valid_color_names:
        role_name = f"{color_input.capitalize()}"
        rgb = webcolors.name_to_rgb(color_input)
        color = disnake.Color.from_rgb(*rgb)
    elif color_input.startswith("#"):
        try:
            role_name = f"{color_input.upper()}"
            rgb = webcolors.hex_to_rgb(color_input)
            color = disnake.Color.from_rgb(*rgb)
        except ValueError:
            await ctx.send("Invalid hex code. Please enter a valid one.", ephemeral=True)
            return
    else:
        await ctx.send(f"No color found for the name: {color_input}", ephemeral=True)
        return

    role_exists = disnake.utils.get(ctx.guild.roles, name=role_name)
    if not role_exists:
        role = await ctx.guild.create_role(name=role_name, color=color)
        await role.edit(position=1) # Position can be adjusted as needed
        await ctx.send(f"Role {role_name} has been created.", ephemeral=True)
    else:
        role = role_exists

    await ctx.author.add_roles(role)
    await ctx.send(f"You have been added to the role {role_name}.", ephemeral=True)
    user_color_change[user_id] = True

    # Log the color change
    await send_log(f"{ctx.author} changed their color to {role_name} using /colorchange")


@bot.slash_command()
async def admincolorchange(ctx, member: disnake.Member, color_input: str):
    if not ctx.author.guild_permissions.administrator:
        await ctx.send("You must be an admin to run this command.", ephemeral=True)
        return

    color_input = color_input.lower().strip()
    role_name = None
    color = None

    if color_input in valid_color_names:
        role_name = f"{color_input.capitalize()}"
        rgb = webcolors.name_to_rgb(color_input)
        color = disnake.Color.from_rgb(*rgb)
    elif color_input.startswith("#"):
        try:
            role_name = f"{color_input.upper()}"
            rgb = webcolors.hex_to_rgb(color_input)
            color = disnake.Color.from_rgb(*rgb)
        except ValueError:
            await ctx.send("Invalid hex code. Please enter a valid one.", ephemeral=True)
            return

    role_exists = disnake.utils.get(ctx.guild.roles, name=role_name)
    if not role_exists:
        role = await ctx.guild.create_role(name=role_name, color=color)
        await role.edit(position=1)
        await ctx.send(f"Role {role_name} has been created for {member.display_name}.", ephemeral=True)
    else:
        role = role_exists

    await member.add_roles(role)
    await ctx.send(f"{member.display_name} has been added to the role {role_name}.", ephemeral=True)

    # Log the admin color change
    await send_log(f"{ctx.author} (Admin) changed the color of {member.display_name} to {role_name} using /admincolorchange")

@bot.slash_command()
async def color(ctx, color_name):
    try:
        base_color_hex = webcolors.name_to_hex(color_name)
    except ValueError:
        await ctx.send(f"No color found for the name: {color_name}", ephemeral=True)
        return

    base_color_rgb = hex_to_rgb(base_color_hex)
    lighter_shade_hex = get_lighter_shade(base_color_rgb)
    darker_shade_hex = get_darker_shade(base_color_rgb)

    color_image = create_color_shades_image(base_color_hex, lighter_shade_hex, darker_shade_hex)

    embed = Embed(title=f"Color Shades for {color_name.capitalize()}", color=disnake.Color.from_rgb(*base_color_rgb))
    embed.add_field(name="Base Color", value=base_color_hex, inline=True)
    embed.add_field(name="Lighter Shade", value=lighter_shade_hex, inline=True)
    embed.add_field(name="Darker Shade", value=darker_shade_hex, inline=True)

    try:
        await ctx.send(embed=embed, ephemeral=True)
        image_message = await ctx.send(file=File(color_image, filename="color_shades.png"))
    except disnake.HTTPException as e:
        await ctx.send(f"Failed to send message: {str(e)}", ephemeral=True)

@bot.slash_command()
async def reset(ctx, member: disnake.Member):
    if ctx.author.guild_permissions.administrator:
        if member.id in user_color_change:
            del user_color_change[member.id]
            await ctx.send(f"The color change limit for {member.display_name} has been reset.", ephemeral=True)
        else:
            await ctx.send(f"{member.display_name} has not changed their color yet.", ephemeral=True)
    else:
        await ctx.send("You must be an admin to run this command.", ephemeral=True)

# Error handling for incorrect color names
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandInvokeError):
        error_message = str(error.original)
        
        # Specific error handling for color commands
        if ctx.command.qualified_name in ["colorchange", "color"]:
            if "No color found for the name" in error_message:
                await ctx.send("⚠️ The color name you entered is incorrect. Please check the color name and try again.", ephemeral=True)
        
        # Log the error in the log channel
        if log_channel_id:
            log_channel = bot.get_channel(log_channel_id)
            if log_channel:
                embed = Embed(title="Command Error", color=disnake.Color.red())
                embed.add_field(name="User", value=ctx.author.mention, inline=False)
                embed.add_field(name="Command", value=ctx.command.qualified_name, inline=False)
                embed.add_field(name="Error", value=error_message, inline=False)
                await log_channel.send(embed=embed)

        # Notify the user
        await ctx.send("An error occurred while executing the command.", ephemeral=True)
bot.run(TOKEN)
