from __future__ import annotations

# pyrefly: ignore [missing-import]
from discord import app_commands, Interaction

from config import settings


def requires_role():
    """
    App command check that verifies the invoking member has the configured role.
    Returns a user-friendly ephemeral error if they don't.
    """

    async def predicate(interaction: Interaction) -> bool:
        if interaction.guild is None:
            await interaction.response.send_message(
                "⛔ This command can only be used in a server.", ephemeral=True
            )
            return False

        role = next(
            (r for r in interaction.guild.roles if r.name == settings.required_role_name),
            None,
        )
        if role is None:
            await interaction.response.send_message(
                f"⛔ Required role **{settings.required_role_name}** not found in this server.",
                ephemeral=True,
            )
            return False

        if role not in interaction.user.roles:
            await interaction.response.send_message(
                f"⛔ You need the **{settings.required_role_name}** role to run this command.",
                ephemeral=True,
            )
            return False

        return True

    return app_commands.check(predicate)
