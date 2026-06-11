from __future__ import annotations

import csv
import json
import re
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import numpy as np

from . import spec
from .data_io import iter_pairs, load_task, task_paths
from .onnx_build import (
    build_component_count_diagonal_network,
    build_dynamic_first_hsplit_network,
    build_hconcat_self_network,
    build_least_color_bbox_crop_network,
    build_most_color_canvas_network,
    build_most_connected_nonzero_bbox_crop_network,
    build_most_frequent_nonzero_bbox_crop_network,
    build_nonzero_bbox_scaled_crop_network,
    build_remove_isolated_foreground_network,
    build_spatial_repeat_network,
    build_uniform_frontier_fill_network,
    build_valid_axis_reverse_network,
)
from .paths import root
from .validation import validate_onnx_file


BANK_FIELDS = [
    "task_id",
    "rule_family",
    "rule_name",
    "train_examples",
    "train_pass_count",
    "train_pass_rate",
    "estimated_hidden_risk",
    "source_basis",
    "candidate_generator",
    "candidate_onnx_path",
    "local_validation_status",
    "eligible_for_batch",
    "notes",
]

ATTEMPT_FIELDS = [
    "task_id",
    "train_examples",
    "detected_rule_count",
    "eligible_rule_count",
    "best_rule_name",
    "status",
    "notes",
]

RULE_PRIORITY = [
    "identity",
    "rotate180",
    "horizontal_mirror",
    "vertical_mirror",
    "crop_nonzero_bbox",
    "upscale_x2",
    "upscale_x3",
    "largest_color_crop",
    "largest_object_crop",
    "least_color_crop",
    "most_color_canvas",
    "remove_isolated_pixels",
    "color_replacement",
    "fill_bounding_box",
    "frontier_fill",
    "hconcat_self",
    "vconcat_self",
    "first_hsplit",
    "first_vsplit",
    "rotate90",
    "rotate270",
    "connected_component_count",
    "simple_mask_extraction",
]

CONSERVATIVE_RULES = {
    "identity",
    "rotate180",
    "horizontal_mirror",
    "vertical_mirror",
    "crop_nonzero_bbox",
    "upscale_x2",
    "upscale_x3",
}


@dataclass(frozen=True)
class RuleCandidate:
    task_id: str
    rule_family: str
    rule_name: str
    train_examples: int
    train_pass_count: int
    params: dict
    notes: str = ""

    @property
    def priority(self) -> int:
        try:
            return RULE_PRIORITY.index(self.rule_name)
        except ValueError:
            return 999


def norm_task_id(value: str) -> str:
    stem = value[:-5] if value.endswith(".onnx") else value
    if stem.startswith("task"):
        return stem
    return f"task{int(stem):03d}"


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(root())).replace("\\", "/")
    except ValueError:
        return str(path)


def read_csv(path: Path) -> list[dict]:
    if not path.exists() or not path.stat().st_size:
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, fields: list[str], rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def parse_params(notes: str) -> dict:
    match = re.search(r"params=(\{.*?\})(?:;|$)", notes)
    if not match:
        return {}
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return {}


def grid_shape(grid: list[list[int]]) -> tuple[int, int]:
    return len(grid), len(grid[0]) if grid else 0


def same_grid(a: list[list[int]], b: list[list[int]]) -> bool:
    return a == b


def bbox(points: list[tuple[int, int]]) -> tuple[int, int, int, int] | None:
    if not points:
        return None
    rows = [r for r, _ in points]
    cols = [c for _, c in points]
    return min(rows), min(cols), max(rows), max(cols)


def crop(grid: list[list[int]], box: tuple[int, int, int, int]) -> list[list[int]]:
    r0, c0, r1, c1 = box
    return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]


def nonzero_bbox_crop(grid: list[list[int]]) -> list[list[int]]:
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    box = bbox(points)
    return crop(grid, box) if box else [[0]]


