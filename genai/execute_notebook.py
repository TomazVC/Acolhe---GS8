"""Execute our small standard-library notebook cells and capture actual stdout (no fake outputs)."""
import contextlib
import io
import json
from pathlib import Path

def run():
    source = [
        "import json\nfrom genai.evaluate import evaluate\nreport = evaluate()\nprint(json.dumps(report, ensure_ascii=False, indent=2))",
        "from genai.service import answer\nprint(json.dumps(answer('Como atravessar a rua?', 'pt'), ensure_ascii=False, indent=2))"
    ]
    cells = [{"cell_type":"markdown","metadata":{},"source":["# Avaliação real da recuperação\nExecutado com Python stdlib. Não executa LLM."]}]
    namespace = {}
    for i, code in enumerate(source, 1):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            exec(compile(code, "<notebook-cell>", "exec"), namespace)
        cells.append({"cell_type":"code","execution_count":i,"metadata":{},"source":code.splitlines(True),"outputs":[{"output_type":"stream","name":"stdout","text":output.getvalue().splitlines(True)}]})
    root=Path(__file__).parent
    (root/"notebooks").mkdir(exist_ok=True)
    notebook={"cells":cells,"metadata":{"kernelspec":{"display_name":"Python 3","language":"python","name":"python3"},"language_info":{"name":"python","version":"3.12"}},"nbformat":4,"nbformat_minor":5}
    (root/"notebooks/01_retrieval.ipynb").write_text(json.dumps(notebook,ensure_ascii=False,indent=2),encoding="utf-8")
    (root/"reports").mkdir(exist_ok=True)
    report=namespace["report"]
    (root/"reports/retrieval.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps({"recall_at_1":report["recall_at_1"],"recall_at_3":report["recall_at_3"],"errors":len(report["errors"])}))

if __name__ == "__main__":
    run()
