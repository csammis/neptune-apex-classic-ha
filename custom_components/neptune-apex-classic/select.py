"""Create the selection controls for Apex outlets."""

from __future__ import annotations

import logging

from neptune_apex_classic.connection import ApexConnection
from neptune_apex_classic.outlet import Outlet, get_connected_outlets

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import DiscoveryInfoType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from . import ApexBaseEntity
from .const import (
    CONFIG_KEY_SERIAL_NUMBER,
    DATA_KEY_CONNECTION,
    DATA_KEY_COORDINATOR,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Find the outlets reported by this Apex and create selection entities for them."""

    hostname = config.data[CONF_HOST]
    name = config.data[CONF_NAME]
    serial_number = config.data[CONFIG_KEY_SERIAL_NUMBER]
    apex_data = hass.data[DOMAIN][serial_number]
    conn = apex_data[DATA_KEY_CONNECTION]
    coordinator = apex_data[DATA_KEY_COORDINATOR]

    entities = []
    for outlet in get_connected_outlets(conn):
        # Exclude virtual outlets from having selection entities made. They are essentially read-only.
        if outlet.device_id.startswith("Cntl") is False:
            entities.append(
                ApexOutletControl(conn, coordinator, name, serial_number, outlet)
            )

    _LOGGER.debug(
        "Found %s controllable outlets for Apex at %s", len(entities), hostname
    )
    if len(entities) == 0:
        _LOGGER.warning("No controllable outlets found for Apex at %s", hostname)

    async_add_entities(entities)


class ApexOutletControl(ApexBaseEntity, SelectEntity):
    """Apex outlet controller."""

    def __init__(
        self,
        conn: ApexConnection,
        coordinator: DataUpdateCoordinator,
        name: str,
        serial_number: str,
        outlet: Outlet,
    ) -> None:
        """Initialize the entity."""
        super().__init__(conn, coordinator, name, serial_number)
        self._outlet = outlet
        self.entity_description = SelectEntityDescription(
            key=f"{outlet.name}-{outlet.device_id}-state", name=outlet.name
        )

    @property
    def unique_id(self) -> str:
        """Return this entity's unique ID."""
        return f"{self._unique_id}/{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return this entity's name."""
        return f"{self._name} {self._outlet.name} - Set State"

    @property
    def current_option(self) -> str | None:
        """Return this entity's currently selected option."""
        value = self._outlet.value
        if value in [Outlet.AUTO_OFF, Outlet.AUTO_ON]:
            return str(Outlet.AUTO)
        return str(value)  # Outlet.ON or Outlet.OFF

    @property
    def options(self) -> list[str]:
        """Return the possible states for this entity."""
        return [Outlet.OFF, Outlet.AUTO, Outlet.ON]

    async def async_select_option(self, option: str) -> None:
        """Update the outlet state to the selected option."""
        await self._outlet.set_state(option)

        # Force a refresh to ensure that any displayed outlet binary sensors are updated
        await self.async_update_ha_state(force_refresh=True)
