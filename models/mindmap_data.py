# models/mindmap_data.py
"""
マインドマップのデータモデル。

マインドマップ全体（ノードとエッジの集合）を表現し、
シリアライズ/デシリアライズをサポートする。
"""

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class MindMapData:
    """マインドマップ全体のデータ。

    Attributes:
        name: マインドマップの名前。
        nodes: ノードデータのリスト。
        edges: エッジデータのリスト。
        canvas_settings: キャンバス設定（背景色、グリッドなど）。
        metadata: メタデータ（作成日時など）。
    """

    name: str = "Untitled Mind Map"
    nodes: list[dict[str, Any]] = field(default_factory=list)
    edges: list[dict[str, Any]] = field(default_factory=list)
    canvas_settings: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """辞書形式にシリアライズする。"""
        return {
            "name": self.name,
            "nodes": self.nodes,
            "edges": self.edges,
            "canvas_settings": self.canvas_settings,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MindMapData":
        """辞書からインスタンスを生成する。"""
        return cls(
            name=data.get("name", "Untitled Mind Map"),
            nodes=data.get("nodes", []),
            edges=data.get("edges", []),
            canvas_settings=data.get("canvas_settings", {}),
            metadata=data.get("metadata", {}),
        )

    def add_node(self, node_data: dict[str, Any]) -> None:
        """ノードを追加する。"""
        self.nodes.append(node_data)

    def add_edge(self, edge_data: dict[str, Any]) -> None:
        """エッジを追加する。"""
        self.edges.append(edge_data)

    def remove_node_by_uuid(self, uuid: str) -> bool:
        """UUIDでノードを削除する。"""
        for i, node in enumerate(self.nodes):
            if node.get("uuid") == uuid:
                self.nodes.pop(i)
                # 関連エッジも削除
                self.edges = [e for e in self.edges if e.get("source_uuid") != uuid and e.get("target_uuid") != uuid]
                return True
        return False

    def remove_edge_by_uuid(self, uuid: str) -> bool:
        """UUIDでエッジを削除する。"""
        for i, edge in enumerate(self.edges):
            if edge.get("uuid") == uuid:
                self.edges.pop(i)
                return True
        return False

    def find_node_by_uuid(self, uuid: str) -> dict[str, Any] | None:
        """UUIDでノードを検索する。"""
        for node in self.nodes:
            if node.get("uuid") == uuid:
                return node
        return None

    def clear(self) -> None:
        """全データをクリアする。"""
        self.nodes.clear()
        self.edges.clear()
        logger.info(f"MindMapData '{self.name}' cleared")

    @property
    def node_count(self) -> int:
        """ノード数を取得する。"""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """エッジ数を取得する。"""
        return len(self.edges)
