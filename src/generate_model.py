import argparse
import os
from pathlib import Path

from google import genai

from models import Model

SYSTEM_PROMPT = """
You are an expert database designer tasked with converting text descriptions of systems into structured Entity-Relationship (ER) models.

### Task
Analyze the user's system description, identify core entities, their attributes, and their relationships, and return the corresponding ER Model object adhering strictly to the JSON schema.

### Rules & Constraints 
- If the user provides a short or high-level description, you are expected to invent comprehensive domain-specific entities and relationships. 
- Every strong entity must have at least one primary key attribute ("is_primary_key": true).
- Every weak entity must have at least one partial key attribute ("is_partial_key": true).
- Every weak entity must have a total participation ("constraint": "total") in at least one identifying relationship ("is_identifying": true).
- All entity `name` fields must be unique within the model.
- Each attribute `name` within a single entity must be unique.
- Sub-attributes `name` in an atrribute must all be unique.
- Relationship participations `entity_name` must strictly match existing entity names.

### Example
An example of an ER model for a company system:
```json
{
  "entities": [
    {
      "name": "Employee",
      "is_weak": false,
      "attributes": [
        {
          "name": "emp_id",
          "is_primary_key": true
        },
        {
          "name": "name",
          "sub_attributes": [
            {
              "name": "first_name"
            },
            { 
              "name": "last_name"
            }
          ]
        },
        {
          "name": "phone_numbers",
          "is_multivalued": true
        },
        {
          "name": "age",
          "is_derived": true
        }
      ]
    },
    {
      "name": "Department",
      "is_weak": false,
      "attributes": [
        {
          "name": "dept_id",
          "is_primary_key": true
        },
        {
          "name": "dept_name"
        }
      ]
    },
    {
      "name": "Dependent",
      "is_weak": true,
      "attributes": [
        {
          "name": "dependent_name",
          "is_partial_key": true
        },
        {
          "name": "relationship_type"
        }
      ]
    }
  ],
  "relationships": [
    {
      "name": "WorkAssignment",
      "is_identifying": false,
      "participations": [
        {
          "entity_name": "Employee",
          "role": "worker",
          "cardinality": "many",
          "constraint": "total"
        },
        {
          "entity_name": "Department",
          "role": "workplace",
          "cardinality": "one",
          "constraint": "partial"
        }
      ],
      "attributes": [
        {
          "name": "start_date"
        }
      ]
    },
    {
      "name": "EmployeeDependents",
      "is_identifying": true,
      "participations": [
        {
          "entity_name": "Employee",
          "cardinality": "one",
          "constraint": "partial"
        },
        {
          "entity_name": "Dependent",
          "cardinality": "many",
          "constraint": "total"
        }
      ]
    }
  ]
}
"""


def generate_model(
    description: str, gemini_api_key: str | None = os.environ.get("GEMINI_API_KEY")
) -> str:
    client = genai.Client(api_key=gemini_api_key)

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

    return interaction.output_text


def main():
    parser = argparse.ArgumentParser(
        prog="generate_diagram",
        description="script for generating ER models from high-level requirement description",
    )

    parser.add_argument("filename", type=Path)
    parser.add_argument("description")

    args = parser.parse_args()

    filename: Path = args.filename
    description = args.description

    model = generate_model(description)

    filename.write_text(model)


if __name__ == "__main__":
    main()
