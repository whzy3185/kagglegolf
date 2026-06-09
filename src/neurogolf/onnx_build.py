from __future__ import annotations

from pathlib import Path

import numpy as np

from . import spec


def build_zero_network(path: Path) -> None:
    import onnx
    from onnx import TensorProto, helper

    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, list(spec.TENSOR_SHAPE))
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, list(spec.TENSOR_SHAPE))
    values = np.zeros(spec.TENSOR_SHAPE, dtype=np.float32).ravel()
    const = helper.make_tensor("zero", TensorProto.FLOAT, list(spec.TENSOR_SHAPE), values)
    node = helper.make_node("Constant", [], [spec.OUTPUT_NAME], value=const)
    graph = helper.make_graph([node], "zero_graph", [x], [y])
    model = helper.make_model(graph, ir_version=spec.IR_VERSION, opset_imports=[helper.make_opsetid("", spec.OPSET)])
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_bbox_delta_fill_network(
    path: Path,
    *,
    source_color: int,
    fill_color: int,
) -> None:
    """Fill the holes of a color's bounding box with another color.

    The input and output use NeuroGolf's fixed one-hot 1x10x30x30 format.
    The graph computes the source-color bounding box from row/column extrema,
    then overwrites only non-source cells inside that box.
    """

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)

    row_coords = np.arange(30, dtype=np.int64).reshape(1, 1, 30, 1)
    col_coords = np.arange(30, dtype=np.int64).reshape(1, 1, 1, 30)
    fill_onehot = np.zeros((1, 10, 1, 1), dtype=np.float32)
    fill_onehot[0, fill_color, 0, 0] = 1.0
    initializers = [
        numpy_helper.from_array(np.array([source_color], dtype=np.int64), "source_index"),
        numpy_helper.from_array(np.array(0.5, dtype=np.float32), "half"),
        numpy_helper.from_array(row_coords, "row_coords"),
        numpy_helper.from_array(col_coords, "col_coords"),
        numpy_helper.from_array(np.array(30, dtype=np.int64), "sentinel_hi"),
        numpy_helper.from_array(np.array(-1, dtype=np.int64), "sentinel_lo"),
        numpy_helper.from_array(fill_onehot, "fill_onehot"),
    ]

    nodes = [
        helper.make_node("Gather", ["input", "source_index"], ["source_plane"], axis=1),
        helper.make_node("Greater", ["source_plane", "half"], ["source_mask"]),
        helper.make_node("ReduceMax", ["source_plane"], ["row_strength"], axes=[3], keepdims=1),
        helper.make_node("ReduceMax", ["source_plane"], ["col_strength"], axes=[2], keepdims=1),
        helper.make_node("Greater", ["row_strength", "half"], ["row_has"]),
        helper.make_node("Greater", ["col_strength", "half"], ["col_has"]),
        helper.make_node("Where", ["row_has", "row_coords", "sentinel_hi"], ["row_min_candidates"]),
        helper.make_node("Where", ["row_has", "row_coords", "sentinel_lo"], ["row_max_candidates"]),
        helper.make_node("Where", ["col_has", "col_coords", "sentinel_hi"], ["col_min_candidates"]),
        helper.make_node("Where", ["col_has", "col_coords", "sentinel_lo"], ["col_max_candidates"]),
        helper.make_node("ReduceMin", ["row_min_candidates"], ["row_min"], axes=[2], keepdims=1),
        helper.make_node("ReduceMax", ["row_max_candidates"], ["row_max"], axes=[2], keepdims=1),
        helper.make_node("ReduceMin", ["col_min_candidates"], ["col_min"], axes=[3], keepdims=1),
        helper.make_node("ReduceMax", ["col_max_candidates"], ["col_max"], axes=[3], keepdims=1),
        helper.make_node("Less", ["row_coords", "row_min"], ["row_lt_min"]),
        helper.make_node("Greater", ["row_coords", "row_max"], ["row_gt_max"]),
        helper.make_node("Not", ["row_lt_min"], ["row_ge_min"]),
        helper.make_node("Not", ["row_gt_max"], ["row_le_max"]),
        helper.make_node("And", ["row_ge_min", "row_le_max"], ["row_inside"]),
        helper.make_node("Less", ["col_coords", "col_min"], ["col_lt_min"]),
        helper.make_node("Greater", ["col_coords", "col_max"], ["col_gt_max"]),
        helper.make_node("Not", ["col_lt_min"], ["col_ge_min"]),
        helper.make_node("Not", ["col_gt_max"], ["col_le_max"]),
        helper.make_node("And", ["col_ge_min", "col_le_max"], ["col_inside"]),
        helper.make_node("And", ["row_inside", "col_inside"], ["bbox_mask"]),
        helper.make_node("Not", ["source_mask"], ["not_source"]),
        helper.make_node("And", ["bbox_mask", "not_source"], ["delta_mask"]),
        helper.make_node("Where", ["delta_mask", "fill_onehot", "input"], [spec.OUTPUT_NAME]),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_bbox_delta_fill",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_uniform_frontier_fill_network(
    path: Path,
    *,
    fill_color: int,
) -> None:
    """Replace every uniform row and column in the valid grid with one color."""

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)

    fill_onehot = np.zeros((1, 10, 1, 1), dtype=np.float32)
    fill_onehot[0, fill_color, 0, 0] = 1.0
    initializers = [
        numpy_helper.from_array(np.array(0.5, dtype=np.float32), "half"),
        numpy_helper.from_array(np.array(0.0, dtype=np.float32), "zero"),
        numpy_helper.from_array(fill_onehot, "fill_onehot"),
    ]

    nodes = [
        helper.make_node("ReduceMax", ["input"], ["valid_strength"], axes=[1], keepdims=1),
        helper.make_node("Greater", ["valid_strength", "half"], ["valid_mask"]),
        helper.make_node("ReduceSum", ["input"], ["row_color_counts"], axes=[3], keepdims=1),
        helper.make_node("ReduceMax", ["row_color_counts"], ["row_max_count"], axes=[1], keepdims=1),
        helper.make_node("ReduceSum", ["valid_strength"], ["row_valid_count"], axes=[3], keepdims=1),
        helper.make_node("Less", ["row_max_count", "row_valid_count"], ["row_has_multiple_colors"]),
        helper.make_node("Not", ["row_has_multiple_colors"], ["row_single_color"]),
        helper.make_node("Greater", ["row_valid_count", "zero"], ["row_nonempty"]),
        helper.make_node("And", ["row_single_color", "row_nonempty"], ["row_frontier"]),
        helper.make_node("ReduceSum", ["input"], ["col_color_counts"], axes=[2], keepdims=1),
        helper.make_node("ReduceMax", ["col_color_counts"], ["col_max_count"], axes=[1], keepdims=1),
        helper.make_node("ReduceSum", ["valid_strength"], ["col_valid_count"], axes=[2], keepdims=1),
        helper.make_node("Less", ["col_max_count", "col_valid_count"], ["col_has_multiple_colors"]),
        helper.make_node("Not", ["col_has_multiple_colors"], ["col_single_color"]),
        helper.make_node("Greater", ["col_valid_count", "zero"], ["col_nonempty"]),
        helper.make_node("And", ["col_single_color", "col_nonempty"], ["col_frontier"]),
        helper.make_node("Or", ["row_frontier", "col_frontier"], ["frontier_broadcast"]),
        helper.make_node("And", ["frontier_broadcast", "valid_mask"], ["frontier_mask"]),
        helper.make_node("Where", ["frontier_mask", "fill_onehot", "input"], [spec.OUTPUT_NAME]),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_uniform_frontier_fill",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_hconcat_self_network(path: Path) -> None:
    """Horizontally concatenate the valid grid with itself.

    The valid width is inferred from the zero-hot padded input. Dynamic gather
    indices repeat columns inside twice that width and point to the first
    padded column everywhere else.
    """

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)

    initializers = [
        numpy_helper.from_array(np.arange(30, dtype=np.int64), "column_indices"),
    ]
    nodes = [
        helper.make_node(
            "ReduceMax",
            ["input"],
            ["valid_columns"],
            axes=[0, 1, 2],
            keepdims=0,
        ),
        helper.make_node(
            "ReduceSum",
            ["valid_columns"],
            ["valid_width_float"],
            axes=[0],
            keepdims=0,
        ),
        helper.make_node(
            "Cast",
            ["valid_width_float"],
            ["valid_width"],
            to=TensorProto.INT64,
        ),
        helper.make_node("Add", ["valid_width", "valid_width"], ["double_width"]),
        helper.make_node("Mod", ["column_indices", "valid_width"], ["wrapped_columns"]),
        helper.make_node(
            "Less",
            ["column_indices", "double_width"],
            ["inside_output_width"],
        ),
        helper.make_node(
            "Where",
            ["inside_output_width", "wrapped_columns", "valid_width"],
            ["gather_columns"],
        ),
        helper.make_node(
            "Gather",
            ["input", "gather_columns"],
            [spec.OUTPUT_NAME],
            axis=3,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_hconcat_self",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_spatial_repeat_network(path: Path, *, scale: int) -> None:
    """Repeat height and width positions by a fixed integer scale.

    This matches simple ARC-DSL ``upscale`` tasks while preserving NeuroGolf's
    zero-hot padding outside the true grid: repeated padding remains zero-hot.
    """
    if scale not in {2, 3}:
        raise ValueError("scale must be 2 or 3")
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    path.parent.mkdir(parents=True, exist_ok=True)
    shape = [1, 10, 30, 30]
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    row_index = np.array([min(i // scale, 29) for i in range(30)], dtype=np.int64)
    col_index = np.array([min(i // scale, 29) for i in range(30)], dtype=np.int64)
    initializers = [
        numpy_helper.from_array(row_index, "row_repeat_index"),
        numpy_helper.from_array(col_index, "col_repeat_index"),
    ]
    nodes = [
        helper.make_node("Gather", [spec.INPUT_NAME, "row_repeat_index"], ["rows_repeated"], axis=2),
        helper.make_node("Gather", ["rows_repeated", "col_repeat_index"], [spec.OUTPUT_NAME], axis=3),
    ]
    graph = helper.make_graph(nodes, "spatial_repeat", [x], [y], initializers)
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 10)])
    onnx.checker.check_model(model)
    onnx.save(model, str(path))


def build_fixed_3x3_rotation_network(path: Path, *, rotation: str) -> None:
    """Rotate the top-left 3x3 grid, leaving zero-hot padding untouched."""
    if rotation not in {"rot180", "rot270"}:
        raise ValueError("rotation must be rot180 or rot270")
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    path.parent.mkdir(parents=True, exist_ok=True)
    shape = [1, 10, 30, 30]
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    rev3 = np.array([2, 1, 0] + list(range(3, 30)), dtype=np.int64)
    initializers = [numpy_helper.from_array(rev3, "rev3")]
    nodes = []
    if rotation == "rot180":
        nodes.extend(
            [
                helper.make_node("Gather", [spec.INPUT_NAME, "rev3"], ["h_reversed"], axis=2),
                helper.make_node("Gather", ["h_reversed", "rev3"], [spec.OUTPUT_NAME], axis=3),
            ]
        )
    else:
        nodes.extend(
            [
                helper.make_node("Transpose", [spec.INPUT_NAME], ["transposed_hw"], perm=[0, 1, 3, 2]),
                helper.make_node("Gather", ["transposed_hw", "rev3"], [spec.OUTPUT_NAME], axis=2),
            ]
        )
    graph = helper.make_graph(nodes, "fixed_3x3_rotation", [x], [y], initializers)
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 10)])
    onnx.checker.check_model(model)
    onnx.save(model, str(path))


def build_fixed_mirror_tile_network(path: Path, *, height: int, width: int) -> None:
    """Tile a fixed valid rectangle with horizontal and vertical mirrors.

    This implements ARC-DSL patterns such as
    ``vconcat(hconcat(I, hmirror(I)), vmirror(hconcat(I, hmirror(I))))`` for
    tasks whose public and generated examples have fixed dimensions.
    """
    if not (1 <= height <= 15 and 1 <= width <= 15):
        raise ValueError("height and width must fit a doubled 30x30 canvas")
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    path.parent.mkdir(parents=True, exist_ok=True)
    shape = [1, 10, 30, 30]
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    rows = np.array(
        list(range(height)) + list(range(height - 1, -1, -1)) + [height] * (30 - 2 * height),
        dtype=np.int64,
    )
    cols = np.array(
        list(range(width)) + list(range(width - 1, -1, -1)) + [width] * (30 - 2 * width),
        dtype=np.int64,
    )
    initializers = [
        numpy_helper.from_array(rows, "mirror_tile_rows"),
        numpy_helper.from_array(cols, "mirror_tile_cols"),
    ]
    nodes = [
        helper.make_node("Gather", [spec.INPUT_NAME, "mirror_tile_rows"], ["rows_tiled"], axis=2),
        helper.make_node("Gather", ["rows_tiled", "mirror_tile_cols"], [spec.OUTPUT_NAME], axis=3),
    ]
    graph = helper.make_graph(nodes, "fixed_mirror_tile", [x], [y], initializers)
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 10)])
    onnx.checker.check_model(model)
    onnx.save(model, str(path))


