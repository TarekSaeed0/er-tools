import argparse
from models import ERModel
from pathlib import Path
from pydantic import ValidationError
from devtools import pprint
from graphviz import Graph


def main():
    parser = argparse.ArgumentParser(
        prog="er-diagram-generator",
        description="script for generating ER digrams from json",
    )
    parser.add_argument("filename", type=Path)

    args = parser.parse_args()

    try:
        model = ERModel.model_validate_json(args.filename.read_text())
    except FileNotFoundError:
        parser.error(f"file not found: {args.filename}")
    except ValidationError as e:
        parser.error(f"invalid ER Model:\n{e}")

    pprint(model)

    dot = Graph("ER Diagram", format="png")

    dot.attr(rankdir="LR")

    for entity in model.entities:
        dot.node(
            entity.name,
            shape="box",
            style="filled",
            bgcolor="gray",
        )

        for attribute in entity.attributes:
            attribute_id = f"{entity.name}-{attribute.name}"
            dot.node(
                attribute_id,
                label=f"<<u>{attribute.name}</u>>"
                if attribute.isPrimaryKey
                else attribute.name,
                peripheries=("2" if attribute.isMultiValued else "1"),
            )

            if attribute.composite is not None:
                for name in attribute.composite:
                    composite_id = f"{attribute_id}-{name}"
                    dot.node(composite_id, label=name)

                    dot.edge(attribute_id, composite_id)

            dot.edge(entity.name, attribute_id)

    for relationship in model.relationships:
        relationship_id = (
            f"{relationship.name}-{relationship.entity1}-{relationship.entity2}"
        )
        dot.node(
            relationship_id,
            label=relationship.name,
            shape="diamond",
            style="filled",
            bgcolor="gray",
        )

        dot.edge(
            relationship.entity1, relationship_id, label=relationship.cardinality.left
        )
        dot.edge(
            relationship_id, relationship.entity2, label=relationship.cardinality.right
        )

    dot.render("er-digram", view=True, cleanup=True)


if __name__ == "__main__":
    main()
