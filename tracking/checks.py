import discord

from tracking.models import CheckIn


async def origin_is_active_check_in(interaction: discord.Interaction):
    check_in_active = await CheckIn.objects.filter(thread_id=interaction.channel_id, finished=False).aexists()
    if check_in_active:
        return True
    await interaction.response.send_message(
        'Use an active check-in thread to share your weigh-in',
        ephemeral=True
    )
    return False
