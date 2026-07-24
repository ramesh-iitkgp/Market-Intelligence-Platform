"""RAG Prompt Builder Service: Converts structured context to an LLM prompt."""

from __future__ import annotations
import logging

from backend.schemas.rag_schemas import PromptDiagnostics, RAGContext
from backend.services.llm.tokenizer import Tokenizer


class PromptBuilderService:
    """Builds an LLM-ready prompt from a structured RAGContext object."""

    def __init__(
        self, tokenizer: Tokenizer, max_tokens: int = 8000, logger: logging.Logger | None = None
    ):
        self._max_tokens = max_tokens
        self._tokenizer = tokenizer
        self._logger = logger or logging.getLogger(__name__)

    def build_prompt(
        self, context: RAGContext
    ) -> tuple[str, PromptDiagnostics]:
        """
        Constructs a detailed, evidence-based prompt for a reasoning engine.

        Args:
            context: The structured context object from the assembly service.

        Returns:
            A tuple containing the final prompt string and diagnostic information.
        """
        base_prompt_parts = []
        context_parts = []

        # 1. Add the main query
        if context.query_event:
            base_prompt_parts.append("## Primary Event Under Analysis")
            base_prompt_parts.append(f"**Event Title:** {context.query_event.title}")
            base_prompt_parts.append(f"**Date:** {context.query_event.occurred_at.date()}")
            base_prompt_parts.append(f"**Description:** {context.query_event.description}")
        elif context.query_text:
            base_prompt_parts.append("## Primary Query")
            base_prompt_parts.append(context.query_text)
        base_prompt_parts.append("\n---")

        # 2. Add Similar Historical Events
        if context.similar_events:
            part = ["## Similar Historical Events (for context)"]
            for item in context.similar_events:
                # The item can be a dict or a Pydantic model, handle appropriately
                event_title = item.item.get("title", "N/A") if isinstance(item.item, dict) else item.item.title
                event_id = item.item.get("id", "N/A") if isinstance(item.item, dict) else item.item.id
                event_date = item.item.get("occurred_at", "N/A") if isinstance(item.item, dict) else item.item.occurred_at.date()
                event_desc = item.item.get("description", "N/A") if isinstance(item.item, dict) else item.item.description

                part.append(f"### Historical Event: {event_title} (ID: {event_id})")
                part.append(f"**Date:** {event_date}")
                part.append(f"**Similarity Score:** {item.evidence.final_score:.2f}")
                part.append(f"**Summary:** {event_desc}")
                part.append(
                    f"**Reason for Similarity:** {item.evidence.metadata.get('explanation', 'N/A')}"
                )
            context_parts.append("\n".join(part))

        # 3. Add Timeline Context
        if context.timeline_context:
            part = ["## Immediate Timeline Context"]
            for item in context.timeline_context:
                event_title = item.item.get("title", "N/A") if isinstance(item.item, dict) else item.item.title
                event_id = item.item.get("id", "N/A") if isinstance(item.item, dict) else item.item.id
                event_date = item.item.get("occurred_at", "N/A") if isinstance(item.item, dict) else item.item.occurred_at.date()
                context_type = item.evidence.metadata.get("context", "related")
                part.append(f"- **({context_type.replace('_', ' ').title()})** {event_title} (ID: {event_id}) on {event_date}")
            context_parts.append("\n".join(part))
        
        # Add Graph Context
        if hasattr(context, "graph_neighborhood") and context.graph_neighborhood:
            part = ["## Key Connected Entities (from Knowledge Graph)"]
            for item in context.graph_neighborhood:
                node_name = item.item.get("canonical_name", "N/A") if isinstance(item.item, dict) else item.item.canonical_name
                node_type = item.item.get("entity_type", "N/A") if isinstance(item.item, dict) else item.item.entity_type.value
                part.append(f"- **{node_name}** (Type: {node_type}) - Score: {item.evidence.final_score:.2f}")
            context_parts.append("\n".join(part))

        # 4. Build final prompt with token management
        final_prompt_parts = base_prompt_parts
        current_tokens = self._tokenizer.count_tokens("\n".join(final_prompt_parts))
        items_included = 0
        items_truncated = 0

        for part in context_parts:
            part_tokens = self._tokenizer.count_tokens(part)
            if current_tokens + part_tokens < self._max_tokens:
                final_prompt_parts.append(part)
                current_tokens += part_tokens
                items_included += 1
            else:
                self._logger.warning("Prompt exceeded max tokens. Truncating context.")
                items_truncated += 1

        final_prompt = "\n".join(final_prompt_parts)
        diagnostics = PromptDiagnostics(
            token_limit=self._max_tokens,
            total_tokens_used=self._tokenizer.count_tokens(final_prompt),
            items_included=items_included,
            items_truncated=items_truncated,
        )

        return final_prompt, diagnostics