from pathlib import Path
import networkx as nx
from typing import List, Dict, Set, Tuple
from .static_analyzer import StaticAnalyzer

class DependencyGraph:
    def __init__(self, root_path: Path):
        self.root_path = root_path
        self.graph = nx.DiGraph()
        self.file_map: Dict[str, Path] = {} # Module name -> File Path

    def build(self):
        # 1. Map all python files
        for py_file in self.root_path.rglob("*.py"):
            module_name = self._to_module_name(py_file)
            self.file_map[module_name] = py_file
            self.graph.add_node(module_name, type="internal")

        # 2. Add edges
        for module_name, file_path in self.file_map.items():
            analyzer = StaticAnalyzer(file_path)
            stats = analyzer.analyze()
            
            for imp in stats.imports:
                # Resolve import to node
                target = self._resolve_import(imp)
                if target:
                   self.graph.add_edge(module_name, target)
                else:
                    # External dependency
                    if imp not in self.graph:
                        self.graph.add_node(imp, type="external")
                    self.graph.add_edge(module_name, imp)

    def _to_module_name(self, file_path: Path) -> str:
        rel = file_path.relative_to(self.root_path)
        return str(rel.with_suffix("")).replace("\\", ".").replace("/", ".")

    def _resolve_import(self, import_name: str) -> str:
        # Exact match
        if import_name in self.file_map:
            return import_name
        # Match sub-module (e.g. app.utils.helper -> app.utils)
        parts = import_name.split(".")
        for i in range(len(parts), 0, -1):
            sub = ".".join(parts[:i])
            if sub in self.file_map:
                return sub
        return None

    def detect_cycles(self) -> List[List[str]]:
        try:
            return list(nx.simple_cycles(self.graph))
        except nx.NetworkXException:
            logger.exception("Unexpected Network failure during cycle detection")
            raise

    def get_coupling_metrics(self) -> Dict[str, Dict[str, int]]:
        metrics = {}
        for node in self.graph.nodes:
            if self.graph.nodes[node].get("type") == "internal":
                metrics[node] = {
                    "fan_in": self.graph.in_degree(node),
                    "fan_out": self.graph.out_degree(node)
                }
        return metrics
