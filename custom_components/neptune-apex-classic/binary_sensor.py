"""Create the binary sensor (outlet) entities associated with an Apex."""

from __future__ import annotations

import logging

from neptune_apex_classic.connection import ApexConnection
from neptune_apex_classic.outlet import Outlet, get_connected_outlets

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
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
    """Find the outlets reported by this Apex and create binary sensor entities for them."""

    hostname = config.data[CONF_HOST]
    name = config.data[CONF_NAME]
    serial_number = config.data[CONFIG_KEY_SERIAL_NUMBER]
    apex_data = hass.data[DOMAIN][serial_number]
    conn = apex_data[DATA_KEY_CONNECTION]
    coordinator = apex_data[DATA_KEY_COORDINATOR]

    entities = []
    for outlet in get_connected_outlets(conn):
        entities.append(ApexOutlet(conn, coordinator, name, serial_number, outlet))

    _LOGGER.debug("Found %s outlets for Apex at %s", len(entities), hostname)
    if len(entities) == 0:
        _LOGGER.warning("Apex at %s did not return any outlets in its status", hostname)

    async_add_entities(entities)


class ApexOutlet(ApexBaseEntity, BinarySensorEntity):
    """Apex outlet."""

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
        self.entity_description = BinarySensorEntityDescription(
            key=f"{outlet.name}-{outlet.device_id}",
            name=outlet.name,
            device_class=BinarySensorDeviceClass.POWER,
        )

    @property
    def unique_id(self) -> str:
        """Return this entity's unique ID."""
        return f"{self._unique_id}/{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return this entity's name."""
        return f"{self._name} {self._outlet.name}"

    @property
    def is_on(self) -> bool:
        """Get a value indicating whether this binary sensor is on or off."""
        value = self._outlet.value
        return value in [Outlet.AUTO_ON, Outlet.ON]
