import argparse
from pathlib import Path

from graphviz import Graph
from graphviz.dot import Dot
from pydantic import ValidationError

from models import (
    Attribute,
    Model,
    Entity,
    Participation,
    Relationship,
    Cardinality,
    ParticipationConstraint,
)


def draw_model(dot: Dot, model: Model):
    for entity in model.entities:
        draw_entity(dot, entity)

    for relationship in model.relationships:
        draw_relationship(dot, relationship)


def draw_entity(dot: Dot, entity: Entity):
    entity_id = entity.name

    dot.node(
        entity.name,
        shape="box",
        peripheries=("2" if entity.is_weak else "1"),
    )

    for attribute in entity.attributes:
        draw_attribute(dot, entity_id, attribute)


def draw_relationship(dot: Dot, relationship: Relationship):
    relationship_id = f"{relationship.name}-{'-'.join(p.entity_name for p in relationship.participations)}"

    dot.node(
        relationship_id,
        label=relationship.name,
        shape="diamond",
        peripheries=("2" if relationship.is_identifying else "1"),
    )

    for attribute in relationship.attributes:
        draw_attribute(dot, relationship_id, attribute)

    many_participations_before = 0
    for participation in relationship.participations:
        draw_participation(
            dot, relationship_id, participation, many_participations_before
        )

        if participation.cardinality == Cardinality.MANY:
            many_participations_before += 1


def draw_participation(
    dot: Dot,
    relationship_id: str,
    participation: Participation,
    many_participations_before: int,
):
    entity_id = participation.entity_name

    label: str
    match participation.cardinality:
        case Cardinality.ONE:
            label = "1"
        case Cardinality.MANY:
            label = "NMPQORSTUVWXYZABCDEFGHIJKL"[many_participations_before]

    if participation.constraint == ParticipationConstraint.TOTAL:
        dot.edge(
            relationship_id,
            entity_id,
            label=label,
            penwidth="1",
            color="black:invis:black",
        )
    else:
        dot.edge(relationship_id, entity_id, label=label)


def draw_attribute(dot: Dot, owner_id: str, attribute: Attribute):
    attribute_id = f"{owner_id}-{attribute.name}"

    dot.node(
        attribute_id,
        label=f"""<
            <table border="0" cellborder="0" cellspacing="0" cellpadding="0">
                <tr><td border="1" sides="b">{attribute.name}</td></tr>
            </table>
        >"""
        if attribute.is_primary_key
        else f"""<
            <table border="0" cellborder="0" cellspacing="0" cellpadding="0">
                <tr><td border="1" style="dashed" sides="b">{attribute.name}</td></tr>
            </table>
        >"""
        if attribute.is_partial_key
        else attribute.name,
        peripheries=("2" if attribute.is_multivalued else "1"),
        style="dashed" if attribute.is_derived else "solid",
    )

    if attribute.sub_attributes is not None:
        for sub_attribute in attribute.sub_attributes:
            draw_attribute(dot, attribute_id, sub_attribute)

    dot.edge(owner_id, attribute_id, len="0.5")


def main():
    parser = argparse.ArgumentParser(
        prog="generate-diagram",
        description="script for generating ER digrams from json",
    )
    parser.add_argument("filename", type=Path)

    args = parser.parse_args()

    filename: Path = args.filename

    try:
        model = Model.model_validate_json(filename.read_text())
    except FileNotFoundError:
        parser.error(f"file not found: {filename}")
    except ValidationError as e:
        parser.error(f"invalid ER Model:\n{e}")

    dot = Graph("ER Diagram", engine="neato", format="png")

    dot.attr(overlap="false")
    dot.attr(mode="KK")
    dot.attr(maxiter="100000")

    draw_model(dot, model)

    dot.render(f"diagrams/{filename.stem}", view=True, cleanup=True)


if __name__ == "__main__":
    main()
