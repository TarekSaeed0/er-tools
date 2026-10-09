from enum import StrEnum

from pydantic import BaseModel, field_validator, model_validator, Field


class Attribute(BaseModel):
    name: str
    is_primary_key: bool = False
    is_partial_key: bool = False
    is_multivalued: bool = False
    is_derived: bool = False
    sub_attributes: list["Attribute"] = []

    @field_validator("sub_attributes")
    @classmethod
    def validate_sub_attributes(
        cls, sub_attributes: list["Attribute"] | None
    ) -> list["Attribute"] | None:
        if sub_attributes is not None:
            if len(sub_attributes) != len(set(a.name for a in sub_attributes)):
                raise ValueError("Sub-attributes must be unique")

        return sub_attributes

    @model_validator(mode="after")
    def validate_attribute(self) -> "Attribute":
        if self.is_primary_key and self.is_partial_key:
            raise ValueError(
                f'Attribute "{self.name}" can\'t be both a primary key and a partial key'
            )
        return self


class Entity(BaseModel):
    name: str
    is_weak: bool = False
    attributes: list[Attribute] = []

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, attributes: list[Attribute]) -> list[Attribute]:
        if len(attributes) != len({a.name for a in attributes}):
            raise ValueError("Entity attributes must be unique")

        return attributes

    @model_validator(mode="after")
    def validate_entity(self) -> "Entity":
        has_primary_key = any(a.is_primary_key for a in self.attributes)
        has_partial_key = any(a.is_partial_key for a in self.attributes)

        if self.is_weak:
            if has_primary_key:
                raise ValueError(f'Weak entity "{self.name}" can\'t have a primary key')
            if not has_partial_key:
                raise ValueError(f'Weak entity "{self.name}" must have a partial key')
        else:
            if not has_primary_key:
                raise ValueError(f'Strong entity "{self.name}" must have a primary key')
            if has_partial_key:
                raise ValueError(
                    f'Strong entity "{self.name}" can\'t have a partial key'
                )

        return self


class Cardinality(StrEnum):
    ONE = "one"
    MANY = "many"


class ParticipationConstraint(StrEnum):
    PARTIAL = "partial"
    TOTAL = "total"


class Participation(BaseModel):
    entity_name: str
    role: str | None = None
    cardinality: Cardinality = Cardinality.MANY
    constraint: ParticipationConstraint = ParticipationConstraint.PARTIAL


class Relationship(BaseModel):
    name: str
    is_identifying: bool = False
    participations: list[Participation] = Field(min_length=2)
    attributes: list[Attribute] = []

    @field_validator("attributes")
    @classmethod
    def validate_attributes(cls, attributes: list[Attribute]) -> list[Attribute]:
        if len(attributes) != len({a.name for a in attributes}):
            raise ValueError("Relationship attributes must be unique")

        return attributes

    @property
    def degree(self) -> int:
        return len(self.participations)


class Model(BaseModel):
    entities: list[Entity]
    relationships: list[Relationship]

    @model_validator(mode="after")
    def validate_model(self) -> "Model":
        entity_map = {e.name: e for e in self.entities}

        if len(self.entities) != len(entity_map):
            raise ValueError("Model entities must be unique")

        for relationship in self.relationships:
            for participant in relationship.participations:
                if participant.entity_name not in entity_map:
                    raise ValueError(
                        f'Relationship "{relationship.name}" references an unknown entity "{participant.entity_name}"'
                    )

            if relationship.is_identifying:
                if not any(
                    not entity_map[p.entity_name].is_weak
                    for p in relationship.participations
                ):
                    raise ValueError(
                        f'Identifying relationship "{relationship.name}" must have at least one strong entity participating'
                    )

                if not any(
                    entity_map[p.entity_name].is_weak
                    for p in relationship.participations
                ):
                    raise ValueError(
                        f'Identifying relationship "{relationship.name}" must have at least one weak entity participating'
                    )

        weak_entities = {e.name for e in self.entities if e.is_weak}

        identifying_relationship_participants = {
            p.entity_name
            for r in self.relationships
            for p in r.participations
            if r.is_identifying
        }

        missing_identifying_relationship = (
            weak_entities - identifying_relationship_participants
        )

        if missing_identifying_relationship:
            missing_names = ", ".join(
                f'"{name}"' for name in missing_identifying_relationship
            )

            raise ValueError(
                f"Weak entities {missing_names} must participate in at least one identifying relationship"
            )

        return self
