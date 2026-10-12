from dataclasses import dataclass

import flet as ft
import flet_secure_storage as fss


@ft.observable
@dataclass
class Settings:
    GEMINI_API_KEY_KEY = "er_tools.gemini_api_key"
    THEME_MODE_KEY = "er_tools.theme_mode"

    gemini_api_key: str = ""
    theme_mode: ft.ThemeMode = ft.ThemeMode.SYSTEM

    async def load(self):
        gemini_api_key = await fss.SecureStorage().get(Settings.GEMINI_API_KEY_KEY)
        if gemini_api_key:
            self.gemini_api_key = gemini_api_key

        theme_mode = await ft.SharedPreferences().get(Settings.THEME_MODE_KEY)
        if theme_mode:
            try:
                self.theme_mode = ft.ThemeMode(theme_mode)
            except ValueError:
                self.theme_mode = ft.ThemeMode.SYSTEM

    async def set_gemini_api_key(self, gemini_api_key: str):
        self.gemini_api_key = gemini_api_key
        await fss.SecureStorage().set(Settings.GEMINI_API_KEY_KEY, gemini_api_key)

    async def delete_gemini_api_key(self):
        self.gemini_api_key = ""
        await fss.SecureStorage().remove(Settings.GEMINI_API_KEY_KEY)

    async def set_theme_mode(self, theme_mode: ft.ThemeMode):
        self.theme_mode = theme_mode
        await ft.SharedPreferences().set(Settings.THEME_MODE_KEY, theme_mode.value)


SettingsContext = ft.create_context(Settings())
