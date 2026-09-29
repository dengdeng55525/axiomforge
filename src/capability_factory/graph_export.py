"""Deterministic, dependency-light GraphML export for the capability graph.

The SQLite property graph is the source of truth.  This module deliberately
serializes node and edge properties as JSON strings inside GraphML ``data``
elements so nested provenance facts survive a round trip through tools such as
Gephi, yEd, NetworkX, and Neo4j import adapters without pretending that every
property has a scalar schema.
"""

from __future__ import annotations

import hashlib
import json
import re
import xml.etree.ElementTree as ET
from collections.abc import Mapping
from pathlib import Path
from typing import Any

GRAPHML_NAMESPACE = "http://graphml.graphdrawing.org/xmlns"
ET.register_namespace("", GRAPHML_NAMESPACE)


class GraphExportError(ValueError):
    """The graph snapshot cannot be represented as a valid GraphML document."""


def _safe_text(value: Any) -> str:
    """Encode a value deterministically and remove XML 1.0 control characters."""

    if isinstance(value, (dict, list, tuple)):
        text = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    elif value is None:
        text = "null"
    elif isinstance(value, bool):
        text = "true" if value else "false"
    else:
        text = str(value)
    # XML 1.0 accepts tab, LF and CR; other C0 controls are invalid even when
    # ElementTree escapes their surrounding text.
    return "".join(char for char in text if char in "\t\n\r" or ord(char) >= 0x20)


def _xml_id(value: str, prefix: str) -> str:
    """Return an XML Name-safe ID, preserving ordinary graph IDs verbatim."""

    if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_.:-]*", value):
        return value
    return f"{prefix}_{hashlib.sha256(value.encode('utf-8')).hexdigest()[:20]}"


def _check_graph(graph: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not isinstance(graph, Mapping):
        raise GraphExportError("Graph snapshot must be an object")
    nodes = graph.get("nodes")
    edges = graph.get("edges")
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise GraphExportError("Graph snapshot requires nodes and edges arrays")
    normalized_nodes: list[dict[str, Any]] = []
    node_ids: set[str] = set()
    for item in nodes:
        if not isinstance(item, Mapping) or not isinstance(item.get("id"), str) or not item["id"].strip():
            raise GraphExportError("Every graph node requires a nonempty string id")
        identity = item["id"]
        if identity in node_ids:
            raise GraphExportError(f"Duplicate graph node id: {identity}")
        node_ids.add(identity)
        properties = item.get("properties", {})
        if not isinstance(properties, Mapping):
            raise GraphExportError(f"Node properties must be an object: {identity}")
        normalized_nodes.append({"id": identity, "kind": item.get("kind", ""),
                                 "label": item.get("label", ""), "properties": dict(properties)})
    normalized_edges: list[dict[str, Any]] = []
    edge_ids: set[str] = set()
    for item in edges:
        if not isinstance(item, Mapping):
            raise GraphExportError("Every graph edge must be an object")
        identity = item.get("id")
        source, target = item.get("source"), item.get("target")
        if not isinstance(identity, str) or not identity.strip() or not isinstance(source, str) or not isinstance(target, str):
            raise GraphExportError("Every graph edge requires id, source, and target strings")
        if identity in edge_ids:
            raise GraphExportError(f"Duplicate graph edge id: {identity}")
        if source not in node_ids or target not in node_ids:
            raise GraphExportError(f"Graph edge references an unknown endpoint: {identity}")
        properties = item.get("properties", {})
        if not isinstance(properties, Mapping):
            raise GraphExportError(f"Edge properties must be an object: {identity}")
        edge_ids.add(identity)
        normalized_edges.append({"id": identity, "source": source, "target": target,
                                 "relation": item.get("relation", ""), "properties": dict(properties)})
    return normalized_nodes, normalized_edges


def graphml_document(graph: Mapping[str, Any]) -> str:
    """Render a graph snapshot as deterministic UTF-8 GraphML text.

    ``kind``, ``label`` and ``properties_json`` are node attributes; ``relation``
    and ``properties_json`` are edge attributes.  The original IDs are retained
    in ``node_id``/``edge_id`` data fields when an XML-safe surrogate is needed.
    """

    nodes, edges = _check_graph(graph)
    key = ET.QName(GRAPHML_NAMESPACE, "key")
    data = ET.QName(GRAPHML_NAMESPACE, "data")
    root = ET.Element(ET.QName(GRAPHML_NAMESPACE, "graphml"))
    key_specs = [
        ("node_kind", "node", "kind"), ("node_label", "node", "label"),
        ("node_id", "node", "original_id"), ("node_properties", "node", "properties_json"),
        ("edge_relation", "edge", "relation"), ("edge_id", "edge", "original_id"),
        ("edge_properties", "edge", "properties_json"),
    ]
    for key_id, scope, name in key_specs:
        ET.SubElement(root, key, {"id": key_id, "for": scope, "attr.name": name, "attr.type": "string"})
    graph_element = ET.SubElement(root, ET.QName(GRAPHML_NAMESPACE, "graph"),
                                  {"id": "capability_factory", "edgedefault": "directed"})
    node_xml_ids = {item["id"]: _xml_id(item["id"], "node") for item in nodes}
    for item in nodes:
        node = ET.SubElement(graph_element, ET.QName(GRAPHML_NAMESPACE, "node"), {"id": node_xml_ids[item["id"]]})
        values = [("node_kind", item["kind"]), ("node_label", item["label"]),
                  ("node_id", item["id"]), ("node_properties", item["properties"])]
        for key_id, value in values:
            ET.SubElement(node, data, {"key": key_id}).text = _safe_text(value)
    for item in edges:
        edge = ET.SubElement(graph_element, ET.QName(GRAPHML_NAMESPACE, "edge"), {
            "id": _xml_id(item["id"], "edge"), "source": node_xml_ids[item["source"]],
            "target": node_xml_ids[item["target"]],
        })
        values = [("edge_relation", item["relation"]), ("edge_id", item["id"]),
                  ("edge_properties", item["properties"])]
        for key_id, value in values:
            ET.SubElement(edge, data, {"key": key_id}).text = _safe_text(value)
    body = ET.tostring(root, encoding="unicode", short_empty_elements=True)
    return "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" + body + "\n"


def write_graphml(path: str | Any, graph: Mapping[str, Any]) -> dict[str, Any]:
    """Write GraphML and return a compact manifest useful in CLI/report logs."""

    target = path if hasattr(path, "write_text") else Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    content = graphml_document(graph)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "nodes": len(graph.get("nodes", [])), "edges": len(graph.get("edges", [])),
            "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest()}


__all__ = ["GraphExportError", "graphml_document", "write_graphml"]
