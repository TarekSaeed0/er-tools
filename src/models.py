from typing import Any

from pydantic import BaseModel, field_validator, model_validator


class Attribute(BaseModel):
    name: str
    isPrimaryKey: bool = False
    isMultiValued: bool = False
    composite: list[str] | None = None

    @field_validator("composite")
    @classmethod
    def validate_composite(cls, composite: list[str] | None) -> list[str] | None:
        if composite is not None:
            if len(composite) <= 1:
                raise ValueError(
                    "A composite attribute must contain at least 2 sub-attributes"
                )

            if len(composite) != len(set(composite)):
                raise ValueError("Composite sub-attributes must be unique")

        return composite


class Entity(BaseModel):
    name: str
    attributes: list[Attribute]

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, attributes: list[Attribute]) -> list[Attribute]:
        if len(attributes) != len({a.name for a in attributes}):
            raise ValueError("Entity attributes must be unique")

        return attributes

    @model_validator(mode="after")
    def validate_entity(self) -> "Entity":
        if not any(attr.isPrimaryKey for attr in self.attributes):
            raise ValueError(f'Entity "{self.name}" must have a primary key')

        return self


class Cardinality(BaseModel):
    left: str
    right: str

    @model_validator(mode="before")
    @classmethod
    def parse_string(cls, data: Any) -> Any:
        if isinstance(data, str):
            left, right = data.split(":", 1)
            return {"left": left.strip(), "right": right.strip()}

        return data


class Relationship(BaseModel):
    entity1: str
    entity2: str
    name: str
    cardinality: Cardinality


class ERModel(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]

    @model_validator(mode="after")
    def validate_model(self) -> "ERModel":
        entity_names = {e.name for e in self.entities}

        if len(self.entities) != len(entity_names):
            raise ValueError("ER Model entities must be unique")

        for relationship in self.relationships:
            for entity in [relationship.entity1, relationship.entity2]:
                if entity not in entity_names:
                    raise ValueError(
                        f'Relationship "{relationship.name}" references unknown entity "{entity}"'
                    )

        return self
