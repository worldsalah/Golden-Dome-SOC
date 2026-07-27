import json
import logging
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import AiAnalysis, DetectionRule, KnowledgeBaseItem

logger = logging.getLogger(__name__)


class RAGRetriever:
    """Lightweight retrieval-augmented generation using TF-IDF over security documents."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)

    async def search(self, query: str, top_k: int = 5) -> list[dict[str, Any]]:
        docs = await self._load_documents()
        if not docs:
            return []

        corpus = [d["text"] for d in docs]
        try:
            vectors = self.vectorizer.fit_transform(corpus)
        except ValueError:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, vectors).flatten()
        indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in indices:
            if scores[idx] <= 0:
                continue
            doc = docs[idx]
            results.append({
                "source": doc["source"],
                "source_id": doc["source_id"],
                "title": doc["title"],
                "text": doc["text"],
                "score": float(round(scores[idx], 4)),
            })
        return results

    async def _load_documents(self) -> list[dict[str, Any]]:
        docs: list[dict[str, Any]] = []

        kb_result = await self.db.execute(select(KnowledgeBaseItem))
        for item in kb_result.scalars().all():
            text = f"{item.name}. {item.tactic or ''} {item.description or ''} {item.recommendations or ''}"
            docs.append({
                "source": "knowledge_base",
                "source_id": item.id,
                "title": item.name,
                "text": text.strip(),
            })

        rule_result = await self.db.execute(select(DetectionRule))
        for rule in rule_result.scalars().all():
            text = f"{rule.name}. {rule.description or ''} Category {rule.category}. Source {rule.source}. MITRE {rule.mitre_attack_id or ''}. Logic {rule.logic}."
            docs.append({
                "source": "detection_rule",
                "source_id": rule.id,
                "title": rule.name,
                "text": text.strip(),
            })

        analysis_result = await self.db.execute(select(AiAnalysis).order_by(AiAnalysis.created_at.desc()).limit(100))
        for analysis in analysis_result.scalars().all():
            text = f"AI analysis summary: {analysis.summary or ''}. Explanation: {analysis.explanation or ''}. Recommendation: {analysis.recommendation or ''}."
            docs.append({
                "source": "ai_analysis",
                "source_id": analysis.id,
                "title": f"Analysis #{analysis.id}",
                "text": text.strip(),
            })

        return docs

    async def build_context(self, query: str, top_k: int = 5) -> str:
        results = await self.search(query, top_k=top_k)
        if not results:
            return "No relevant internal knowledge found."
        parts = []
        for r in results:
            parts.append(f"[{r['source']} - {r['title']}]\n{r['text']}")
        return "\n\n".join(parts)
