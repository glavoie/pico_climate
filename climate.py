"""Climate platform for Pi Pico W Remote integration."""
from __future__ import annotations

import urllib.request

import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    FAN_AUTO,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_UNIQUE_ID,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

SUPPORT_FLAGS = 0

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_IP_ADDRESS): cv.string,
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    # Assign configuration variables.
    # The configuration check takes care they are present.
    ip = config[CONF_IP_ADDRESS]
    name = config[CONF_NAME]
    unique_id = config[CONF_UNIQUE_ID]

    # Add devices
    add_entities([PicoClimate(unique_id=unique_id, name=name, ip=ip)])


class PicoClimate(ClimateEntity):
    """pico_climate Climate."""

    def __init__(
        self,
        unique_id: str,
        name: str,
        ip: str,
    ) -> None:
        """Initialize the climate device."""
        super().__init__()

        self._unique_id = unique_id
        self._attr_name = name
        self.ip = ip

        self._attr_hvac_modes = [cls.value for cls in HVACMode]
        self._attr_temperature_unit = TEMP_CELSIUS
        self._attr_supported_features = (
            ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE
        )
        self._attr_fan_modes = ["Auto", "Silent", "1", "2", "3", "4", "5"]
        self._attr_hvac_mode = HVACMode.FAN_ONLY
        self._attr_fan_mode = "Auto"
        self._attr_current_temperature = 23
        self._attr_target_temperature = 23
        self._attr_min_temp = 10
        self._attr_max_temp = 30

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""

        if hvac_mode == HVACMode.OFF:
            urllib.request.urlopen("http://" + self.ip + "/off").read()
        else:
            urllib.request.urlopen("http://" + self.ip + "/on").read()
