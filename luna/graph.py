"""LangGraph assembly for LUNA."""

from __future__ import annotations

from langgraph.graph import END, START, StateGraph

from luna.agents import (
    build_query,
    final_synthesizer,
    make_compute_uncertainty,
    make_deep_audit_agent,
    make_lore_agent,
    make_meaning_agent,
    make_retrieve_node,
    route_by_uncertainty,
    make_style_agent,
)
from luna.config import DeepSeekConfig, LunaPaths, RetrievalConfig
from luna.deepseek_client import DeepSeekClient
from luna.retriever import LunaRetriever
from luna.state import LunaState


def build_luna_graph(
    paths: LunaPaths | None = None,
    retrieval_config: RetrievalConfig | None = None,
    deepseek_config: DeepSeekConfig | None = None,
    use_retrieval: bool = True,
):
    paths = paths or LunaPaths()
    deepseek_config = deepseek_config or DeepSeekConfig()
    llm_client = None
    if deepseek_config.use_llm:
        if not deepseek_config.api_key:
            raise RuntimeError(
                f"DeepSeek LLM mode is enabled, but {deepseek_config.api_key_env} is not set. "
                "Set the environment variable, or pass --no-llm to intentionally use scaffold scoring."
            )
        llm_client = DeepSeekClient(deepseek_config)
    retriever = None
    if use_retrieval:
        retriever = LunaRetriever(
            db_dir=paths.vector_db_dir,
            collection_name=paths.collection_name,
            config=retrieval_config or RetrievalConfig(),
        )

    def no_retrieval_node(_state: LunaState) -> dict:
        return {"evidence": []}

    builder = StateGraph(LunaState)
    builder.add_node("build_query", build_query)
    builder.add_node(
        "retrieve_evidence",
        make_retrieve_node(retriever) if retriever is not None else no_retrieval_node,
    )
    builder.add_node("meaning_agent", make_meaning_agent(llm_client, deepseek_config))
    builder.add_node("lore_agent", make_lore_agent(llm_client, deepseek_config))
    builder.add_node("style_agent", make_style_agent(llm_client, deepseek_config))
    builder.add_node(
        "compute_uncertainty",
        make_compute_uncertainty(
            deepseek_config.routing_threshold,
            deepseek_config.low_score_threshold,
            deepseek_config.low_average_threshold,
        ),
    )
    builder.add_node("deep_audit", make_deep_audit_agent(llm_client, deepseek_config))
    builder.add_node("finalize", final_synthesizer)

    builder.add_edge(START, "build_query")
    builder.add_edge("build_query", "retrieve_evidence")
    builder.add_edge("retrieve_evidence", "meaning_agent")
    builder.add_edge("retrieve_evidence", "lore_agent")
    builder.add_edge("retrieve_evidence", "style_agent")
    builder.add_edge("meaning_agent", "compute_uncertainty")
    builder.add_edge("lore_agent", "compute_uncertainty")
    builder.add_edge("style_agent", "compute_uncertainty")
    builder.add_conditional_edges(
        "compute_uncertainty",
        route_by_uncertainty,
        {"deep_audit": "deep_audit", "finalize": "finalize"},
    )
    builder.add_edge("deep_audit", "finalize")
    builder.add_edge("finalize", END)
    return builder.compile()
