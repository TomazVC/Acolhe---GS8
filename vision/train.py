"""Explicit real-dataset training. Does not download data or publish children's images."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

def validate_names(names):
    from vision.service import LABELS
    expected = list(LABELS)
    if isinstance(names, dict):
        if any(type(k) is not int for k in names) or set(names) != set(range(len(expected))):
            raise ValueError("Class IDs must be integers 0..11")
        names = [names[i] for i in range(len(expected))]
    if not isinstance(names, list) or names != expected:
        raise ValueError("Class names must exactly match the 12 service classes in order")
    return names


def validate_dataset(dataset, provenance):
    import yaml
    # Reject duplicate mapping keys instead of silently retaining the last value.
    class UniqueLoader(yaml.SafeLoader):
        pass
    def unique_mapping(loader, node, deep=False):
        result = {}
        for key_node, value_node in node.value:
            key = loader.construct_object(key_node, deep=deep)
            if key in result:
                raise ValueError("Duplicate YAML mapping key")
            result[key] = loader.construct_object(value_node, deep=deep)
        return result
    UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)
    data = Path(dataset).resolve()
    config = yaml.load(data.read_text(encoding="utf-8-sig"), Loader=UniqueLoader)
    if not isinstance(config, dict):
        raise ValueError("Dataset YAML must be a mapping")
    validate_names(config.get("names"))
    if "nc" in config and (type(config["nc"]) is not int or config["nc"] != 12):
        raise ValueError("nc must be 12")
    if any(not config.get(key) for key in ("train", "val", "test")):
        raise ValueError("Train, validation and test splits must be declared")
    metadata = json.loads(Path(provenance).read_text(encoding="utf-8-sig"))
    if not isinstance(metadata, dict) or metadata.get("real_images") is not True:
        raise ValueError("Document verified real-image provenance")
    for key in ("source_url", "license", "split_method"):
        if not isinstance(metadata.get(key), str) or not metadata[key].strip():
            raise ValueError("Missing provenance: " + key)
    validate_names(metadata.get("class_names"))
    return data, metadata


def reserve_output(path):
    path = Path(path)
    path.mkdir(parents=True, exist_ok=False)
    return path


def train(dataset, provenance, epochs=40, output=None):
    if type(epochs) is not int or epochs < 1:
        raise ValueError("epochs must be a positive integer")
    data, metadata = validate_dataset(dataset, provenance)
    from ultralytics import YOLO
    root = Path(__file__).parent
    out = reserve_output(output or root/"artifacts")
    model = YOLO("yolo11n.pt")
    model.train(data=str(data), epochs=epochs, imgsz=640, seed=42, deterministic=True, project=str(root/"runs"), name="acolhe", exist_ok=False)
    best = Path(model.trainer.best)
    evaluation = YOLO(str(best)).val(data=str(data), split="test")
    with best.open("rb") as source, (out/"best.pt").open("xb") as target:
        shutil.copyfileobj(source, target)
    metadata.update(trained_on_real_images=True, epochs=epochs, model="yolo11n",
                    dataset_yaml_sha256=hashlib.sha256(data.read_bytes()).hexdigest(),
                    checkpoint_sha256=hashlib.sha256((out/"best.pt").read_bytes()).hexdigest(),
                    test_metrics={str(k): float(v) for k,v in evaluation.results_dict.items()})
    with (out/"model_manifest.json").open("x", encoding="utf-8") as target:
        json.dump(metadata, target, indent=2)
    return metadata

if __name__ == "__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--dataset",required=True)
    p.add_argument("--provenance",required=True)
    p.add_argument("--epochs", type=int, default=40)
    p.add_argument("--output", help="New artifact directory; existing directories are never reused")
    a=p.parse_args()
    print(json.dumps(train(a.dataset,a.provenance,a.epochs,a.output),indent=2))