def build_fixed_mirror_concat_network(path: Path, *, height: int, width: int, mode: str) -> None:
    """Concatenate a fixed rectangle with its horizontal or vertical mirror."""
    if mode not in {"hconcat_hmirror", "vconcat_vmirror"}:
        raise ValueError("mode must be hconcat_hmirror or vconcat_vmirror")
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("height and width must fit a 30x30 canvas")
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    path.parent.mkdir(parents=True, exist_ok=True)
    shape = [1, 10, 30, 30]
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    if mode == "hconcat_hmirror":
        if width > 15:
            raise ValueError("width must be <= 15 for horizontal concat")
        rows = np.arange(30, dtype=np.int64)
        cols = np.array(
            list(range(width)) + list(range(width - 1, -1, -1)) + [width] * (30 - 2 * width),
            dtype=np.int64,
        )
    else:
        if height > 15:
            raise ValueError("height must be <= 15 for vertical concat")
        rows = np.array(
            list(range(height)) + list(range(height - 1, -1, -1)) + [height] * (30 - 2 * height),
            dtype=np.int64,
        )
        cols = np.arange(30, dtype=np.int64)
    initializers = [
        numpy_helper.from_array(rows, "mirror_concat_rows"),
        numpy_helper.from_array(cols, "mirror_concat_cols"),
    ]
    nodes = [
        helper.make_node("Gather", [spec.INPUT_NAME, "mirror_concat_rows"], ["rows_concat"], axis=2),
        helper.make_node("Gather", ["rows_concat", "mirror_concat_cols"], [spec.OUTPUT_NAME], axis=3),
    ]
    graph = helper.make_graph(nodes, "fixed_mirror_concat", [x], [y], initializers)
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 10)])
    onnx.checker.check_model(model)
    onnx.save(model, str(path))


