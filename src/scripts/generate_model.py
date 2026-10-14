import argparse
import os
from pathlib import Path

from services.model_generator import GeminiModelGenerator


def main():
    parser = argparse.ArgumentParser(
        prog="generate_diagram",
        description="script for generating ER models from high-level requirement description",
    )

    parser.add_argument("description", type=str)
    parser.add_argument("-o", "--output_file", type=Path, required=True)
    parser.add_argument(
        "--api-key",
        type=str,
        default=os.environ.get("GEMINI_API_KEY"),
    )

    args = parser.parse_args()

    description = args.description
    output_file: Path = args.output_file
    api_key = args.api_key

    generator = GeminiModelGenerator()

    try:
        model = generator.generate(description, api_key)

        output_file.write_text(model.model_dump_json(indent=2))
    except Exception as error:
        print(f"Failed to generate model: {error}")


if __name__ == "__main__":
    main()
