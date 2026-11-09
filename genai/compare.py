"""Real local LLM only. Never writes fabricated baseline/RAG/agent scores."""
import argparse
import json
import time
from genai.service import generate, retrieve

def compare(question, model):
    results = []
    for mode in ("baseline", "rag", "agent"):
        start = time.perf_counter()
        context = []
        trace = []
        try:
            if mode == "rag":
                context = retrieve(question)
            elif mode == "agent":
                plan = generate('Choose one tool: retrieve or refuse. Return JSON with tool and query. Question: ' + json.dumps(question), model)
                trace.append({"decision": plan})
                if plan.get("tool") != "retrieve" or not isinstance(plan.get("query"), str):
                    results.append({"mode": mode, "status": "refused", "trace": trace})
                    continue
                context = retrieve(plan["query"][:1000])
                trace.append({"tool": "retrieve", "ids": [d["id"] for d in context]})
            result = generate('Educational experiment, not child-facing. Answer in Portuguese; JSON answer and sources. Use supplied context only when supplied. ' + json.dumps({"question": question, "context": context}, ensure_ascii=False), model)
            results.append({"mode": mode, "status": "executed", "output": result, "trace": trace, "seconds": round(time.perf_counter()-start, 3)})
        except (OSError, ValueError, KeyError, RuntimeError) as exc:
            results.append({"mode": mode, "status": "blocked", "error": str(exc), "trace": trace})
    return results

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--question", default="Como atravessar a rua?")
    a = p.parse_args()
    print(json.dumps(compare(a.question, a.model), ensure_ascii=False, indent=2))