def build_dynamic_first_hsplit_network(path: Path, *, parts: int = 3) -> None:
    """Keep the first horizontal split of a valid zero-hot-padded grid."""
    if parts <= 1:
        raise ValueError("parts must be > 1")
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    path.parent.mkdir(parents=True, exist_ok=True)
    shape = [1, 10, 30, 30]
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    column_indices = np.arange(30, dtype=np.float32).reshape(1, 1, 1, 30)
    zero_hot = np.zeros((1, 10, 1, 1), dtype=np.float32)
    initializers = [
        numpy_helper.from_array(column_indices, "column_indices_float"),
        numpy_helper.from_array(np.array(float(parts), dtype=np.float32), "parts_float"),
        numpy_helper.from_array(zero_hot, "zero_hot"),
    ]
    nodes = [
        helper.make_node("ReduceMax", [spec.INPUT_NAME], ["valid_columns"], axes=[0, 1, 2], keepdims=0),
        helper.make_node("ReduceSum", ["valid_columns"], ["valid_width_float"], axes=[0], keepdims=0),
        helper.make_node("Div", ["valid_width_float", "parts_float"], ["split_width_float"]),
        helper.make_node("Less", ["column_indices_float", "split_width_float"], ["inside_first_split"]),
        helper.make_node("Where", ["inside_first_split", spec.INPUT_NAME, "zero_hot"], [spec.OUTPUT_NAME]),
    ]
    graph = helper.make_graph(nodes, "dynamic_first_hsplit", [x], [y], initializers)
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 10)])
    onnx.checker.check_model(model)
    onnx.save(model, str(path))


def build_fixed_crop_network(
    path: Path,
    *,
    row_start: int,
    col_start: int,
    height: int,
    width: int,
) -> None:
    """Crop a fixed rectangle to the top-left and zero-hot pad the rest."""
    if not (0 <= row_start < 30 and 0 <= col_start < 30):
        raise ValueError("crop start must be inside 30x30")
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("crop size must be positive")
    if row_start + height > 30 or col_start + width > 30:
        raise ValueError("crop must fit inside 30x30")
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    path.parent.mkdir(parents=True, exist_ok=True)
    shape = [1, 10, 30, 30]
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    rows = np.arange(row_start, row_start + height, dtype=np.int64)
    cols = np.arange(col_start, col_start + width, dtype=np.int64)
    initializers = [
        numpy_helper.from_array(rows, "crop_rows"),
        numpy_helper.from_array(cols, "crop_cols"),
    ]
    nodes = [
        helper.make_node("Gather", [spec.INPUT_NAME, "crop_rows"], ["row_crop"], axis=2),
        helper.make_node("Gather", ["row_crop", "crop_cols"], ["small_crop"], axis=3),
        helper.make_node(
            "Pad",
            ["small_crop"],
            [spec.OUTPUT_NAME],
            pads=[0, 0, 0, 0, 0, 0, 30 - height, 30 - width],
            value=0.0,
        ),
    ]
    graph = helper.make_graph(nodes, "fixed_crop", [x], [y], initializers)
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 10)])
    onnx.checker.check_model(model)
    onnx.save(model, str(path))


def build_most_color_canvas_network(path: Path, *, height: int, width: int) -> None:
    """Fill a fixed rectangle with the most frequent input color."""
    if not (1 <= height <= 30 and 1 <= width <= 30):
        raise ValueError("canvas size must fit 30x30")
    import onnx
    from onnx import TensorProto, helper, numpy_helper

    path.parent.mkdir(parents=True, exist_ok=True)
    shape = [1, 10, 30, 30]
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    initializers = [
        numpy_helper.from_array(np.array(10, dtype=np.int64), "depth"),
        numpy_helper.from_array(np.array([0.0, 1.0], dtype=np.float32), "onehot_values"),
        numpy_helper.from_array(np.array([1, 10, 1, 1], dtype=np.int64), "reshape_shape"),
        numpy_helper.from_array(np.array([1, 10, height, width], dtype=np.int64), "canvas_shape"),
    ]
    nodes = [
        helper.make_node("ReduceSum", [spec.INPUT_NAME], ["color_counts"], axes=[0, 2, 3], keepdims=0),
        helper.make_node("ArgMax", ["color_counts"], ["most_color"], axis=0, keepdims=1),
        helper.make_node("OneHot", ["most_color", "depth", "onehot_values"], ["onehot_color"], axis=1),
        helper.make_node("Reshape", ["onehot_color", "reshape_shape"], ["onehot_4d"]),
        helper.make_node("Expand", ["onehot_4d", "canvas_shape"], ["small_canvas"]),
        helper.make_node(
            "Pad",
            ["small_canvas"],
            [spec.OUTPUT_NAME],
            pads=[0, 0, 0, 0, 0, 0, 30 - height, 30 - width],
            value=0.0,
        ),
    ]
    graph = helper.make_graph(nodes, "most_color_canvas", [x], [y], initializers)
    model = helper.make_model(graph, ir_version=10, opset_imports=[helper.make_opsetid("", 10)])
    onnx.checker.check_model(model)
    onnx.save(model, str(path))


