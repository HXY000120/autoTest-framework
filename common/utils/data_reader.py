"""统一数据读取：按扩展名分派 yaml / json，替代分散的读取函数。"""


import json
import os

import yaml

from common.config.settings import BASE_DIR


def load_data(rel_path: str, data_dir: str = None):
    if data_dir is None:
        data_dir = os.path.join(BASE_DIR, "data")
    path = os.path.join(data_dir, rel_path)
    with open(path, "r", encoding="utf-8") as f:
        if path.endswith((".yaml", ".yml")):
            return yaml.safe_load(f)
        if path.endswith(".json"):
            return json.load(f)
    raise ValueError(f"不支持的数据文件: {path}")
