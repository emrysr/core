"""The Radio Browser integration."""

from __future__ import annotations

import logging

from aiodns.error import DNSError
from radios import RadioBrowser, RadioBrowserError

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import __version__
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

type RadioBrowserConfigEntry = ConfigEntry[RadioBrowser]


async def async_setup_entry(
    hass: HomeAssistant, entry: RadioBrowserConfigEntry
) -> bool:
    """Set up Radio Browser from a config entry.

    This integration doesn't set up any entities, as it provides a media source
    only.
    """
    session = async_get_clientsession(hass)
    radios = RadioBrowser(session=session, user_agent=f"HomeAssistant/{__version__}")

    try:
        await radios.stats()
    except (DNSError, RadioBrowserError) as err:
        raise ConfigEntryNotReady("Could not connect to Radio Browser API") from err

    entry.runtime_data = radios

    async def async_add_favorite(call):
        """Add a radio station to favorites."""
        station_uuid = call.data.get("station_uuid")
        if station_uuid:
            favorites = entry.options.get("favorites", [])
            if station_uuid not in favorites:
                favorites.append(station_uuid)
                hass.config_entries.async_update_entry(
                    entry, options={**entry.options, "favorites": favorites}
                )
            else:
                _LOGGER.warning(f"Station {station_uuid} is already a favorite.")

    async def async_remove_favorite(call):
        """Remove a radio station from favorites."""
        station_uuid = call.data.get("station_uuid")
        if station_uuid:
            favorites = entry.options.get("favorites", [])
            if station_uuid in favorites:
                favorites.remove(station_uuid)
                hass.config_entries.async_update_entry(
                    entry, options={**entry.options, "favorites": favorites}
                )
            else:
                _LOGGER.warning(f"Station {station_uuid} is not a favorite.")

    async def async_list_favorites(call):
        """List all favorite radio stations."""
        favorites = entry.options.get("favorites", [])
        _LOGGER.info(f"Favorite stations: {favorites}")
        # Here you would add the logic to retrieve station data from the API
        # based on the UUIDs and return it to the user.
        # This part depends on how you want to present the data.
        # For example, you could fire a Home Assistant event.
        hass.bus.async_fire("radio_browser_favorites", {"favorites": favorites})

    async def async_play_favorite(call):
        """Play a favorite radio station."""
        station_uuid = call.data.get("station_uuid")
        favorites = entry.options.get("favorites", [])
        if station_uuid in favorites:
            # Code here that uses the existing play functionality to play the station.
            # You will need to find the existing service call that does this.
            # Then call that service here.
            _LOGGER.info(f"Playing favorite station: {station_uuid}")
            # Example:
            # await hass.services.async_call(
            #     "media_player",
            #     "play_media",
            #     {"entity_id": "your_media_player_entity", "media_content_id": station_uuid, "media_content_type": "music"},
            # )
        else:
            _LOGGER.warning(f"Station {station_uuid} is not a favorite.")

    hass.services.async_register("radio_browser", "add_favorite", async_add_favorite, vol.Schema({vol.Required("station_uuid"): cv.string}))
    hass.services.async_register("radio_browser", "remove_favorite", async_remove_favorite, vol.Schema({vol.Required("station_uuid"): cv.string}))
    hass.services.async_register("radio_browser", "list_favorites", async_list_favorites)
    hass.services.async_register("radio_browser", "play_favorite", async_play_favorite, vol.Schema({vol.Required("station_uuid"): cv.string}))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    hass.services.async_remove("radio_browser", "add_favorite")
    hass.services.async_remove("radio_browser", "remove_favorite")
    hass.services.async_remove("radio_browser", "list_favorites")
    hass.services.async_remove("radio_browser", "play_favorite")
    return True

async def async_remove_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> None:
    """Handle removal of an entry."""
    pass

async def async_migrate_entry(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> bool:
    """Migrate old entry."""
    return True

class RadioBrowserOptionsFlow(config_entries.OptionsFlow):
    """Handle radio_browser options."""

    async def async_step_init(self, user_input=None):
        """Manage the options."""
        return await self.async_step_user()

    async def async_step_user(self, user_input=None):
        """Handle a flow initialized by the user."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "favorites",
                        default=self.hass.config_entries.async_get_entry(self.config_entry.entry_id).options.get("favorites", []),
                    ): cv.ensure_list,
                }
            ),
        )

async def async_config_entry_title(hass: HomeAssistant, entry: config_entries.ConfigEntry) -> str:
    """Return translated title."""
    return "Radio Browser"
