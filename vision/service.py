"""No default pretrained predictions: a locally trained, documented checkpoint is required."""
import hashlib
import io
import json
from pathlib import Path

ROOT = Path(__file__).parent
MODEL = ROOT / "artifacts/best.pt"
MANIFEST = ROOT / "artifacts/model_manifest.json"
LABELS = {en: {"pt": pt, "es": es} for en, pt, es in [
 ("backpack","mochila","mochila"),("chair","cadeira","silla"),("book","livro","libro"),
 ("bottle","garrafa","botella"),("cup","copo","vaso"),("spoon","colher","cuchara"),
 ("fork","garfo","tenedor"),("bowl","tigela","cuenco"),("clock","relógio","reloj"),
 ("umbrella","guarda-chuva","paraguas"),("bus","ônibus","autobús"),("traffic light","semáforo","semáforo")]}

class ModelUnavailable(RuntimeError):
    pass

def _load_verified_model():
    if not MODEL.is_file() or not MANIFEST.is_file():
        raise ModelUnavailable("Checkpoint e manifesto de treino real ausentes.")
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict) or manifest.get("trained_on_real_images") is not True:
            raise ValueError("Treino real nao documentado")
        if manifest.get("class_names") != list(LABELS):
            raise ValueError("Classes ou ordem do manifesto invalidas")
        with MODEL.open("rb") as source:
            digest = hashlib.file_digest(source, "sha256").hexdigest()
        if manifest.get("checkpoint_sha256") != digest:
            raise ValueError("Hash do checkpoint nao confere")
        from PIL import Image
        from ultralytics import YOLO
        model = YOLO(str(MODEL))
        names = model.names
        expected = dict(enumerate(LABELS))
        if isinstance(names, list):
            names = dict(enumerate(names))
        if names != expected:
            raise ValueError("Classes do checkpoint nao correspondem ao servico")
        return model
    except Exception as exc:
        raise ModelUnavailable("Modelo indisponivel: " + type(exc).__name__) from exc


def status():
    try:
        _load_verified_model()
        reason = None
    except ModelUnavailable as exc:
        reason = str(exc)
    ready = reason is None
    return {"ready": ready, "mode": "custom_model" if ready else "unavailable",
            "reason": reason, "classes": LABELS,
            "verification": "checkpoint_hash_classes_and_load" if ready else "not_ready",
            "quality_validated": False}


def predict(image):
    model = _load_verified_model()
    if not isinstance(image, bytes) or not image or len(image) > 8 * 1024 * 1024:
        raise ValueError("image must be nonempty bytes, maximum 8 MiB")
    from PIL import Image
    source = Image.open(io.BytesIO(image))
    if source.width * source.height > 20_000_000:
        raise ValueError("Image too large")
    source = source.convert("RGB")
    results = model.predict(source, conf=0.5, verbose=False)
    detections = []
    for result in results:
        for box in result.boxes:
            label = result.names[int(box.cls.item())]
            if label in LABELS:
                detections.append({"class": label, **LABELS[label], "confidence": round(float(box.conf.item()), 4), "xyxy": box.xyxy[0].tolist()})
    return {"detections": detections, "mode": "custom_model", "warning": "Vocabulário educativo. Não decide se uma travessia é segura.", "stores_image": False}
