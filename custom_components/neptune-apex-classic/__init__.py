"""Integration for classic Neptune Apex units."""
from __future__ import annotations

import logging

from neptune_apex_classic.connection import ApexConnection

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PASSWORD,
    CONF_USERNAME,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import (
    CONFIG_KEY_SERIAL_NUMBER,
    DATA_KEY_CONNECTION,
    DATA_KEY_COORDINATOR,
    DOMAIN,
    TIME_BETWEEN_UPDATES,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Set up the entry for the Apex component."""
    hostname = config.data[CONF_HOST]
    serial_number = config.data[CONFIG_KEY_SERIAL_NUMBER]
    _LOGGER.info(
        "Setting up %s integration with host %s with ID %s",
        DOMAIN,
        hostname,
        serial_number,
    )

    session = async_get_clientsession(hass, False)
    conn = ApexConnection(
        hostname, session, config.data[CONF_USERNAME], config.data[CONF_PASSWORD]
    )

    # Enable the state selection entities to allow controlling outlets
    # if the configuration includes a username and password for authentication
    if config.data[CONF_USERNAME] and config.data[CONF_PASSWORD]:
        PLATFORMS.append(Platform.SELECT)

    # Set up a DataUpdateCoordinator so as to not slam the poor Apex with requests
    async def async_data_update() -> None:
        await conn.refresh()

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=config.data[CONF_NAME],
        update_interval=TIME_BETWEEN_UPDATES,
        update_method=async_data_update,
    )

    # Stash the ApexConnection and coordinator for access by individual sensors
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][serial_number] = {
        DATA_KEY_CONNECTION: conn,
        DATA_KEY_COORDINATOR: coordinator,
    }

    await coordinator.async_config_entry_first_refresh()
    await coordinator.async_refresh()
    await hass.config_entries.async_forward_entry_setups(config, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config: ConfigEntry) -> bool:
    """Unload an Apex entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(config, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(config.data[CONFIG_KEY_SERIAL_NUMBER])
    return unload_ok


class ApexBaseEntity(CoordinatorEntity):
    """Base entity for Apex sensors managed by a DataUpdateCoordinator."""

    def __init__(
        self,
        conn: ApexConnection,
        coordinator: DataUpdateCoordinator,
        name: str,
        serial_number: str,
    ) -> None:
        """Initialize the entity."""
        super().__init__(coordinator)
        self.conn = conn
        self._name = name
        self._unique_id = serial_number

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device information of the entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._unique_id)},
            name=self._name,
            model="Apex Classic",
            manufacturer="Neptune",
        )
