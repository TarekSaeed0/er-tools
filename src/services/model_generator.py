from typing import Protocol

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
- Only use total participation ("constraint": "total") if all instances of the entity are involved in the relationshi,; otherwise, use partial participation ("constraint": "partial").
"""


class ModelGenerator(Protocol):
    def generate(self, description: str, api_key: str) -> Model: ...


class GeminiModelGenerator:
    def generate(self, description: str, api_key: str) -> Model:
        client = genai.Client(api_key=api_key)

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

        return Model.model_validate_json(interaction.output_text)


def create_model_generator() -> ModelGenerator:
    return GeminiModelGenerator()
