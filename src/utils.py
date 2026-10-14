import flet as ft
from pathlib import Path
import os


def get_assets_directory() -> Path:
    default_assets_dir = Path(__file__).parent / "assets"
    return Path(os.environ.get("FLET_ASSETS_DIR", str(default_assets_dir))).resolve()


def show_error(text: str) -> None:
    ft.context.page.show_dialog(
        ft.SnackBar(
            ft.Text(text),
            bgcolor=ft.Colors.RED_400,
        )
    )