def most_color_canvas(grid: list[list[int]], height: int, width: int) -> list[list[int]]:
    color = Counter(value for row in grid for value in row).most_common(1)[0][0]
    return [[color for _ in range(width)] for _ in range(height)]


def color_bbox_crop(grid: list[list[int]], color: int) -> list[list[int]]:
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == color
    ]
    box = bbox(points)
    return crop(grid, box) if box else [[0]]


def most_frequent_nonzero_bbox_crop(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row if value != 0)
    if not counts:
        return [[0]]
    color = min((-count, color) for color, count in counts.items())[1]
    return color_bbox_crop(grid, color)


def least_color_bbox_crop(grid: list[list[int]]) -> list[list[int]]:
    counts = Counter(value for row in grid for value in row)
    color = min((count, color) for color, count in counts.items())[1]
    return color_bbox_crop(grid, color)


def connected_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    height, width = grid_shape(grid)
    seen: set[tuple[int, int]] = set()
    components: list[list[tuple[int, int]]] = []
    for r in range(height):
        for c in range(width):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            q: deque[tuple[int, int]] = deque([(r, c)])
            seen.add((r, c))
            comp: list[tuple[int, int]] = []
            while q:
                cr, cc = q.popleft()
                comp.append((cr, cc))
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = cr + dr, cc + dc
                    if not (0 <= nr < height and 0 <= nc < width):
                        continue
                    if (nr, nc) in seen or grid[nr][nc] != color:
                        continue
                    seen.add((nr, nc))
                    q.append((nr, nc))
            components.append(comp)
    return components


def largest_object_crop(grid: list[list[int]]) -> list[list[int]]:
    components = connected_components(grid)
    if not components:
        return [[0]]
    comp = max(components, key=lambda item: (len(item), -min(r for r, _ in item), -min(c for _, c in item)))
    return crop(grid, bbox(comp) or (0, 0, 0, 0))


def remove_isolated(grid: list[list[int]]) -> list[list[int]]:
    out = [row[:] for row in grid]
    height, width = grid_shape(grid)
    for r in range(height):
        for c in range(width):
            if grid[r][c] == 0:
                continue
            has_neighbor = False
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < height and 0 <= nc < width and grid[nr][nc] != 0:
                        has_neighbor = True
            if not has_neighbor:
                out[r][c] = 0
    return out


def fill_bbox(grid: list[list[int]], source_color: int, fill_color: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    points = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == source_color
    ]
    box = bbox(points)
    if not box:
        return out
    r0, c0, r1, c1 = box
    for r in range(r0, r1 + 1):
        for c in range(c0, c1 + 1):
            if grid[r][c] != source_color:
                out[r][c] = fill_color
    return out


def frontier_fill(grid: list[list[int]], fill_color: int) -> list[list[int]]:
    out = [row[:] for row in grid]
    height, width = grid_shape(grid)
    row_frontier = [
        len(set(grid[r][c] for c in range(width))) == 1 for r in range(height)
    ]
    col_frontier = [
        len(set(grid[r][c] for r in range(height))) == 1 for c in range(width)
    ]
    for r in range(height):
        for c in range(width):
            if row_frontier[r] or col_frontier[c]:
                out[r][c] = fill_color
    return out


def component_count_diagonal(grid: list[list[int]], color: int = 8) -> list[list[int]]:
    masked = [[value if value == color else 0 for value in row] for row in grid]
    count = len(connected_components(masked))
    if count <= 0:
        return [[0]]
    return [[color if r == c else 0 for c in range(count)] for r in range(count)]


def color_replace(grid: list[list[int]], source_color: int, target_color: int) -> list[list[int]]:
    return [
        [target_color if value == source_color else value for value in row]
        for row in grid
    ]


def mask_extract(
    grid: list[list[int]],
    source_color: int,
    target_color: int,
    background_color: int = 0,
) -> list[list[int]]:
    return [
        [target_color if value == source_color else background_color for value in row]
        for row in grid
    ]


def hmirror(grid: list[list[int]]) -> list[list[int]]:
    return [list(reversed(row)) for row in grid]


