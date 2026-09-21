# GraphRAG architecture

Entity graph over the **DataCo + Online Retail II extract**, not a live OMS graph.

```
Customer(segment) → Warehouse → Region
                 ↘ Product → Supplier → Warehouse
Warehouse → Inventory
```

| Piece | Path | Honest behavior |
|---|---|---|
| Snapshot | `artifacts/graph_snapshot.json` | 41 nodes / 112 edges, built from parquet |
| In-process API | `ai/graphrag/retrieve.py` | Rank suppliers by late-line $, join segments via warehouses |
| NetworkX | `ai/graphrag/graph.py::to_networkx` | Optional extra; dict graph is the default |
| Neo4j | `ai/graphrag/neo4j_adapter.py` | Idle unless `NEO4J_URI` is set **and** the driver connects |
| Rebuild | `ai/graphrag/ingest.py` | Requires pandas; does not silently overwrite the committed snapshot |

Customer nodes are **segments** (Consumer / Corporate / Home Office). Names from `dim_customer` are not ingested.

Example questions implemented:

- Which suppliers are indirectly responsible for OTIF failures?
- Which customers are affected by a supplier disruption?
- What dependencies exist between warehouses and suppliers?

Late-line $ on an edge is **overlap exposure**, not a causal claim that the supplier caused the OTIF miss.
