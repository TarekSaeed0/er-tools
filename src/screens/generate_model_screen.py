import asyncio

import flet as ft

from contexts.settings_context import SettingsContext
from services.model_generator import create_model_generator
from utils import show_error


@ft.component
def GenerateModelScreen() -> ft.Control:
    settings = ft.use_context(SettingsContext)
    description, set_description = ft.use_state("")
    output_path, set_output_path = ft.use_state("")
    output, set_output = ft.use_state("")
    is_loading, set_is_loading = ft.use_state(False)
    generator_ref = ft.use_ref(create_model_generator)

    async def on_choose_output(e: ft.Event[ft.OutlinedButton]):
        if not output:
            return

        path = await ft.FilePicker().save_file(
            dialog_title="Save ER model",
            file_name="model.json",
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["json"],
            src_bytes=output.encode(),
        )

        if path:
            set_output_path(path)

    async def on_generate(e: ft.Event[ft.Button]):
        assert generator_ref.current is not None

        if not settings.gemini_api_key:
            show_error("Please enter your Gemini API key in the Settings tab first")
            return

        trimmed_description = description.strip()
        if not trimmed_description:
            show_error("Please enter a requirement description")
            return

        set_is_loading(True)

        try:
            model = await asyncio.to_thread(
                generator_ref.current.generate,
                trimmed_description,
                settings.gemini_api_key,
            )
        except Exception as error:
            show_error(f"Failed to generate model: {error}")
        else:
            set_output(model.model_dump_json(indent=2))
        finally:
            set_is_loading(False)

    controls = [
        ft.Text("Generate ER model from description", size=20),
        ft.Text(
            "Describe your requirements in natural language, then click generate to generate a JSON describing an ER model.",
            color=ft.Colors.GREY_600,
        ),
        ft.TextField(
            label="Requirement Description",
            align_label_with_hint=True,
            multiline=True,
            min_lines=6,
            max_lines=10,
            expand=True,
            value=description,
            on_change=lambda e: set_description(e.control.value),
            hint_text="e.g. A library system where members borrow books.",
        ),
        ft.Row(
            [
                ft.FilledButton(
                    "Generate Model",
                    on_click=on_generate,
                    disabled=is_loading,
                ),
                ft.ProgressRing(visible=is_loading, width=20, height=20),
            ]
        ),
    ]

    if output:
        controls.extend(
            [
                ft.Row(
                    [
                        ft.TextField(
                            label="Output JSON file",
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
                ft.TextField(
                    label="Generated Model",
                    multiline=True,
                    min_lines=8,
                    max_lines=12,
                    expand=True,
                    read_only=True,
                    value=output,
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
