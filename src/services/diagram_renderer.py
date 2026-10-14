import asyncio
import base64
import json
from abc import ABC, abstractmethod
from typing import Protocol

import flet as ft
import flet_webview as fwv
from graphviz import Graph
from graphviz.dot import Dot

from models import (
    Attribute,
    Cardinality,
    Entity,
    Model,
    Participation,
    ParticipationConstraint,
    Relationship,
)
from utils import get_assets_directory


class DiagramRenderer(Protocol):
    def render(self, model: Model) -> bytes: ...


class DotDiagramRenderer(ABC):
    def _generate_dot(self, model: Model) -> Graph:
        def draw_model(dot: Dot, model: Model):
            for entity in model.entities:
                draw_entity(dot, entity)

            for relationship in model.relationships:
                draw_relationship(dot, relationship)

        def draw_entity(dot: Dot, entity: Entity) -> None:
            entity_id = entity.name

            dot.node(
                entity.name,
                shape="box",
                peripheries=("2" if entity.is_weak else "1"),
            )

            for attribute in entity.attributes:
                draw_attribute(dot, entity_id, attribute)

        def draw_relationship(dot: Dot, relationship: Relationship) -> None:
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
        ) -> None:
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
                    taillabel=label,
                    labeldistance="2",
                    labelangle="35",
                    label=participation.role,
                    penwidth="1",
                    color="black:invis:black",
                )
            else:
                dot.edge(
                    relationship_id,
                    entity_id,
                    taillabel=label,
                    labeldistance="2",
                    labelangle="35",
                    label=participation.role,
                )

        def draw_attribute(dot: Dot, owner_id: str, attribute: Attribute) -> None:
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

            for sub_attribute in attribute.sub_attributes:
                draw_attribute(dot, attribute_id, sub_attribute)

            dot.edge(owner_id, attribute_id, len="0.5")

        dot = Graph(engine="neato")

        dot.attr(overlap="false", splines="true", esep="+12")

        draw_model(dot, model)

        return dot

    @abstractmethod
    def render(self, model: Model) -> bytes:
        pass


class GraphvizDiagramRenderer(DotDiagramRenderer):
    def render(self, model: Model) -> bytes:
        dot = self._generate_dot(model)

        return dot.pipe(format="png")


class VizJsDiagramRenderer(DotDiagramRenderer):
    def __init__(self, page: ft.Page):
        self.page = page
        self.event_loop = None
        self.ready_event = None
        self.render_future = None
        self.image_chunks = {}
        self.is_started = False
        self.web_view = fwv.WebView(
            url="about:blank",
            width=1,
            height=1,
            on_console_message=self.on_console_message,
        )

    async def ensure_webview_started(self):
        if self.is_started:
            return

        self.is_started = True
        self.ready_event = asyncio.Event()
        self.page.overlay.append(self.web_view)
        self.page.update()

        await asyncio.sleep(0.5)
        await self.web_view.load_html(self.html(), base_url="https://localhost/")
        await asyncio.wait_for(self.ready_event.wait(), timeout=60)

    def render(self, model: Model) -> bytes:
        return asyncio.run(self.render_async(model))

    async def render_async(self, model: Model) -> bytes:
        self.event_loop = asyncio.get_running_loop()

        await self.ensure_webview_started()
        self.image_chunks = {}
        self.render_future = self.event_loop.create_future()

        dot = self._generate_dot(model)

        await self.web_view.run_javascript(f"render({json.dumps(dot.source)})")
        return await asyncio.wait_for(self.render_future, timeout=60)

    def on_console_message(self, event):
        if self.event_loop is not None and not self.event_loop.is_closed():
            try:
                self.event_loop.call_soon_threadsafe(
                    self.handle_console_message, event.message
                )
            except RuntimeError:
                pass

    def handle_console_message(self, message: str):
        if message.startswith("READY|"):
            if self.ready_event:
                self.ready_event.set()

        elif message.startswith("CHUNK|"):
            _, chunk_index_str, total_chunks_str, chunk_data = message.split("|", 3)
            chunk_index = int(chunk_index_str)
            total_chunks = int(total_chunks_str)

            self.image_chunks[chunk_index] = chunk_data

            if (
                len(self.image_chunks) == total_chunks
                and self.render_future
                and not self.render_future.done()
            ):
                encoded_base64 = "".join(
                    self.image_chunks[key] for key in range(total_chunks)
                )
                decoded_bytes = base64.b64decode(encoded_base64)
                self.render_future.set_result(decoded_bytes)

        elif (
            message.startswith("ERROR|")
            and self.render_future
            and not self.render_future.done()
        ):
            self.render_future.set_exception(RuntimeError(message[4:]))

    @staticmethod
    def html() -> str:
        viz_js = (get_assets_directory() / "viz.js").read_text(encoding="utf-8")

        return f"""<!doctype html>
<html>
<body>
<script>{viz_js}</script>
<script>
async function render(dotSource) {{
  try {{
    const viz = await Viz.instance();
    const svg = viz.renderString(dotSource, {{
      format: "svg",
      engine: "neato",
      edgeAttributes: {{ len: "4" }}
    }});
    
    const image = new Image();
    image.onload = () => {{
      const canvas = document.createElement("canvas");
      canvas.width = image.naturalWidth;
      canvas.height = image.naturalHeight;
      
      const context = canvas.getContext("2d");
      context.fillStyle = "white";
      context.fillRect(0, 0, canvas.width, canvas.height);
      context.drawImage(image, 0, 0, canvas.width, canvas.height);
      
      const base64Data = canvas.toDataURL("image/png").split(",")[1];
      const chunkSize = 100000;
      const totalChunks = Math.ceil(base64Data.length / chunkSize);
      
      for (let index = 0; index < totalChunks; index++) {{
        const slice = base64Data.slice(index * chunkSize, (index + 1) * chunkSize);
        console.log("CHUNK|" + index + "|" + totalChunks + "|" + slice);
      }}
    }};
    
    image.onerror = () => console.log("ERROR|SVG rendering failed");
    image.src = "data:image/svg+xml;charset=utf-8," + encodeURIComponent(svg);
  }} catch (error) {{
    console.log("ERROR|" + error);
  }}
}}

console.log("READY|");
</script>
</body>
</html>"""


def create_diagram_renderer() -> DiagramRenderer:
    if ft.context.page.platform in [ft.PagePlatform.IOS, ft.PagePlatform.ANDROID]:
        return VizJsDiagramRenderer(ft.context.page)

    return GraphvizDiagramRenderer()
