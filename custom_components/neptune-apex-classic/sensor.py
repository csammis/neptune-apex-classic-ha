"""Create the sensor entities associated with an Apex."""

from __future__ import annotations

import logging

from neptune_apex_classic.connection import ApexConnection
from neptune_apex_classic.probe import Probe, get_connected_probes

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfTemperature,
)
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
    """Find the probes reported by this Apex and create sensor entities for them."""

    hostname = config.data[CONF_HOST]
    name = config.data[CONF_NAME]
    serial_number = config.data[CONFIG_KEY_SERIAL_NUMBER]
    apex_data = hass.data[DOMAIN][serial_number]
    conn = apex_data[DATA_KEY_CONNECTION]
    coordinator = apex_data[DATA_KEY_COORDINATOR]

    entities = list[ApexBaseEntity]()
    for probe in get_connected_probes(conn):
        if probe.type == "Amps":
            entities.append(
                ApexCurrentSensor(conn, coordinator, name, serial_number, probe)
            )
        elif probe.type == "Temp":
            entities.append(
                ApexTempSensor(conn, coordinator, name, serial_number, probe)
            )
        elif probe.type == "ORP":
            entities.append(
                ApexORPSensor(conn, coordinator, name, serial_number, probe)
            )
        else:
            entities.append(ApexSensor(conn, coordinator, name, serial_number, probe))

    _LOGGER.debug("Found %s probes for Apex at %s", len(entities), hostname)
    if len(entities) == 0:
        _LOGGER.warning("Apex at %s did not return any probes in its status", hostname)

    async_add_entities(entities)


class ApexSensor(ApexBaseEntity, SensorEntity):
    """Apex sensor which does not have a specific known type."""

    def __init__(
        self,
        conn: ApexConnection,
        coordinator: DataUpdateCoordinator,
        name: str,
        serial_number: str,
        probe: Probe,
    ) -> None:
        """Initialize the entity."""
        super().__init__(conn, coordinator, name, serial_number)
        self._probe = probe
        self.entity_description = SensorEntityDescription(
            key=f"{probe.name}-{probe.type}", name=probe.name
        )

    @property
    def unique_id(self) -> str:
        """Return this entity's unique ID."""
        return f"{self._unique_id}/{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return this entity's name."""
        return f"{self._name} {self._probe.name}"

    @property
    def native_value(self) -> str:
        """Return this entity's value."""
        return str(self._probe.value)


class ApexORPSensor(ApexBaseEntity, SensorEntity):
    """Oxygen Reduction Potential probe."""

    def __init__(
        self,
        conn: ApexConnection,
        coordinator: DataUpdateCoordinator,
        name: str,
        serial_number: str,
        probe: Probe,
    ) -> None:
        """Initialize the entity."""
        super().__init__(conn, coordinator, name, serial_number)
        self._probe = probe
        self.entity_description = SensorEntityDescription(
            key=f"{probe.name}-{probe.type}",
            name=probe.name,
            icon="mdi:gas-cylinder",
            native_unit_of_measurement=UnitOfElectricPotential.MILLIVOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def unique_id(self) -> str:
        """Return this entity's unique ID."""
        return f"{self._unique_id}/{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return this entity's name."""
        return f"{self._name} {self._probe.name}"

    @property
    def native_value(self) -> float:
        """Return this entity's value."""
        return float(self._probe.value)


class ApexCurrentSensor(ApexBaseEntity, SensorEntity):
    """Current consumption probe."""

    def __init__(
        self,
        conn: ApexConnection,
        coordinator: DataUpdateCoordinator,
        name: str,
        serial_number: str,
        probe: Probe,
    ) -> None:
        """Initialize the entity."""
        super().__init__(conn, coordinator, name, serial_number)
        self._probe = probe

        self.entity_description = SensorEntityDescription(
            key=f"{probe.name}-{probe.type}",
            name=probe.name,
            icon="mdi:current-ac",
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def unique_id(self) -> str:
        """Return this entity's unique ID."""
        return f"{self._unique_id}/{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return this entity's name."""
        return f"{self._name} {self._probe.name}"

    @property
    def native_value(self) -> float:
        """Return this entity's value."""
        return float(self._probe.value)


class ApexTempSensor(ApexBaseEntity, SensorEntity):
    """Temperature probe."""

    def __init__(
        self,
        conn: ApexConnection,
        coordinator: DataUpdateCoordinator,
        name: str,
        serial_number: str,
        probe: Probe,
    ) -> None:
        """Initialize the entity."""
        super().__init__(conn, coordinator, name, serial_number)
        self._probe = probe

        self.entity_description = SensorEntityDescription(
            key=f"{probe.name}-{probe.type}",
            name=probe.name,
            icon="mdi:thermometer-water",
            native_unit_of_measurement=UnitOfTemperature.FAHRENHEIT,
            device_class=SensorDeviceClass.TEMPERATURE,
            state_class=SensorStateClass.MEASUREMENT,
        )

    @property
    def unique_id(self) -> str:
        """Return this entity's unique ID."""
        return f"{self._unique_id}/{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return this entity's name."""
        return f"{self._name} {self._probe.name}"

    @property
    def native_value(self) -> float:
        """Return this entity's value."""
        return float(self._probe.value)
