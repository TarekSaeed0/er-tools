import asyncio
import tempfile
import uuid
from pathlib import Path

import flet as ft
from pydantic import ValidationError

from generate_diagram import generate_diagram
from models import Model
from utils import show_error

ZOOM_STEP = 1.25


@ft.component
def GenerateDiagramScreen() -> ft.Control:
    json_path, set_json_path = ft.use_state("")
    output_path, set_output_path = ft.use_state("")
    status, set_status = ft.use_state("")
    is_loading, set_is_loading = ft.use_state(False)
    preview_file_path, set_preview_file_path = ft.use_state("")

    viewer_ref = ft.Ref[ft.InteractiveViewer]()

    def cleanup_preview():
        if preview_file_path:
            Path(preview_file_path).unlink(missing_ok=True)

    async def on_browse(e: ft.Event[ft.OutlinedButton]):
        files = await ft.FilePicker().pick_files(
            dialog_title="Select ER model JSON",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
            allow_multiple=False,
        )

        if not files or not files[0].path:
            return

        file_path = files[0].path
        set_json_path(file_path)
        set_status("")

    async def on_choose_output(e: ft.Event[ft.OutlinedButton]):
        default_name = f"{Path(json_path).stem}.png" if json_path else "diagram.png"

        image_bytes = Path(preview_file_path).read_bytes()

        path = await ft.FilePicker().save_file(
            dialog_title="Save ER diagram",
            file_name=default_name,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png"],
            src_bytes=image_bytes,
        )

        if path and preview_file_path:
            set_output_path(path)
            set_status(f"Saved to {path}")

    def render_diagram_blocking(filename: Path) -> str:
        model = Model.model_validate_json(filename.read_text())

        render = generate_diagram(model)

        temporary_file_path = (
            Path(tempfile.gettempdir()) / f"er_diagram_{uuid.uuid4().hex}"
        )

        saved = render.render(
            str(temporary_file_path), format="png", view=False, cleanup=True
        )

        return saved

    async def on_generate(e: ft.Event[ft.Button]):
        if not json_path:
            show_error("Please select a JSON file first")
            return

        filename = Path(json_path)

        set_is_loading(True)
        set_status("Generating diagram...")

        try:
            preview_path = await asyncio.to_thread(render_diagram_blocking, filename)
        except FileNotFoundError:
            set_status("File not found")
            show_error(f"File not found: {filename}")
        except ValidationError as error:
            set_status("Invalid ER model")
            show_error(f"Invalid ER model:\n{error}")
        except Exception as error:
            set_status("Generation failed")
            show_error(f"Failed to generate diagram: {error}")
        else:
            cleanup_preview()
            set_preview_file_path(preview_path)
            set_status("Diagram generated")
        finally:
            set_is_loading(False)

    async def on_zoom_in(e: ft.Event[ft.IconButton]):
        if viewer_ref.current:
            await viewer_ref.current.zoom(ZOOM_STEP)

    async def on_zoom_out(e: ft.Event[ft.IconButton]):
        if viewer_ref.current:
            await viewer_ref.current.zoom(1 / ZOOM_STEP)

    async def on_reset_view(e: ft.Event[ft.IconButton]):
        if viewer_ref.current:
            await viewer_ref.current.reset()

    controls = [
        ft.Text("Generate ER diagram from JSON", size=20, weight=ft.FontWeight.BOLD),
        ft.Text(
            "Select a JSON file describing an ER model, then click generate to generate an ER diagram.",
            color=ft.Colors.GREY_600,
        ),
        ft.Row(
            [
                ft.TextField(
                    label="ER model JSON file",
                    value=json_path,
                    read_only=True,
                    expand=True,
                ),
                ft.OutlinedButton(
                    "Browse",
                    icon=ft.Icons.FOLDER_OPEN,
                    on_click=on_browse,
                ),
            ]
        ),
        ft.Row(
            [
                ft.FilledButton(
                    "Generate Diagram",
                    on_click=on_generate,
                    disabled=is_loading,
                ),
                ft.ProgressRing(visible=is_loading, width=20, height=20),
                ft.Text(status, size=13),
            ]
        ),
    ]

    if preview_file_path:
        controls.extend(
            [
                ft.Row(
                    [
                        ft.TextField(
                            label="Output PNG file",
                            value=output_path,
                            read_only=True,
                            expand=True,
                        ),
                        ft.OutlinedButton(
                            "Save",
                            icon=ft.Icons.SAVE,
                            on_click=on_choose_output,
                        ),
                    ]
                ),
                ft.Row(
                    [
                        ft.IconButton(
                            icon=ft.Icons.ZOOM_IN,
                            tooltip="Zoom in",
                            on_click=on_zoom_in,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ZOOM_OUT,
                            tooltip="Zoom out",
                            on_click=on_zoom_out,
                        ),
                        ft.IconButton(
                            icon=ft.Icons.CENTER_FOCUS_STRONG,
                            tooltip="Reset view",
                            on_click=on_reset_view,
                        ),
                        ft.Text(
                            "Scroll or pinch to zoom, drag to pan",
                            size=12,
                            color=ft.Colors.GREY_600,
                        ),
                    ]
                ),
                ft.Container(
                    ft.InteractiveViewer(
                        ref=viewer_ref,
                        content=ft.Image(src=preview_file_path, fit=ft.BoxFit.CONTAIN),
                        min_scale=0.1,
                        max_scale=10,
                        boundary_margin=ft.Margin.all(100),
                        expand=True,
                    ),
                    expand=True,
                    border=ft.Border.all(1, ft.Colors.OUTLINE),
                    border_radius=ft.BorderRadius.all(8),
                    clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    bgcolor=ft.Colors.WHITE,
                    aspect_ratio=1,
                ),
            ]
        )

    return ft.ListView(
        controls,
        expand=True,
        padding=20,
        spacing=15,
        scroll=ft.ScrollMode.AUTO,
    )
