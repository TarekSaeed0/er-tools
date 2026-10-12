import flet as ft


def show_error(text: str) -> None:
    ft.context.page.show_dialog(
        ft.SnackBar(
            ft.Text(text),
            bgcolor=ft.Colors.RED_400,
        )
    )
