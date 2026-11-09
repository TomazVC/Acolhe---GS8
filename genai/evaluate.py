"""Run with python -m genai.evaluate. Metrics concern retrieval, not answer quality."""
import json
from pathlib import Path
from genai.service import retrieve

CASES = [
 ("Como atravessar a rua?", "crossing"), ("¿Cómo cruzar la calle?", "crossing"),
 ("Estou perdido", "lost"), ("Necesito ayuda, estoy perdido", "lost"),
 ("Como digo silla?", "chair"), ("O que é mochila?", "backpack"),
 ("Como digo botella?", "bottle"), ("Vou embarcar no ônibus", "bus"),
 ("Como dizer buenos días?", "greeting"), ("Como digo cuaderno?", "book"),
 ("Posso ir para o outro lado?", "crossing"), ("Cadê quem estava comigo?", "lost"),
 ("Onde coloco meu estojo?", "backpack"), ("Quero me acomodar", "chair"),
 ("Preciso me hidratar", "bottle"), ("Saludamos al amanecer", "greeting"),
]
def recall_at(predictions, expected, k):
    if len(predictions) != len(expected) or k < 1:
        raise ValueError("aligned cases and positive k required")
    return sum(gold in ids[:k] for ids, gold in zip(predictions, expected)) / len(expected) if expected else 0.0

def evaluate():
    rows = [{"question": q, "expected": gold, "retrieved": [x["id"] for x in retrieve(q)]} for q, gold in CASES]
    predictions = [r["retrieved"] for r in rows]
    expected = [r["expected"] for r in rows]
    return {"scope": "lexical retrieval on 16 hand-authored bilingual cases, not independent benchmark or LLM evaluation",
            "recall_at_1": recall_at(predictions, expected, 1), "recall_at_3": recall_at(predictions, expected, 3),
            "cases": rows, "errors": [r for r in rows if r["expected"] not in r["retrieved"][:1]]}

if __name__ == "__main__":
    print(json.dumps(evaluate(), ensure_ascii=False, indent=2))