def vmirror(grid: list[list[int]]) -> list[list[int]]:
    return list(reversed(grid))


def rotate(grid: list[list[int]], k: int) -> list[list[int]]:
    arr = np.array(grid, dtype=np.int64)
    return np.rot90(arr, k=k).tolist()


def upscale(grid: list[list[int]], scale: int) -> list[list[int]]:
    return [
        [value for value in row for _ in range(scale)]
        for row in grid
        for _ in range(scale)
    ]


def hconcat_self(grid: list[list[int]]) -> list[list[int]]:
    return [row + row for row in grid]


def vconcat_self(grid: list[list[int]]) -> list[list[int]]:
    return grid + [row[:] for row in grid]


def first_hsplit(grid: list[list[int]], parts: int) -> list[list[int]]:
    width = len(grid[0])
    return [row[: width // parts] for row in grid]


def first_vsplit(grid: list[list[int]], parts: int) -> list[list[int]]:
    height = len(grid)
    return [row[:] for row in grid[: height // parts]]


def split_examples(task: dict, splits: Iterable[str]) -> list[dict]:
    return [pair for split, pair in iter_pairs(task, splits=splits) if "output" in pair]


def all_output_shapes(task: dict) -> list[tuple[int, int]]:
    return [grid_shape(pair["output"]) for split, pair in iter_pairs(task) if "output" in pair]


def max_output_shape(task: dict) -> tuple[int, int]:
    shapes = all_output_shapes(task)
    if not shapes:
        return 1, 1
    return max(h for h, _ in shapes), max(w for _, w in shapes)


def fixed_input_shape(task: dict) -> tuple[int, int] | None:
    shapes = {grid_shape(pair["input"]) for split, pair in iter_pairs(task) if "output" in pair}
    return next(iter(shapes)) if len(shapes) == 1 else None


def exact_for_train(
    task_id: str,
    task: dict,
    *,
    rule_family: str,
    rule_name: str,
    params: dict,
    transform: Callable[[list[list[int]]], list[list[int]]],
    notes: str = "",
    require_changed: bool = True,
) -> RuleCandidate | None:
    train = split_examples(task, ["train"])
    if not train:
        return None
    pass_count = 0
    changed_count = 0
    for pair in train:
        output = transform(pair["input"])
        if same_grid(output, pair["output"]):
            pass_count += 1
            if not same_grid(output, pair["input"]):
                changed_count += 1
    if pass_count != len(train):
        return None
    if require_changed and changed_count == 0:
        return None
    return RuleCandidate(
        task_id=task_id,
        rule_family=rule_family,
        rule_name=rule_name,
        train_examples=len(train),
        train_pass_count=pass_count,
        params=params,
        notes=notes,
    )


def detect_task_candidates(task_id: str, task: dict) -> list[RuleCandidate]:
    candidates: list[RuleCandidate] = []
    hmax, wmax = max_output_shape(task)

    simple_rules: list[tuple[str, str, dict, Callable[[list[list[int]]], list[list[int]]], str]] = [
        ("identity", "identity", {}, lambda g: [row[:] for row in g], "copy input"),
        (
            "crop",
            "crop_nonzero_bbox",
            {"max_output_height": hmax, "max_output_width": wmax, "scale": 1},
            nonzero_bbox_crop,
            "crop bounding box of nonzero cells",
        ),
        (
            "object_crop",
            "largest_color_crop",
            {"padding_index": 29},
            most_frequent_nonzero_bbox_crop,
            "crop bounding box of most frequent nonzero color",
        ),
        (
            "object_crop",
            "largest_object_crop",
            {"padding_index": 29},
            largest_object_crop,
            "crop bounding box of largest 4-connected same-color object",
        ),
        (
            "object_crop",
            "least_color_crop",
            {"max_output_size": max(hmax, wmax)},
            least_color_bbox_crop,
            "crop bounding box of least frequent present color",
        ),
        ("mirror", "horizontal_mirror", {}, hmirror, "reverse valid columns"),
        ("mirror", "vertical_mirror", {}, vmirror, "reverse valid rows"),
        ("upscale", "upscale_x2", {"scale": 2}, lambda g: upscale(g, 2), "repeat pixels x2"),
        ("upscale", "upscale_x3", {"scale": 3}, lambda g: upscale(g, 3), "repeat pixels x3"),
        ("cleanup", "remove_isolated_pixels", {}, remove_isolated, "remove 8-neighbor isolated foreground"),
        ("count", "connected_component_count", {"object_color": 8}, component_count_diagonal, "render component-count diagonal"),
        ("concat", "hconcat_self", {}, hconcat_self, "horizontal concat input with itself"),
        ("concat", "vconcat_self", {}, vconcat_self, "vertical concat input with itself"),
    ]

    for family, name, params, transform, note in simple_rules:
        item = exact_for_train(
            task_id,
            task,
            rule_family=family,
            rule_name=name,
            params=params,
            transform=transform,
            notes=note,
            require_changed=(name != "identity"),
        )
        if item:
            candidates.append(item)

    fixed_shape = fixed_input_shape(task)
    if fixed_shape:
        height, width = fixed_shape
        rotation_rules = [
            ("rotate90", {"height": height, "width": width, "rotation": "rotate90"}, lambda g: rotate(g, -1)),
            ("rotate180", {"height": height, "width": width, "rotation": "rotate180"}, lambda g: rotate(g, 2)),
            ("rotate270", {"height": height, "width": width, "rotation": "rotate270"}, lambda g: rotate(g, 1)),
        ]
        for name, params, transform in rotation_rules:
            item = exact_for_train(
                task_id,
                task,
                rule_family="rotation",
                rule_name=name,
                params=params,
                transform=transform,
                notes=f"fixed input rectangle {height}x{width}",
            )
            if item:
                candidates.append(item)

    output_shapes = set(all_output_shapes(task))
    if len(output_shapes) == 1:
        height, width = next(iter(output_shapes))
        item = exact_for_train(
            task_id,
            task,
            rule_family="color_canvas",
            rule_name="most_color_canvas",
            params={"height": height, "width": width},
            transform=lambda g, h=height, w=width: most_color_canvas(g, h, w),
            notes=f"fixed output canvas {height}x{width}",
        )
        if item:
            candidates.append(item)

    for source_color in range(10):
        for target_color in range(10):
            if source_color == target_color:
                continue
            item = exact_for_train(
                task_id,
                task,
                rule_family="color_map",
                rule_name="color_replacement",
                params={"source_color": source_color, "target_color": target_color},
                transform=lambda g, s=source_color, t=target_color: color_replace(g, s, t),
                notes=f"replace color {source_color} with {target_color}",
            )
            if item:
                candidates.append(item)

    for source_color in range(10):
        for target_color in range(10):
            item = exact_for_train(
                task_id,
                task,
                rule_family="mask",
                rule_name="simple_mask_extraction",
                params={
                    "source_color": source_color,
                    "target_color": target_color,
                    "background_color": 0,
                },
                transform=lambda g, s=source_color, t=target_color: mask_extract(g, s, t, 0),
                notes=f"extract color {source_color} as {target_color} on zero background",
            )
            if item:
                candidates.append(item)

    for source_color in range(10):
        for fill_color in range(10):
            item = exact_for_train(
                task_id,
                task,
                rule_family="fill",
                rule_name="fill_bounding_box",
                params={"source_color": source_color, "fill_color": fill_color},
                transform=lambda g, s=source_color, f=fill_color: fill_bbox(g, s, f),
                notes=f"fill non-source cells in color {source_color} bbox with {fill_color}",
            )
            if item:
                candidates.append(item)

    for fill_color in range(10):
        item = exact_for_train(
            task_id,
            task,
            rule_family="fill",
            rule_name="frontier_fill",
            params={"fill_color": fill_color},
            transform=lambda g, f=fill_color: frontier_fill(g, f),
            notes=f"fill uniform row/column frontier with {fill_color}",
        )
        if item:
            candidates.append(item)

    for parts in range(2, 7):
        item = exact_for_train(
            task_id,
            task,
            rule_family="split",
            rule_name="first_hsplit",
            params={"parts": parts},
            transform=lambda g, p=parts: first_hsplit(g, p) if len(g[0]) % p == 0 else [],
            notes=f"keep first of {parts} horizontal splits",
        )
        if item:
            candidates.append(item)
        item = exact_for_train(
            task_id,
            task,
            rule_family="split",
            rule_name="first_vsplit",
            params={"parts": parts},
            transform=lambda g, p=parts: first_vsplit(g, p) if len(g) % p == 0 else [],
            notes=f"keep first of {parts} vertical splits",
        )
        if item:
            candidates.append(item)

    dedup: dict[tuple[str, str], RuleCandidate] = {}
    for item in candidates:
        key = (item.rule_name, json.dumps(item.params, sort_keys=True))
        dedup[key] = item
    return sorted(dedup.values(), key=lambda item: (item.priority, item.rule_name))


def make_tensor_value_info():
    import onnx
    from onnx import TensorProto, helper

    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, list(spec.TENSOR_SHAPE))
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, list(spec.TENSOR_SHAPE))
    return onnx, helper, TensorProto, x, y


def build_identity_network(path: Path) -> None:
    onnx, helper, _, x, y = make_tensor_value_info()
    node = helper.make_node("Identity", [spec.INPUT_NAME], [spec.OUTPUT_NAME])
    graph = helper.make_graph([node], "simple_identity", [x], [y])
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    onnx.checker.check_model(model, full_check=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_color_replacement_network(path: Path, *, source_color: int, target_color: int) -> None:
    onnx, helper, TensorProto, x, y = make_tensor_value_info()
    from onnx import numpy_helper

    replacement = np.zeros((1, 10, 1, 1), dtype=np.float32)
    replacement[0, target_color, 0, 0] = 1.0
    initializers = [
        numpy_helper.from_array(np.array([source_color], dtype=np.int64), "source_color"),
        numpy_helper.from_array(np.array(0.5, dtype=np.float32), "half"),
        numpy_helper.from_array(replacement, "replacement_onehot"),
    ]
    nodes = [
        helper.make_node("Gather", [spec.INPUT_NAME, "source_color"], ["source_plane"], axis=1),
        helper.make_node("Greater", ["source_plane", "half"], ["source_mask"]),
        helper.make_node("Where", ["source_mask", "replacement_onehot", spec.INPUT_NAME], [spec.OUTPUT_NAME]),
    ]
    graph = helper.make_graph(nodes, "simple_color_replacement", [x], [y], initializer=initializers)
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    onnx.checker.check_model(model, full_check=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_mask_extraction_network(
    path: Path,
    *,
    source_color: int,
    target_color: int,
    background_color: int = 0,
) -> None:
    onnx, helper, TensorProto, x, y = make_tensor_value_info()
    from onnx import numpy_helper

    target = np.zeros((1, 10, 1, 1), dtype=np.float32)
    target[0, target_color, 0, 0] = 1.0
    background = np.zeros((1, 10, 1, 1), dtype=np.float32)
    background[0, background_color, 0, 0] = 1.0
    zero = np.zeros(spec.TENSOR_SHAPE, dtype=np.float32)
    initializers = [
        numpy_helper.from_array(np.array([source_color], dtype=np.int64), "source_color"),
        numpy_helper.from_array(np.array(0.5, dtype=np.float32), "half"),
        numpy_helper.from_array(target, "target_onehot"),
        numpy_helper.from_array(background, "background_onehot"),
        numpy_helper.from_array(zero, "zero_tensor"),
    ]
    nodes = [
        helper.make_node("Gather", [spec.INPUT_NAME, "source_color"], ["source_plane"], axis=1),
        helper.make_node("Greater", ["source_plane", "half"], ["source_mask"]),
        helper.make_node("ReduceSum", [spec.INPUT_NAME], ["valid_plane"], axes=[1], keepdims=1),
        helper.make_node("Greater", ["valid_plane", "half"], ["valid_mask"]),
        helper.make_node("Where", ["valid_mask", "background_onehot", "zero_tensor"], ["background_canvas"]),
        helper.make_node("Where", ["source_mask", "target_onehot", "background_canvas"], [spec.OUTPUT_NAME]),
    ]
    graph = helper.make_graph(nodes, "simple_mask_extraction", [x], [y], initializer=initializers)
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    onnx.checker.check_model(model, full_check=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_fixed_rotation_network(path: Path, *, height: int, width: int, rotation: str) -> None:
    onnx, helper, _, x, y = make_tensor_value_info()
    from onnx import numpy_helper

    if rotation not in {"rotate90", "rotate180", "rotate270"}:
        raise ValueError("rotation must be rotate90, rotate180, or rotate270")
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("height and width must fit 30x30")
    rows = np.arange(height, dtype=np.int64)
    cols = np.arange(width, dtype=np.int64)
    initializers = [
        numpy_helper.from_array(rows, "rows"),
        numpy_helper.from_array(cols, "cols"),
    ]
    nodes = [
        helper.make_node("Gather", [spec.INPUT_NAME, "rows"], ["row_crop"], axis=2),
        helper.make_node("Gather", ["row_crop", "cols"], ["small"], axis=3),
    ]
    if rotation == "rotate180":
        rev_rows = np.arange(height - 1, -1, -1, dtype=np.int64)
        rev_cols = np.arange(width - 1, -1, -1, dtype=np.int64)
        initializers.extend(
            [
                numpy_helper.from_array(rev_rows, "rev_rows"),
                numpy_helper.from_array(rev_cols, "rev_cols"),
            ]
        )
        nodes.extend(
            [
                helper.make_node("Gather", ["small", "rev_rows"], ["rev_row"], axis=2),
                helper.make_node("Gather", ["rev_row", "rev_cols"], ["rotated"], axis=3),
            ]
        )
        out_h, out_w = height, width
    elif rotation == "rotate90":
        rev_cols_after_t = np.arange(height - 1, -1, -1, dtype=np.int64)
        initializers.append(numpy_helper.from_array(rev_cols_after_t, "rev_cols_after_t"))
        nodes.extend(
            [
                helper.make_node("Transpose", ["small"], ["transposed"], perm=[0, 1, 3, 2]),
                helper.make_node("Gather", ["transposed", "rev_cols_after_t"], ["rotated"], axis=3),
            ]
        )
        out_h, out_w = width, height
    else:
        rev_rows_after_t = np.arange(width - 1, -1, -1, dtype=np.int64)
        initializers.append(numpy_helper.from_array(rev_rows_after_t, "rev_rows_after_t"))
        nodes.extend(
            [
                helper.make_node("Transpose", ["small"], ["transposed"], perm=[0, 1, 3, 2]),
                helper.make_node("Gather", ["transposed", "rev_rows_after_t"], ["rotated"], axis=2),
            ]
        )
        out_h, out_w = width, height
    nodes.append(
        helper.make_node(
            "Pad",
            ["rotated"],
            [spec.OUTPUT_NAME],
            pads=[0, 0, 0, 0, 0, 0, 30 - out_h, 30 - out_w],
            value=0.0,
        )
    )
    graph = helper.make_graph(nodes, "simple_fixed_rotation", [x], [y], initializer=initializers)
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    onnx.checker.check_model(model, full_check=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_vconcat_self_network(path: Path) -> None:
    onnx, helper, TensorProto, x, y = make_tensor_value_info()
    from onnx import numpy_helper

    initializers = [numpy_helper.from_array(np.arange(30, dtype=np.int64), "row_indices")]
    nodes = [
        helper.make_node("ReduceMax", [spec.INPUT_NAME], ["valid_rows"], axes=[0, 1, 3], keepdims=0),
        helper.make_node("ReduceSum", ["valid_rows"], ["valid_height_float"], axes=[0], keepdims=0),
        helper.make_node("Cast", ["valid_height_float"], ["valid_height"], to=TensorProto.INT64),
        helper.make_node("Add", ["valid_height", "valid_height"], ["double_height"]),
        helper.make_node("Mod", ["row_indices", "valid_height"], ["wrapped_rows"]),
        helper.make_node("Less", ["row_indices", "double_height"], ["inside_output_height"]),
        helper.make_node("Where", ["inside_output_height", "wrapped_rows", "valid_height"], ["gather_rows"]),
        helper.make_node("Gather", [spec.INPUT_NAME, "gather_rows"], [spec.OUTPUT_NAME], axis=2),
    ]
    graph = helper.make_graph(nodes, "simple_vconcat_self", [x], [y], initializer=initializers)
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    onnx.checker.check_model(model, full_check=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_dynamic_first_vsplit_network(path: Path, *, parts: int = 3) -> None:
    onnx, helper, _, x, y = make_tensor_value_info()
    from onnx import numpy_helper

    row_indices = np.arange(30, dtype=np.float32).reshape(1, 1, 30, 1)
    zero_hot = np.zeros((1, 10, 1, 1), dtype=np.float32)
    initializers = [
        numpy_helper.from_array(row_indices, "row_indices_float"),
        numpy_helper.from_array(np.array(float(parts), dtype=np.float32), "parts_float"),
        numpy_helper.from_array(zero_hot, "zero_hot"),
    ]
    nodes = [
        helper.make_node("ReduceMax", [spec.INPUT_NAME], ["valid_rows"], axes=[0, 1, 3], keepdims=0),
        helper.make_node("ReduceSum", ["valid_rows"], ["valid_height_float"], axes=[0], keepdims=0),
        helper.make_node("Div", ["valid_height_float", "parts_float"], ["split_height_float"]),
        helper.make_node("Less", ["row_indices_float", "split_height_float"], ["inside_first_split"]),
        helper.make_node("Where", ["inside_first_split", spec.INPUT_NAME, "zero_hot"], [spec.OUTPUT_NAME]),
    ]
    graph = helper.make_graph(nodes, "dynamic_first_vsplit", [x], [y], initializer=initializers)
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    onnx.checker.check_model(model, full_check=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_simple_rule_onnx(rule_name: str, params: dict, out_path: Path) -> None:
    if rule_name == "identity":
        build_identity_network(out_path)
    elif rule_name == "crop_nonzero_bbox":
        build_nonzero_bbox_scaled_crop_network(
            out_path,
            max_output_height=int(params["max_output_height"]),
            max_output_width=int(params["max_output_width"]),
            scale=int(params.get("scale", 1)),
        )
    elif rule_name == "largest_color_crop":
        build_most_frequent_nonzero_bbox_crop_network(
            out_path,
            padding_index=int(params.get("padding_index", 29)),
        )
    elif rule_name == "largest_object_crop":
        build_most_connected_nonzero_bbox_crop_network(
            out_path,
            padding_index=int(params.get("padding_index", 29)),
        )
    elif rule_name == "least_color_crop":
        build_least_color_bbox_crop_network(out_path, max_output_size=int(params["max_output_size"]))
    elif rule_name == "most_color_canvas":
        build_most_color_canvas_network(out_path, height=int(params["height"]), width=int(params["width"]))
    elif rule_name == "horizontal_mirror":
        build_valid_axis_reverse_network(out_path, axis=3)
    elif rule_name == "vertical_mirror":
        build_valid_axis_reverse_network(out_path, axis=2)
    elif rule_name in {"rotate90", "rotate180", "rotate270"}:
        build_fixed_rotation_network(
            out_path,
            height=int(params["height"]),
            width=int(params["width"]),
            rotation=rule_name,
        )
    elif rule_name == "upscale_x2":
        build_spatial_repeat_network(out_path, scale=2)
    elif rule_name == "upscale_x3":
        build_spatial_repeat_network(out_path, scale=3)
    elif rule_name == "remove_isolated_pixels":
        build_remove_isolated_foreground_network(out_path)
    elif rule_name == "connected_component_count":
        build_component_count_diagonal_network(out_path, object_color=int(params.get("object_color", 8)))
    elif rule_name == "color_replacement":
        build_color_replacement_network(
            out_path,
            source_color=int(params["source_color"]),
            target_color=int(params["target_color"]),
        )
    elif rule_name == "fill_bounding_box":
        from .onnx_build import build_bbox_delta_fill_network

        build_bbox_delta_fill_network(
            out_path,
            source_color=int(params["source_color"]),
            fill_color=int(params["fill_color"]),
        )
    elif rule_name == "frontier_fill":
        build_uniform_frontier_fill_network(out_path, fill_color=int(params["fill_color"]))
    elif rule_name == "hconcat_self":
        build_hconcat_self_network(out_path)
    elif rule_name == "vconcat_self":
        build_vconcat_self_network(out_path)
    elif rule_name == "first_hsplit":
        build_dynamic_first_hsplit_network(out_path, parts=int(params.get("parts", 3)))
    elif rule_name == "first_vsplit":
        build_dynamic_first_vsplit_network(out_path, parts=int(params.get("parts", 3)))
    elif rule_name == "simple_mask_extraction":
        build_mask_extraction_network(
            out_path,
            source_color=int(params["source_color"]),
            target_color=int(params["target_color"]),
            background_color=int(params.get("background_color", 0)),
        )
    else:
        raise ValueError(f"no ONNX generator for rule: {rule_name}")


def task_candidate_path(task_id: str, rule_name: str) -> Path:
    return root("task_bank/tasks", task_id, "simple_exact", rule_name, f"{task_id}.onnx")


def validation_status(task_id: str, path: Path) -> tuple[bool, str]:
    result = validate_onnx_file(
        path,
        root("data/raw/neurogolf-2026"),
        smoke_examples_per_split=10_000,
    )
    if result.ok and result.examples_failed == 0:
        return True, f"pass: examples_checked={result.examples_checked}; examples_failed=0"
    details = "; ".join(result.structural_errors[:5])
    return False, f"fail: examples_checked={result.examples_checked}; examples_failed={result.examples_failed}; {details}"


def row_from_candidate(candidate: RuleCandidate, onnx_path: Path, status: str) -> dict:
    risk = "low" if candidate.rule_name in CONSERVATIVE_RULES else "medium"
    return {
        "task_id": candidate.task_id,
        "rule_family": candidate.rule_family,
        "rule_name": candidate.rule_name,
        "train_examples": str(candidate.train_examples),
        "train_pass_count": str(candidate.train_pass_count),
        "train_pass_rate": "1.0",
        "estimated_hidden_risk": risk,
        "source_basis": "official task train exact match plus local train/test/arc-gen validation",
        "candidate_generator": "scripts/37_generate_simple_task_onnx.py",
        "candidate_onnx_path": rel(onnx_path),
        "local_validation_status": status,
        "eligible_for_batch": "true",
        "notes": f"params={json.dumps(candidate.params, sort_keys=True)}; {candidate.notes}",
    }


def load_bank(path: Path | None = None) -> list[dict]:
    return read_csv(path or root("task_bank/simple_exact_task_bank.csv"))


def candidate_for_bank_row(row: dict) -> RuleCandidate:
    task_id = norm_task_id(row["task_id"])
    task = load_task(task_id, root("data/raw/neurogolf-2026"))
    params = parse_params(row.get("notes", ""))
    for item in detect_task_candidates(task_id, task):
        if item.rule_name == row.get("rule_name") and (not params or item.params == params):
            return item
    raise ValueError(f"could not reconstruct candidate for {task_id} {row.get('rule_name')}")


def task_count(data_dir: Path | None = None) -> int:
    return len(task_paths(data_dir or root("data/raw/neurogolf-2026")))
