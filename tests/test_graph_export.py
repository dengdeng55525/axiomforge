"""GraphML export preserves graph facts and rejects malformed snapshots."""

import xml.etree.ElementTree as ET

import pytest

from capability_factory.graph_export import GraphExportError, graphml_document


def test_graphml_is_deterministic_and_keeps_nested_properties():
    graph = {
        "nodes": [
            {"id": "capability:bank v1", "kind": "Capability", "label": "响应预测",
             "properties": {"tags": ["bank", "ap"], "provenance": {"sha": "abc"}}},
            {"id": "source:uci", "kind": "Source", "label": "UCI", "properties": {"license": "CC"}},
        ],
        "edges": [{"id": "edge-1", "source": "capability:bank v1", "target": "source:uci",
                   "relation": "DERIVED_FROM", "properties": {"locator": {"line": [1, 2]}}}],
    }
    first, second = graphml_document(graph), graphml_document(graph)
    assert first == second
    root = ET.fromstring(first)
    namespace = {"g": "http://graphml.graphdrawing.org/xmlns"}
    assert len(root.findall("g:graph/g:node", namespace)) == 2
    assert len(root.findall("g:graph/g:edge", namespace)) == 1
    values = [item.text or "" for item in root.findall(".//g:data", namespace)]
    assert any('"provenance":{"sha":"abc"}' in value for value in values)
    # The whitespace-containing ID is represented by a safe XML ID and retained
    # exactly as a data attribute for import adapters.
    assert "capability:bank v1" in values


def test_graphml_rejects_duplicate_or_dangling_graph_facts():
    with pytest.raises(GraphExportError, match="Duplicate graph node"):
        graphml_document({"nodes": [{"id": "a"}, {"id": "a"}], "edges": []})
    with pytest.raises(GraphExportError, match="unknown endpoint"):
        graphml_document({"nodes": [{"id": "a"}],
                          "edges": [{"id": "e", "source": "a", "target": "missing"}]})


def test_graphml_rejects_non_object_properties():
    with pytest.raises(GraphExportError, match="Node properties"):
        graphml_document({"nodes": [{"id": "a", "properties": []}], "edges": []})
