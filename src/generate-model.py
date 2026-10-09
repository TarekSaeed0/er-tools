import argparse
import os
from pathlib import Path

from google import genai

from models import Model

SYSTEM_PROMPT = """
You are an expert database designer tasked with converting text descriptions of systems into structured Entity-Relationship (ER) models.

### Task
Analyze the user's system description, identify core entities, their attributes, and their relationships, and return the corresponding ER Model object adhering strictly to the JSON schema.

### Rules 
- Every strong entity must have at least one primary key attribute.
- Every weak entity must have at least one partial key attribute.
- Every weak entity must have a total participation in at least one identifying relationship.
- All entity `name` fields must be unique within the model.
- Each attribute `name` within a single entity must be unique.
- Sub-attributes `name` in an atrribute must all be unique.
- Relationship participations `entity_name` must strictly match existing entity names.
"""


def main():
    parser = argparse.ArgumentParser(
        prog="generate-diagram",
        description="script for generating ER models from high-level requirement description",
    )

    parser.add_argument("filename", type=Path)
    parser.add_argument("description")

    args = parser.parse_args()

    filename: Path = args.filename
    description = args.description

    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=description,
        system_instruction=SYSTEM_PROMPT,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": Model.model_json_schema(),
        },
    )

    model = interaction.output_text

    filename.write_text(model)


if __name__ == "__main__":
    main()
