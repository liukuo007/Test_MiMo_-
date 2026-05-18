from __future__ import annotations

import os
import json
from dataclasses import dataclass


@dataclass
class DatasetItem:
    image_path: str
    ground_truth: str
    metadata: dict


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class DatasetManager:
    def __init__(self, dataset_root: str):
        self.dataset_root = dataset_root

    def load(self, dataset_name: str) -> list[DatasetItem]:
        dataset_path = os.path.join(self.dataset_root, dataset_name)
        items = []

        if not os.path.exists(dataset_path):
            return items

        annotations = {}
        annotation_file = os.path.join(dataset_path, "annotations.json")
        if os.path.exists(annotation_file):
            with open(annotation_file, "r", encoding="utf-8") as f:
                annotations = json.load(f)

        if isinstance(annotations, dict) and "images" in annotations:
            for img_info in annotations["images"]:
                file_name = img_info.get("file_name", "")
                label = img_info.get("label", img_info.get("category", "unknown"))
                img_path = os.path.join(dataset_path, file_name)
                items.append(DatasetItem(
                    image_path=img_path,
                    ground_truth=label,
                    metadata=img_info,
                ))
        else:
            for root, _dirs, files in os.walk(dataset_path):
                for fname in sorted(files):
                    ext = os.path.splitext(fname)[1].lower()
                    if ext in IMAGE_EXTENSIONS:
                        img_path = os.path.join(root, fname)
                        label = annotations.get(fname, os.path.splitext(fname)[0])
                        if isinstance(label, dict):
                            label = label.get("label", label.get("category", "unknown"))
                        items.append(DatasetItem(
                            image_path=img_path,
                            ground_truth=str(label),
                            metadata={"file": fname},
                        ))

        return items

    def list_datasets(self) -> list[str]:
        if not os.path.exists(self.dataset_root):
            return []
        return [d for d in os.listdir(self.dataset_root) if os.path.isdir(os.path.join(self.dataset_root, d))]