def build_valid_axis_reverse_network(path: Path, *, axis: int) -> None:
    """Reverse rows or columns inside the valid zero-hot-padded grid."""

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    if axis not in {2, 3}:
        raise ValueError("axis must be 2 (rows) or 3 (columns)")

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    index_name = "row_indices" if axis == 2 else "column_indices"
    reduce_axes = [0, 1, 3] if axis == 2 else [0, 1, 2]
    initializers = [
        numpy_helper.from_array(np.arange(30, dtype=np.int64), index_name),
        numpy_helper.from_array(np.array(1, dtype=np.int64), "one"),
    ]
    nodes = [
        helper.make_node(
            "ReduceMax",
            ["input"],
            ["valid_axis"],
            axes=reduce_axes,
            keepdims=0,
        ),
        helper.make_node(
            "ReduceSum",
            ["valid_axis"],
            ["valid_size_float"],
            axes=[0],
            keepdims=0,
        ),
        helper.make_node(
            "Cast",
            ["valid_size_float"],
            ["valid_size"],
            to=TensorProto.INT64,
        ),
        helper.make_node("Sub", ["valid_size", "one"], ["last_valid_index"]),
        helper.make_node(
            "Sub",
            ["last_valid_index", index_name],
            ["reversed_indices"],
        ),
        helper.make_node(
            "Less",
            [index_name, "valid_size"],
            ["inside_valid_axis"],
        ),
        helper.make_node(
            "Where",
            ["inside_valid_axis", "reversed_indices", index_name],
            ["gather_indices"],
        ),
        helper.make_node(
            "Gather",
            ["input", "gather_indices"],
            [spec.OUTPUT_NAME],
            axis=axis,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        f"arc_dsl_reverse_axis_{axis}",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_most_frequent_nonzero_bbox_crop_network(
    path: Path,
    *,
    padding_index: int = 29,
) -> None:
    """Crop the bounding box of the most frequent nonzero color.

    This is a compact specialization of the ARC-DSL
    ``objects -> argmax(size) -> subgrid`` family for tasks where every
    candidate object has a distinct nonzero color. The caller must verify that
    the chosen padding row and column are outside every valid input grid.
    """

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    if padding_index < 0 or padding_index >= 30:
        raise ValueError("padding_index must be within the 30x30 tensor")

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)

    coordinates = np.arange(30, dtype=np.int64)
    initializers = [
        numpy_helper.from_array(np.arange(1, 10, dtype=np.int64), "nonzero_colors"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "one"),
        numpy_helper.from_array(coordinates, "coordinates"),
        numpy_helper.from_array(coordinates[::-1].copy(), "reverse_coordinates"),
        numpy_helper.from_array(np.array([29], dtype=np.int64), "last_index"),
        numpy_helper.from_array(
            np.array([padding_index], dtype=np.int64),
            "padding_index",
        ),
    ]

    nodes = [
        helper.make_node(
            "ReduceSum",
            ["input"],
            ["color_counts"],
            axes=[2, 3],
            keepdims=0,
        ),
        helper.make_node(
            "Gather",
            ["color_counts", "nonzero_colors"],
            ["nonzero_counts"],
            axis=1,
        ),
        helper.make_node(
            "ArgMax",
            ["nonzero_counts"],
            ["selected_offset"],
            axis=1,
            keepdims=0,
        ),
        helper.make_node(
            "Add",
            ["selected_offset", "one"],
            ["selected_color"],
        ),
        helper.make_node(
            "Gather",
            ["input", "selected_color"],
            ["selected_plane"],
            axis=1,
        ),
        helper.make_node(
            "ReduceMax",
            ["selected_plane"],
            ["row_presence"],
            axes=[0, 1, 3],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["row_presence"],
            ["row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["row_presence", "reverse_coordinates"],
            ["reversed_row_presence"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_row_presence"],
            ["reverse_row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Sub",
            ["last_index", "reverse_row_start"],
            ["row_end"],
        ),
        helper.make_node(
            "ReduceMax",
            ["selected_plane"],
            ["column_presence"],
            axes=[0, 1, 2],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["column_presence"],
            ["column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["column_presence", "reverse_coordinates"],
            ["reversed_column_presence"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_column_presence"],
            ["reverse_column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Sub",
            ["last_index", "reverse_column_start"],
            ["column_end"],
        ),
        helper.make_node("Sub", ["row_end", "row_start"], ["row_span"]),
        helper.make_node("Add", ["row_span", "one"], ["crop_height"]),
        helper.make_node(
            "Less",
            ["coordinates", "crop_height"],
            ["inside_crop_rows"],
        ),
        helper.make_node(
            "Add",
            ["coordinates", "row_start"],
            ["shifted_rows"],
        ),
        helper.make_node(
            "Where",
            ["inside_crop_rows", "shifted_rows", "padding_index"],
            ["gather_rows"],
        ),
        helper.make_node(
            "Gather",
            ["input", "gather_rows"],
            ["row_cropped"],
            axis=2,
        ),
        helper.make_node(
            "Sub",
            ["column_end", "column_start"],
            ["column_span"],
        ),
        helper.make_node("Add", ["column_span", "one"], ["crop_width"]),
        helper.make_node(
            "Less",
            ["coordinates", "crop_width"],
            ["inside_crop_columns"],
        ),
        helper.make_node(
            "Add",
            ["coordinates", "column_start"],
            ["shifted_columns"],
        ),
        helper.make_node(
            "Where",
            ["inside_crop_columns", "shifted_columns", "padding_index"],
            ["gather_columns"],
        ),
        helper.make_node(
            "Gather",
            ["row_cropped", "gather_columns"],
            [spec.OUTPUT_NAME],
            axis=3,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_most_frequent_nonzero_bbox_crop",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_most_connected_nonzero_bbox_crop_network(
    path: Path,
    *,
    padding_index: int = 29,
) -> None:
    """Crop the color with the densest local eight-neighbor component.

    This specializes ``objects(diagonal=True) -> argmax(size) -> subgrid`` for
    ARC tasks where the target is the only dense nonzero component while other
    colors are sparse distractors. Maximum 3x3 density selects the component
    family; total color count breaks equal-density ties.
    """

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    if padding_index < 0 or padding_index >= 30:
        raise ValueError("padding_index must be within the 30x30 tensor")

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)

    coordinates = np.arange(30, dtype=np.int64)
    density_kernel = np.ones((10, 1, 3, 3), dtype=np.float32)
    initializers = [
        numpy_helper.from_array(density_kernel, "density_kernel"),
        numpy_helper.from_array(np.array(1000.0, dtype=np.float32), "density_scale"),
        numpy_helper.from_array(np.array(0.0, dtype=np.float32), "zero"),
        numpy_helper.from_array(np.arange(1, 10, dtype=np.int64), "nonzero_colors"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "one"),
        numpy_helper.from_array(coordinates, "coordinates"),
        numpy_helper.from_array(coordinates[::-1].copy(), "reverse_coordinates"),
        numpy_helper.from_array(np.array([29], dtype=np.int64), "last_index"),
        numpy_helper.from_array(
            np.array([padding_index], dtype=np.int64),
            "padding_index",
        ),
    ]

    nodes = [
        helper.make_node(
            "Conv",
            ["input", "density_kernel"],
            ["local_density"],
            group=10,
            pads=[1, 1, 1, 1],
            strides=[1, 1],
        ),
        helper.make_node(
            "ReduceMax",
            ["local_density"],
            ["max_density"],
            axes=[2, 3],
            keepdims=0,
        ),
        helper.make_node(
            "ReduceSum",
            ["input"],
            ["color_counts"],
            axes=[2, 3],
            keepdims=0,
        ),
        helper.make_node(
            "Mul",
            ["max_density", "density_scale"],
            ["weighted_density"],
        ),
        helper.make_node(
            "Add",
            ["weighted_density", "color_counts"],
            ["color_scores"],
        ),
        helper.make_node(
            "Gather",
            ["color_scores", "nonzero_colors"],
            ["nonzero_scores"],
            axis=1,
        ),
        helper.make_node(
            "ArgMax",
            ["nonzero_scores"],
            ["selected_offset"],
            axis=1,
            keepdims=0,
        ),
        helper.make_node("Add", ["selected_offset", "one"], ["selected_color"]),
        helper.make_node(
            "Gather",
            ["input", "selected_color"],
            ["selected_plane"],
            axis=1,
        ),
        helper.make_node(
            "ReduceMax",
            ["selected_plane"],
            ["row_presence"],
            axes=[0, 1, 3],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["row_presence"],
            ["row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["row_presence", "reverse_coordinates"],
            ["reversed_row_presence"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_row_presence"],
            ["reverse_row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node("Sub", ["last_index", "reverse_row_start"], ["row_end"]),
        helper.make_node(
            "ReduceMax",
            ["selected_plane"],
            ["column_presence"],
            axes=[0, 1, 2],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["column_presence"],
            ["column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["column_presence", "reverse_coordinates"],
            ["reversed_column_presence"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_column_presence"],
            ["reverse_column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Sub",
            ["last_index", "reverse_column_start"],
            ["column_end"],
        ),
        helper.make_node("Sub", ["row_end", "row_start"], ["row_span"]),
        helper.make_node("Add", ["row_span", "one"], ["crop_height"]),
        helper.make_node("Less", ["coordinates", "crop_height"], ["inside_crop_rows"]),
        helper.make_node("Add", ["coordinates", "row_start"], ["shifted_rows"]),
        helper.make_node(
            "Where",
            ["inside_crop_rows", "shifted_rows", "padding_index"],
            ["gather_rows"],
        ),
        helper.make_node("Gather", ["input", "gather_rows"], ["row_cropped"], axis=2),
        helper.make_node("Sub", ["column_end", "column_start"], ["column_span"]),
        helper.make_node("Add", ["column_span", "one"], ["crop_width"]),
        helper.make_node(
            "Less",
            ["coordinates", "crop_width"],
            ["inside_crop_columns"],
        ),
        helper.make_node("Add", ["coordinates", "column_start"], ["shifted_columns"]),
        helper.make_node(
            "Where",
            ["inside_crop_columns", "shifted_columns", "padding_index"],
            ["gather_columns"],
        ),
        helper.make_node(
            "Gather",
            ["row_cropped", "gather_columns"],
            ["gathered_output"],
            axis=3,
        ),
        helper.make_node(
            "Unsqueeze",
            ["inside_crop_rows"],
            ["row_output_mask"],
            axes=[1],
        ),
        helper.make_node(
            "Unsqueeze",
            ["inside_crop_columns"],
            ["column_output_mask"],
            axes=[0],
        ),
        helper.make_node(
            "And",
            ["row_output_mask", "column_output_mask"],
            ["spatial_output_mask"],
        ),
        helper.make_node(
            "Unsqueeze",
            ["spatial_output_mask"],
            ["output_mask"],
            axes=[0, 1],
        ),
        helper.make_node(
            "Where",
            ["output_mask", "gathered_output", "zero"],
            [spec.OUTPUT_NAME],
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_most_connected_nonzero_bbox_crop",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_zero_bbox_vertical_mirror_crop_network(
    path: Path,
    *,
    valid_width: int = 16,
    crop_size: int = 3,
) -> None:
    """Crop zero-color coordinates from a horizontally mirrored input.

    ARC-DSL names the left-right reflection ``vmirror`` because the mirror
    axis is vertical. This task specialization assumes a fixed valid width
    and square zero-color bounding box, both verified against official and
    generated examples before the graph is built.
    """

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    if valid_width <= 0 or valid_width > 30:
        raise ValueError("valid_width must be within the 30x30 tensor")
    if crop_size <= 0 or crop_size > 30:
        raise ValueError("crop_size must be within the 30x30 tensor")

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    offsets = np.arange(crop_size, dtype=np.int64)
    mirrored_columns = np.arange(
        valid_width - 1,
        valid_width - crop_size - 1,
        -1,
        dtype=np.int64,
    )
    initializers = [
        numpy_helper.from_array(np.array([0], dtype=np.int64), "zero_channel"),
        numpy_helper.from_array(offsets, "crop_offsets"),
        numpy_helper.from_array(mirrored_columns, "mirrored_columns"),
    ]
    nodes = [
        helper.make_node(
            "Gather",
            ["input", "zero_channel"],
            ["zero_plane"],
            axis=1,
        ),
        helper.make_node(
            "ReduceMax",
            ["zero_plane"],
            ["zero_rows"],
            axes=[0, 1, 3],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["zero_rows"],
            ["row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "ReduceMax",
            ["zero_plane"],
            ["zero_columns"],
            axes=[0, 1, 2],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["zero_columns"],
            ["column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Add",
            ["row_start", "crop_offsets"],
            ["gather_rows"],
        ),
        helper.make_node(
            "Sub",
            ["mirrored_columns", "column_start"],
            ["gather_columns"],
        ),
        helper.make_node(
            "Gather",
            ["input", "gather_rows"],
            ["cropped_rows"],
            axis=2,
        ),
        helper.make_node(
            "Gather",
            ["cropped_rows", "gather_columns"],
            ["crop"],
            axis=3,
        ),
        helper.make_node(
            "Pad",
            ["crop"],
            [spec.OUTPUT_NAME],
            mode="constant",
            pads=[0, 0, 0, 0, 0, 0, 30 - crop_size, 30 - crop_size],
            value=0.0,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_zero_bbox_vertical_mirror_crop",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_nonzero_bbox_scaled_crop_network(
    path: Path,
    *,
    max_output_height: int,
    max_output_width: int,
    scale: int = 1,
) -> None:
    """Crop the nonzero bounding box and optionally upscale it.

    The graph gathers only the verified maximum output extent before padding,
    avoiding a full 30x30 dynamic crop intermediate. Rows and columns outside
    the example-specific bounding box are masked to zero-hot padding.
    """

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    if scale <= 0:
        raise ValueError("scale must be positive")
    if max_output_height <= 0 or max_output_height > 30:
        raise ValueError("max_output_height must be within the 30x30 tensor")
    if max_output_width <= 0 or max_output_width > 30:
        raise ValueError("max_output_width must be within the 30x30 tensor")

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    row_output_offsets = np.arange(max_output_height, dtype=np.int64)
    column_output_offsets = np.arange(max_output_width, dtype=np.int64)
    initializers = [
        numpy_helper.from_array(np.array([0], dtype=np.int64), "zero_channel"),
        numpy_helper.from_array(
            np.arange(29, -1, -1, dtype=np.int64),
            "reverse_coordinates",
        ),
        numpy_helper.from_array(np.array([29], dtype=np.int64), "last_index"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "one"),
        numpy_helper.from_array(np.array([scale], dtype=np.int64), "scale"),
        numpy_helper.from_array(
            row_output_offsets,
            "row_output_offsets",
        ),
        numpy_helper.from_array(
            column_output_offsets,
            "column_output_offsets",
        ),
        numpy_helper.from_array(
            row_output_offsets // scale,
            "row_source_offsets",
        ),
        numpy_helper.from_array(
            column_output_offsets // scale,
            "column_source_offsets",
        ),
    ]
    nodes = [
        helper.make_node(
            "ReduceSum",
            ["input"],
            ["valid_plane"],
            axes=[1],
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["input", "zero_channel"],
            ["zero_plane"],
            axis=1,
        ),
        helper.make_node(
            "Sub",
            ["valid_plane", "zero_plane"],
            ["nonzero_plane"],
        ),
        helper.make_node(
            "ReduceMax",
            ["nonzero_plane"],
            ["nonzero_rows"],
            axes=[0, 1, 3],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["nonzero_rows"],
            ["row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["nonzero_rows", "reverse_coordinates"],
            ["reversed_nonzero_rows"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_nonzero_rows"],
            ["reverse_row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Sub",
            ["last_index", "reverse_row_start"],
            ["row_end"],
        ),
        helper.make_node("Sub", ["row_end", "row_start"], ["row_span"]),
        helper.make_node("Add", ["row_span", "one"], ["crop_height"]),
        helper.make_node(
            "Mul",
            ["crop_height", "scale"],
            ["output_height"],
        ),
        helper.make_node(
            "ReduceMax",
            ["nonzero_plane"],
            ["nonzero_columns"],
            axes=[0, 1, 2],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["nonzero_columns"],
            ["column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["nonzero_columns", "reverse_coordinates"],
            ["reversed_nonzero_columns"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_nonzero_columns"],
            ["reverse_column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Sub",
            ["last_index", "reverse_column_start"],
            ["column_end"],
        ),
        helper.make_node(
            "Sub",
            ["column_end", "column_start"],
            ["column_span"],
        ),
        helper.make_node("Add", ["column_span", "one"], ["crop_width"]),
        helper.make_node(
            "Mul",
            ["crop_width", "scale"],
            ["output_width"],
        ),
        helper.make_node(
            "Add",
            ["row_start", "row_source_offsets"],
            ["gather_rows"],
        ),
        helper.make_node(
            "Add",
            ["column_start", "column_source_offsets"],
            ["gather_columns"],
        ),
        helper.make_node(
            "Gather",
            ["input", "gather_rows"],
            ["cropped_rows"],
            axis=2,
        ),
        helper.make_node(
            "Gather",
            ["cropped_rows", "gather_columns"],
            ["fixed_crop"],
            axis=3,
        ),
        helper.make_node(
            "Less",
            ["row_output_offsets", "output_height"],
            ["inside_rows"],
        ),
        helper.make_node(
            "Less",
            ["column_output_offsets", "output_width"],
            ["inside_columns"],
        ),
        helper.make_node(
            "Unsqueeze",
            ["inside_rows"],
            ["row_mask"],
            axes=[0, 1, 3],
        ),
        helper.make_node(
            "Unsqueeze",
            ["inside_columns"],
            ["column_mask"],
            axes=[0, 1, 2],
        ),
        helper.make_node("And", ["row_mask", "column_mask"], ["crop_mask"]),
        helper.make_node(
            "Cast",
            ["crop_mask"],
            ["crop_mask_float"],
            to=TensorProto.FLOAT,
        ),
        helper.make_node(
            "Mul",
            ["fixed_crop", "crop_mask_float"],
            ["masked_crop"],
        ),
        helper.make_node(
            "Pad",
            ["masked_crop"],
            [spec.OUTPUT_NAME],
            mode="constant",
            pads=[
                0,
                0,
                0,
                0,
                0,
                0,
                30 - max_output_height,
                30 - max_output_width,
            ],
            value=0.0,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        f"arc_dsl_nonzero_bbox_scaled_crop_{scale}",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_least_color_bbox_crop_network(
    path: Path,
    *,
    max_output_size: int,
) -> None:
    """Crop the bounding box of the least frequent color present."""

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    if max_output_size <= 0 or max_output_size > 30:
        raise ValueError("max_output_size must be within the 30x30 tensor")

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    output_offsets = np.arange(max_output_size, dtype=np.int64)
    initializers = [
        numpy_helper.from_array(np.array(0.0, dtype=np.float32), "zero"),
        numpy_helper.from_array(np.array(901.0, dtype=np.float32), "large_count"),
        numpy_helper.from_array(
            np.arange(29, -1, -1, dtype=np.int64),
            "reverse_coordinates",
        ),
        numpy_helper.from_array(np.array([29], dtype=np.int64), "last_index"),
        numpy_helper.from_array(np.array([30], dtype=np.int64), "axis_limit"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "one"),
        numpy_helper.from_array(output_offsets, "output_offsets"),
    ]
    nodes = [
        helper.make_node(
            "ReduceSum",
            ["input"],
            ["color_counts"],
            axes=[2, 3],
            keepdims=0,
        ),
        helper.make_node(
            "Greater",
            ["color_counts", "zero"],
            ["color_present"],
        ),
        helper.make_node(
            "Where",
            ["color_present", "color_counts", "large_count"],
            ["present_color_counts"],
        ),
        helper.make_node(
            "ArgMin",
            ["present_color_counts"],
            ["selected_color"],
            axis=1,
            keepdims=0,
        ),
        helper.make_node(
            "Gather",
            ["input", "selected_color"],
            ["selected_plane"],
            axis=1,
        ),
        helper.make_node(
            "ReduceMax",
            ["selected_plane"],
            ["selected_rows"],
            axes=[0, 1, 3],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["selected_rows"],
            ["row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["selected_rows", "reverse_coordinates"],
            ["reversed_selected_rows"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_selected_rows"],
            ["reverse_row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Sub",
            ["last_index", "reverse_row_start"],
            ["row_end"],
        ),
        helper.make_node("Sub", ["row_end", "row_start"], ["row_span"]),
        helper.make_node("Add", ["row_span", "one"], ["crop_height"]),
        helper.make_node(
            "ReduceMax",
            ["selected_plane"],
            ["selected_columns"],
            axes=[0, 1, 2],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["selected_columns"],
            ["column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["selected_columns", "reverse_coordinates"],
            ["reversed_selected_columns"],
            axis=0,
        ),
        helper.make_node(
            "ArgMax",
            ["reversed_selected_columns"],
            ["reverse_column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Sub",
            ["last_index", "reverse_column_start"],
            ["column_end"],
        ),
        helper.make_node(
            "Sub",
            ["column_end", "column_start"],
            ["column_span"],
        ),
        helper.make_node("Add", ["column_span", "one"], ["crop_width"]),
        helper.make_node(
            "Add",
            ["row_start", "output_offsets"],
            ["unclipped_gather_rows"],
        ),
        helper.make_node(
            "Less",
            ["unclipped_gather_rows", "axis_limit"],
            ["rows_in_bounds"],
        ),
        helper.make_node(
            "Where",
            ["rows_in_bounds", "unclipped_gather_rows", "last_index"],
            ["gather_rows"],
        ),
        helper.make_node(
            "Add",
            ["column_start", "output_offsets"],
            ["unclipped_gather_columns"],
        ),
        helper.make_node(
            "Less",
            ["unclipped_gather_columns", "axis_limit"],
            ["columns_in_bounds"],
        ),
        helper.make_node(
            "Where",
            ["columns_in_bounds", "unclipped_gather_columns", "last_index"],
            ["gather_columns"],
        ),
        helper.make_node(
            "Gather",
            ["input", "gather_rows"],
            ["cropped_rows"],
            axis=2,
        ),
        helper.make_node(
            "Gather",
            ["cropped_rows", "gather_columns"],
            ["fixed_crop"],
            axis=3,
        ),
        helper.make_node(
            "Less",
            ["output_offsets", "crop_height"],
            ["inside_rows"],
        ),
        helper.make_node(
            "Less",
            ["output_offsets", "crop_width"],
            ["inside_columns"],
        ),
        helper.make_node(
            "Unsqueeze",
            ["inside_rows"],
            ["row_mask"],
            axes=[0, 1, 3],
        ),
        helper.make_node(
            "Unsqueeze",
            ["inside_columns"],
            ["column_mask"],
            axes=[0, 1, 2],
        ),
        helper.make_node("And", ["row_mask", "column_mask"], ["crop_mask"]),
        helper.make_node(
            "Cast",
            ["crop_mask"],
            ["crop_mask_float"],
            to=TensorProto.FLOAT,
        ),
        helper.make_node(
            "Mul",
            ["fixed_crop", "crop_mask_float"],
            ["masked_crop"],
        ),
        helper.make_node(
            "Pad",
            ["masked_crop"],
            [spec.OUTPUT_NAME],
            mode="constant",
            pads=[
                0,
                0,
                0,
                0,
                0,
                0,
                30 - max_output_size,
                30 - max_output_size,
            ],
            value=0.0,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_least_color_bbox_crop",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_remove_isolated_foreground_network(path: Path) -> None:
    """Replace isolated eight-neighbor foreground pixels with background."""

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    neighbor_kernel = np.ones((1, 1, 3, 3), dtype=np.float32)
    neighbor_kernel[0, 0, 1, 1] = 0.0
    background = np.zeros((1, 10, 1, 1), dtype=np.float32)
    background[0, 0, 0, 0] = 1.0
    initializers = [
        numpy_helper.from_array(np.array([0], dtype=np.int64), "zero_channel"),
        numpy_helper.from_array(np.array(0.0, dtype=np.float32), "zero"),
        numpy_helper.from_array(neighbor_kernel, "neighbor_kernel"),
        numpy_helper.from_array(background, "background_onehot"),
    ]
    nodes = [
        helper.make_node(
            "ReduceSum",
            ["input"],
            ["valid_plane"],
            axes=[1],
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["input", "zero_channel"],
            ["zero_plane"],
            axis=1,
        ),
        helper.make_node(
            "Sub",
            ["valid_plane", "zero_plane"],
            ["foreground_plane"],
        ),
        helper.make_node(
            "Conv",
            ["foreground_plane", "neighbor_kernel"],
            ["neighbor_count"],
            pads=[1, 1, 1, 1],
            strides=[1, 1],
        ),
        helper.make_node(
            "Greater",
            ["neighbor_count", "zero"],
            ["has_neighbor"],
        ),
        helper.make_node(
            "Greater",
            ["foreground_plane", "zero"],
            ["is_foreground"],
        ),
        helper.make_node("Not", ["has_neighbor"], ["has_no_neighbor"]),
        helper.make_node(
            "And",
            ["is_foreground", "has_no_neighbor"],
            ["is_isolated"],
        ),
        helper.make_node(
            "Where",
            ["is_isolated", "background_onehot", "input"],
            [spec.OUTPUT_NAME],
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_remove_isolated_foreground",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_size_two_object_outbox_network(
    path: Path,
    *,
    object_color: int = 2,
    outbox_color: int = 3,
) -> None:
    """Paint the eight-neighbor outbox of every two-cell orthogonal object."""

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    cross_kernel = np.array(
        [[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]],
        dtype=np.float32,
    ).reshape(1, 1, 3, 3)
    box_kernel = np.ones((1, 1, 3, 3), dtype=np.float32)
    replacement = np.zeros((1, 10, 1, 1), dtype=np.float32)
    replacement[0, outbox_color, 0, 0] = 1.0
    initializers = [
        numpy_helper.from_array(np.array([object_color], dtype=np.int64), "object_channel"),
        numpy_helper.from_array(np.array(0.0, dtype=np.float32), "zero"),
        numpy_helper.from_array(cross_kernel, "cross_kernel"),
        numpy_helper.from_array(box_kernel, "box_kernel"),
        numpy_helper.from_array(replacement, "replacement_onehot"),
    ]
    nodes = [
        helper.make_node(
            "Gather",
            ["input", "object_channel"],
            ["object_plane"],
            axis=1,
        ),
        helper.make_node(
            "Conv",
            ["object_plane", "cross_kernel"],
            ["neighbor_count"],
            pads=[1, 1, 1, 1],
        ),
        helper.make_node(
            "Greater",
            ["object_plane", "zero"],
            ["is_object"],
        ),
        helper.make_node(
            "Greater",
            ["neighbor_count", "zero"],
            ["has_object_neighbor"],
        ),
        helper.make_node(
            "And",
            ["is_object", "has_object_neighbor"],
            ["size_two_mask"],
        ),
        helper.make_node(
            "Cast",
            ["size_two_mask"],
            ["size_two_float"],
            to=TensorProto.FLOAT,
        ),
        helper.make_node(
            "Conv",
            ["size_two_float", "box_kernel"],
            ["dilated_count"],
            pads=[1, 1, 1, 1],
        ),
        helper.make_node(
            "Greater",
            ["dilated_count", "zero"],
            ["dilated_mask"],
        ),
        helper.make_node("Not", ["size_two_mask"], ["outside_object"]),
        helper.make_node(
            "And",
            ["dilated_mask", "outside_object"],
            ["unbounded_outbox_mask"],
        ),
        helper.make_node(
            "ReduceSum",
            ["input"],
            ["valid_plane"],
            axes=[1],
            keepdims=1,
        ),
        helper.make_node(
            "Greater",
            ["valid_plane", "zero"],
            ["valid_mask"],
        ),
        helper.make_node(
            "And",
            ["unbounded_outbox_mask", "valid_mask"],
            ["outbox_mask"],
        ),
        helper.make_node(
            "Where",
            ["outbox_mask", "replacement_onehot", "input"],
            [spec.OUTPUT_NAME],
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_size_two_object_outbox",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_single_object_crop_hconcat_network(path: Path) -> None:
    """Crop a single 3x3 foreground object and duplicate it horizontally."""

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.FLOAT, shape)
    initializers = [
        numpy_helper.from_array(np.array([0], dtype=np.int64), "zero_channel"),
        numpy_helper.from_array(np.arange(3, dtype=np.int64), "row_offsets"),
        numpy_helper.from_array(
            np.array([0, 1, 2, 0, 1, 2], dtype=np.int64),
            "column_offsets",
        ),
    ]
    nodes = [
        helper.make_node(
            "ReduceSum",
            ["input"],
            ["valid_plane"],
            axes=[1],
            keepdims=1,
        ),
        helper.make_node(
            "Gather",
            ["input", "zero_channel"],
            ["zero_plane"],
            axis=1,
        ),
        helper.make_node(
            "Sub",
            ["valid_plane", "zero_plane"],
            ["foreground_plane"],
        ),
        helper.make_node(
            "ReduceMax",
            ["foreground_plane"],
            ["row_presence"],
            axes=[0, 1, 3],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["row_presence"],
            ["row_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node("Add", ["row_start", "row_offsets"], ["gather_rows"]),
        helper.make_node(
            "Gather",
            ["input", "gather_rows"],
            ["row_cropped"],
            axis=2,
        ),
        helper.make_node(
            "ReduceMax",
            ["foreground_plane"],
            ["column_presence"],
            axes=[0, 1, 2],
            keepdims=0,
        ),
        helper.make_node(
            "ArgMax",
            ["column_presence"],
            ["column_start"],
            axis=0,
            keepdims=1,
        ),
        helper.make_node(
            "Add",
            ["column_start", "column_offsets"],
            ["gather_columns"],
        ),
        helper.make_node(
            "Gather",
            ["row_cropped", "gather_columns"],
            ["small_output"],
            axis=3,
        ),
        helper.make_node(
            "Pad",
            ["small_output"],
            [spec.OUTPUT_NAME],
            mode="constant",
            pads=[0, 0, 0, 0, 0, 0, 27, 24],
            value=0.0,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_single_object_crop_hconcat",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", spec.OPSET)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def build_component_count_diagonal_network(
    path: Path,
    *,
    object_color: int = 8,
) -> None:
    """Render an N x N diagonal where N is the number of 4-connected objects."""

    import onnx
    from onnx import TensorProto, helper, numpy_helper

    shape = list(spec.TENSOR_SHAPE)
    x = helper.make_tensor_value_info(spec.INPUT_NAME, TensorProto.FLOAT, shape)
    y = helper.make_tensor_value_info(spec.OUTPUT_NAME, TensorProto.BOOL, shape)

    # Encode every padded 2x2 binary neighborhood as a number in [0, 15].
    # A 16-entry lookup table then evaluates the 4-connected Euler numerator:
    # one-pixel patterns contribute +1, three-pixel patterns -1, and diagonal
    # two-pixel patterns +2. Exact 3x3 rings are added back as holes.
    code_kernel = np.array(
        [[1.0, 2.0], [4.0, 8.0]],
        dtype=np.float16,
    ).reshape(1, 1, 2, 2)
    euler_lut = np.zeros(16, dtype=np.float16)
    euler_lut[[1, 2, 4, 8]] = 1.0
    euler_lut[[7, 11, 13, 14]] = -1.0
    euler_lut[[6, 9]] = 2.0
    ring_kernel = np.ones((1, 1, 3, 3), dtype=np.float16)
    ring_kernel[0, 0, 1, 1] = -8.0

    initializers = [
        numpy_helper.from_array(np.array([object_color], dtype=np.int64), "channel_start"),
        numpy_helper.from_array(np.array([object_color + 1], dtype=np.int64), "channel_end"),
        numpy_helper.from_array(np.array([1], dtype=np.int64), "channel_axis"),
        numpy_helper.from_array(code_kernel, "code_kernel"),
        numpy_helper.from_array(euler_lut, "euler_lut"),
        numpy_helper.from_array(ring_kernel, "ring_kernel"),
        numpy_helper.from_array(np.array(4.0, dtype=np.float16), "four"),
        numpy_helper.from_array(np.array(8.0, dtype=np.float16), "eight"),
        numpy_helper.from_array(
            np.arange(30, dtype=np.float16).reshape(1, 1, 30, 1),
            "row_grid",
        ),
        numpy_helper.from_array(
            np.arange(30, dtype=np.float16).reshape(1, 1, 1, 30),
            "column_grid",
        ),
        numpy_helper.from_array(
            np.zeros((1, 1, 30, 30), dtype=np.bool_),
            "false_plane",
        ),
    ]
    nodes = [
        helper.make_node(
            "Slice",
            ["input", "channel_start", "channel_end", "channel_axis", "channel_axis"],
            ["object_plane_float"],
        ),
        helper.make_node(
            "Cast",
            ["object_plane_float"],
            ["object_plane"],
            to=TensorProto.FLOAT16,
        ),
        helper.make_node(
            "Conv",
            ["object_plane", "code_kernel"],
            ["neighborhood_code"],
            pads=[1, 1, 1, 1],
        ),
        helper.make_node(
            "Cast",
            ["neighborhood_code"],
            ["neighborhood_index"],
            to=TensorProto.INT32,
        ),
        helper.make_node(
            "Gather",
            ["euler_lut", "neighborhood_index"],
            ["euler_contribution"],
            axis=0,
        ),
        helper.make_node(
            "ReduceSum",
            ["euler_contribution"],
            ["euler_numerator"],
            keepdims=0,
        ),
        helper.make_node(
            "Div",
            ["euler_numerator", "four"],
            ["euler_characteristic"],
        ),
        helper.make_node(
            "Conv",
            ["object_plane", "ring_kernel"],
            ["ring_code"],
        ),
        helper.make_node(
            "Equal",
            ["ring_code", "eight"],
            ["ring_mask"],
        ),
        helper.make_node(
            "Cast",
            ["ring_mask"],
            ["ring_values"],
            to=TensorProto.FLOAT16,
        ),
        helper.make_node(
            "ReduceSum",
            ["ring_values"],
            ["hole_count"],
            keepdims=0,
        ),
        helper.make_node(
            "Add",
            ["euler_characteristic", "hole_count"],
            ["component_count"],
        ),
        helper.make_node(
            "Less",
            ["row_grid", "component_count"],
            ["row_inside"],
        ),
        helper.make_node(
            "Less",
            ["column_grid", "component_count"],
            ["column_inside"],
        ),
        helper.make_node(
            "And",
            ["row_inside", "column_inside"],
            ["inside_square"],
        ),
        helper.make_node(
            "Equal",
            ["row_grid", "column_grid"],
            ["diagonal_line"],
        ),
        helper.make_node(
            "And",
            ["inside_square", "diagonal_line"],
            ["diagonal_mask"],
        ),
        helper.make_node(
            "Xor",
            ["inside_square", "diagonal_mask"],
            ["background_mask"],
        ),
        helper.make_node(
            "Concat",
            [
                "background_mask",
                "false_plane",
                "false_plane",
                "false_plane",
                "false_plane",
                "false_plane",
                "false_plane",
                "false_plane",
                "diagonal_mask",
                "false_plane",
            ],
            [spec.OUTPUT_NAME],
            axis=1,
        ),
    ]
    graph = helper.make_graph(
        nodes,
        "arc_dsl_component_count_diagonal",
        [x],
        [y],
        initializer=initializers,
    )
    model = helper.make_model(
        graph,
        ir_version=spec.IR_VERSION,
        opset_imports=[helper.make_opsetid("", 16)],
    )
    onnx.checker.check_model(model, full_check=True)
    onnx.shape_inference.infer_shapes(model, strict_mode=True)
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))
