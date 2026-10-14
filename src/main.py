import flet as ft

from contexts.settings_context import SettingsContext
from screens.generate_model_screen import GenerateModelScreen
from screens.generate_diagram_screen import GenerateDiagramScreen
from screens.settings_screen import SettingsScreen


DESTINATIONS = [
    ("Generate Diagram", ft.Icons.ACCOUNT_TREE_OUTLINED, ft.Icons.ACCOUNT_TREE),
    ("Generate Model", ft.Icons.AUTO_AWESOME_OUTLINED, ft.Icons.AUTO_AWESOME),
    ("Settings", ft.Icons.SETTINGS_OUTLINED, ft.Icons.SETTINGS),
]


@ft.component
def App() -> ft.Control:
    settings = ft.use_context(SettingsContext)

    async def load_settings():
        await settings.load()

    ft.use_effect(load_settings, [])

    def update_theme_mode():
        ft.context.page.theme_mode = settings.theme_mode

    ft.use_effect(update_theme_mode, [settings.theme_mode])

    selected_index, set_selected_index = ft.use_state(0)

    screen = (
        GenerateDiagramScreen()
        if selected_index == 0
        else GenerateModelScreen()
        if selected_index == 1
        else SettingsScreen()
    )

    return ft.SafeArea(
        ft.Column(
            [
                ft.AppBar(
                    title=ft.Text(DESTINATIONS[selected_index][0]),
                ),
                ft.Container(
                    ft.AnimatedSwitcher(
                        content=screen,
                        transition=ft.AnimatedSwitcherTransition.FADE,
                        duration=150,
                        reverse_duration=150,
                        switch_in_curve=ft.AnimationCurve.EASE_IN_OUT,
                        switch_out_curve=ft.AnimationCurve.EASE_IN_OUT,
                    ),
                    expand=True,
                ),
                ft.NavigationBar(
                    [
                        ft.NavigationBarDestination(
                            label=label,
                            icon=icon,
                            selected_icon=selected_icon,
                        )
                        for label, icon, selected_icon in DESTINATIONS
                    ],
                    selected_index=selected_index,
                    on_change=lambda e: set_selected_index(e.control.selected_index),
                    label_behavior=ft.NavigationBarLabelBehavior.ONLY_SHOW_SELECTED,
                ),
            ],
            expand=True,
        ),
        expand=True,
    )


def main(page: ft.Page):
    page.title = "ER Tools"
    page.padding = 0
    page.window.width = 400
    page.window.height = 600

    page.render(App)


if __name__ == "__main__":
    ft.run(main)
