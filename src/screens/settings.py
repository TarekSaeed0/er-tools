import flet as ft

from contexts.settings import SettingsContext


@ft.component
def SettingsScreen() -> ft.Control:
    settings = ft.use_context(SettingsContext)
    gemini_api_key, set_gemini_api_key = ft.use_state(settings.gemini_api_key)

    ft.use_effect(
        lambda: set_gemini_api_key(settings.gemini_api_key), [settings.gemini_api_key]
    )

    async def on_save(e):
        await settings.set_gemini_api_key(gemini_api_key)

    async def on_theme_change(e: ft.Event[ft.SegmentedButton]):
        await settings.set_theme_mode(ft.ThemeMode(e.control.selected[0]))

    controls = [
        ft.Text("Theme Mode", size=16, weight=ft.FontWeight.BOLD),
        ft.SegmentedButton(
            segments=[
                ft.Segment(
                    value=ft.ThemeMode.SYSTEM.value,
                    label=ft.Text("System"),
                    icon=ft.Icon(ft.Icons.SETTINGS),
                ),
                ft.Segment(
                    value=ft.ThemeMode.LIGHT.value,
                    label=ft.Text("Light"),
                    icon=ft.Icon(ft.Icons.WB_SUNNY_OUTLINED),
                ),
                ft.Segment(
                    value=ft.ThemeMode.DARK.value,
                    label=ft.Text("Dark"),
                    icon=ft.Icon(ft.Icons.NIGHTLIGHT_ROUND),
                ),
            ],
            selected=[settings.theme_mode.value],
            on_change=on_theme_change,
            allow_empty_selection=False,
            allow_multiple_selection=False,
        ),
        ft.Text("Gemini API Key", size=16, weight=ft.FontWeight.BOLD),
        ft.Row(
            [
                ft.TextField(
                    label="Gemini API key",
                    password=True,
                    can_reveal_password=True,
                    value=gemini_api_key,
                    on_change=lambda e: set_gemini_api_key(e.control.value),
                    expand=True,
                ),
                ft.FilledButton("Save", on_click=on_save),
            ],
            expand=True,
        ),
    ]

    return ft.ListView(
        controls,
        expand=True,
        padding=20,
        spacing=15,
    )
