import argparse
from pathlib import Path

from pydantic import ValidationError

from models import Model
from services.diagram_renderer import GraphvizDiagramRenderer


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="generate_diagram",
        description="script for generating ER digrams from json",
    )
    parser.add_argument("input_file", type=Path)
    parser.add_argument("-o", "--output_file", type=Path)

    args = parser.parse_args()

    input_file: Path = args.input_file
    output_file: Path | None = args.output_file
    if not output_file:
        output_file = input_file.with_suffix(".png")

    try:
        model = Model.model_validate_json(input_file.read_text())
    except FileNotFoundError:
        parser.error(f"File not found: {input_file}")
    except ValidationError as e:
        parser.error(f"Invalid ER Model:\n{e}")

    renderer = GraphvizDiagramRenderer()

    try:
        diagram_bytes = renderer.render(model)

        output_file.write_bytes(diagram_bytes)
    except Exception as error:
        print(f"Failed to generate diagram: {error}")


if __name__ == "__main__":
    main()
