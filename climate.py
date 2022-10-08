"""Climate platform for Pi Pico W Remote integration."""
from __future__ import annotations

import urllib.request
import voluptuous as vol

from homeassistant.components.climate import PLATFORM_SCHEMA, ClimateEntity
from homeassistant.components.climate.const import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    FAN_AUTO,
    ClimateEntityFeature,
    HVACMode,
)

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_WHOLE,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_UNIQUE_ID,
    CONF_API_KEY,
    TEMP_CELSIUS,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.restore_state import RestoreEntity

SUPPORT_FLAGS = 0
DEFAULT_TEMP = 23
HVAC_MODES = [cls.value for cls in HVACMode if cls != HVACMode.HEAT_COOL]
FAN_MODES = ["Auto", "Quiet", "1", "2", "3", "4", "5"]

# Validation of the user's configuration
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Required(CONF_UNIQUE_ID): cv.string,
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_IP_ADDRESS): cv.string,
        vol.Required(CONF_API_KEY): cv.string
    }
)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    # Add devices
    add_entities([PicoClimate(hass, config)])


class PicoClimate(ClimateEntity, RestoreEntity):
    """pico_climate Climate."""

    def __init__(self, hass: HomeAssistant, config: ConfigType) -> None:
        self._hass = hass

        self._unique_id = config[CONF_UNIQUE_ID]
        self._attr_name = config[CONF_NAME]
        self.ip = config[CONF_IP_ADDRESS]
        self.api_key = config[CONF_API_KEY]

        # Default values
        self._attr_hvac_mode = HVACMode.OFF
        self._attr_fan_mode = "Auto"

    async def async_added_to_hass(self):
        """Reload the previous state."""
        await super().async_added_to_hass()

        # Check If we have an old state
        previous_state = await self.async_get_last_state()
        if previous_state is not None:
            if previous_state.state in self.hvac_modes:
                self._attr_hvac_mode = previous_state.state
            else:
                self._attr_hvac_mode = HVACMode.OFF

            self._attr_target_temperature = previous_state.attributes.get(
                ATTR_TEMPERATURE, DEFAULT_TEMP
            )
            
            self._attr_fan_mode = previous_state.attributes.get(
                ATTR_FAN_MODE, FAN_AUTO
            )

            self._attr_current_temperature = previous_state.attributes.get(
                ATTR_CURRENT_TEMPERATURE, DEFAULT_TEMP
            )

            await self._hass.async_add_executor_job(self.send_state)

    @property
    def supported_features(self) -> int:
        """Return the list of supported features."""
        return ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.FAN_MODE

    @property
    def temperature_unit(self) -> str:
        """Return the unit of measurement used by the platform."""
        return TEMP_CELSIUS

    @property
    def precision(self) -> float:
        """Return the precision of the climate device."""
        return PRECISION_WHOLE

    @property
    def hvac_modes(self) -> list[str]:
        """Return the list of available operation modes."""
        return HVAC_MODES

    @property
    def fan_modes(self) -> list[str]:
        """Return the list of available fan modes."""
        return FAN_MODES

    @property
    def min_temp(self) -> float:
        """Return the minimum temperature."""
        return 10

    @property
    def max_temp(self) -> float:
        """Return the maximum temperature."""
        return 32

    def set_hvac_mode(self, hvac_mode: HVACMode) -> None:
        """Set new target hvac mode."""

        self._attr_hvac_mode = hvac_mode
        self.send_state()

    def set_fan_mode(self, fan_mode):
        """Set new target fan mode."""
        self._attr_fan_mode = fan_mode
        self.send_state()

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        self._attr_target_temperature = int(kwargs['temperature'])
        self._attr_current_temperature = self._attr_target_temperature
        self.send_state()

    def send_state(self):
        print("Updating state for " + self.name)
        
        power = 0 if self._attr_hvac_mode == HVACMode.OFF else 1

        query = "http://{ip}/state?key={api_key}&power={power}&mode={mode}&temperature={temperature}&fan={fan}".format(
            ip=self.ip,
            api_key=self.api_key,
            power=power,
            mode=self._attr_hvac_mode,
            temperature=self._attr_target_temperature,
            fan=self._attr_fan_mode
        )
        print(query)

        try:
            urllib.request.urlopen(query, timeout=5).read()
        except urllib.error.URLError as err:
            print(err)