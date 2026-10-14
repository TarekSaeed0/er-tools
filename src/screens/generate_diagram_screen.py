import asyncio
from pathlib import Path

import flet as ft
from pydantic import ValidationError

from models import Model
from services.diagram_renderer import create_diagram_renderer
from utils import show_error

ZOOM_STEP = 1.25


@ft.component
def GenerateDiagramScreen() -> ft.Control:
    input_path, set_input_path = ft.use_state("")
    input_bytes, set_input_bytes = ft.use_state(b"")
    output_path, set_output_path = ft.use_state("")
    output_bytes, set_output_bytes = ft.use_state(b"")
    is_loading, set_is_loading = ft.use_state(False)
    renderer_ref = ft.use_ref(create_diagram_renderer)
    viewer_ref = ft.Ref[ft.InteractiveViewer]()

    async def on_browse(e: ft.Event[ft.OutlinedButton]):
        files = await ft.FilePicker().pick_files(
            dialog_title="Select ER model JSON",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
            allow_multiple=False,
            with_data=True,
        )

        if not files or not files[0] or not files[0].bytes:
            return

        set_input_path(files[0].path or files[0].name)
        set_input_bytes(files[0].bytes)

    async def on_choose_output(e: ft.Event[ft.OutlinedButton]):
        default_name = f"{Path(input_path).stem}.png" if input_path else "diagram.png"

        path = await ft.FilePicker().save_file(
            dialog_title="Save ER diagram",
            file_name=default_name,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["png"],
            src_bytes=output_bytes,
        )

        if path and output_bytes:
            set_output_path(path)

    async def on_generate(e: ft.Event[ft.Button]):
        assert renderer_ref.current is not None

        if not input_bytes:
            show_error("Please select a JSON file first")
            return

        set_is_loading(True)

        try:
            model = Model.model_validate_json(input_bytes)

            output_bytes = await asyncio.to_thread(renderer_ref.current.render, model)
        except ValidationError as error:
            show_error(f"Invalid ER model:\n{error}")
        except Exception as error:
            show_error(f"Failed to generate diagram: {error}")
        else:
            set_output_bytes(output_bytes)

            if viewer_ref.current:
                await viewer_ref.current.reset()

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
        ft.Text("Generate ER diagram from JSON", size=20),
        ft.Text(
            "Select a JSON file describing an ER model, then click generate to generate an ER diagram.",
            color=ft.Colors.GREY_600,
        ),
        ft.Row(
            [
                ft.TextField(
                    label="ER model JSON file",
                    value=input_path,
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
                    disabled=is_loading or not input_bytes,
                ),
                ft.ProgressRing(visible=is_loading, width=20, height=20),
            ]
        ),
    ]

    if output_bytes:
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
                        content=ft.Image(src=output_bytes, fit=ft.BoxFit.CONTAIN),
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
