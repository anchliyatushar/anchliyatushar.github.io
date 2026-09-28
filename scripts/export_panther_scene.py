"""Export the actual Panther Bloom Rhino model as a compact, grouped glTF scene.

Usage (offline build tool, never run in a visitor's browser)::

    python export_panther_scene.py /path/to/f2.3dm --output public/models

Requires numpy, rhino3dm and fast-simplification. ``--dependency-path`` may be
repeated to use temporary tooling without adding Python packages to this site.
The source 3DM and STL are deliberately not copied into the public directory.

The four assembly nodes share one origin. The brooch front is the XY plane,
with +Y up and +Z facing the camera. Its longest dimension is five scene units.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import dataclass
from itertools import chain
import json
from pathlib import Path
import struct
import sys
import time

import numpy as np


MATERIALS = [
    {
        "name": "polished-gold",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.91, 0.63, 0.24, 1],
            "metallicFactor": 1,
            "roughnessFactor": 0.235,
        },
        "doubleSided": True,
    },
    {
        "name": "pale-gold-settings",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.92, 0.78, 0.46, 1],
            "metallicFactor": 1,
            "roughnessFactor": 0.26,
        },
        "doubleSided": True,
    },
    {
        "name": "sapphire-centre",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.025, 0.15, 0.42, 1],
            "metallicFactor": 0.13,
            "roughnessFactor": 0.085,
        },
        "extensions": {"KHR_materials_ior": {"ior": 1.77}},
        "doubleSided": True,
    },
    {
        "name": "ice-blue-stones",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.37, 0.74, 0.92, 1],
            "metallicFactor": 0.05,
            "roughnessFactor": 0.1,
        },
        "extensions": {
            "KHR_materials_ior": {"ior": 1.65},
            "KHR_materials_transmission": {"transmissionFactor": 0.14},
        },
        "doubleSided": True,
    },
    {
        "name": "blue-pave-stones",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.12, 0.28, 0.47, 1],
            "metallicFactor": 0.04,
            "roughnessFactor": 0.13,
        },
        "extensions": {"KHR_materials_ior": {"ior": 1.77}},
        "doubleSided": True,
    },
    {
        "name": "black-onyx-eyes",
        "pbrMetallicRoughness": {
            "baseColorFactor": [0.004, 0.005, 0.006, 1],
            "metallicFactor": 0,
            "roughnessFactor": 0.17,
        },
        "extensions": {"KHR_materials_ior": {"ior": 1.54}},
        "doubleSided": True,
    },
]


@dataclass
class Geometry:
    positions: np.ndarray
    triangles: np.ndarray
    normals: np.ndarray | None = None


def arrays_from_mesh(mesh, preserve_normals: bool = False) -> Geometry | None:
    if not mesh or not len(mesh.Vertices) or not len(mesh.Faces):
        return None
    vertices = np.fromiter(
        (value for point in mesh.Vertices for value in (point.X, point.Y, point.Z)),
        dtype=np.float64,
        count=len(mesh.Vertices) * 3,
    ).reshape(-1, 3)
    faces = np.fromiter(
        chain.from_iterable(mesh.Faces), dtype=np.int32, count=len(mesh.Faces) * 4
    ).reshape(-1, 4)
    quads = faces[:, 2] != faces[:, 3]
    triangles = np.concatenate((faces[:, :3], faces[quads][:, (0, 2, 3)]))
    normals = None
    if preserve_normals and len(mesh.Normals) == len(mesh.Vertices):
        normals = np.fromiter(
            (value for normal in mesh.Normals for value in (normal.X, normal.Y, normal.Z)),
            dtype=np.float64,
            count=len(mesh.Normals) * 3,
        ).reshape(-1, 3)
    return Geometry(vertices, triangles, normals)


def combine(geometries: list[Geometry]) -> Geometry | None:
    if not geometries:
        return None
    if len(geometries) == 1:
        return geometries[0]
    offsets = np.cumsum([0] + [len(geometry.positions) for geometry in geometries[:-1]])
    positions = np.concatenate([geometry.positions for geometry in geometries])
    triangles = np.concatenate(
        [geometry.triangles + offset for geometry, offset in zip(geometries, offsets)]
    ).astype(np.int32)
    normals = None
    if all(geometry.normals is not None for geometry in geometries):
        normals = np.concatenate([geometry.normals for geometry in geometries])
    return Geometry(positions, triangles, normals)


def geometry_mesh(geometry, rhino, preserve_normals: bool = False) -> Geometry | None:
    if isinstance(geometry, rhino.Mesh):
        return arrays_from_mesh(geometry, preserve_normals)
    if isinstance(geometry, rhino.Brep):
        meshes = []
        for face in geometry.Faces:
            mesh = face.GetMesh(rhino.MeshType.Render)
            # Imported surfaces may carry only an analysis mesh.
            if not mesh:
                mesh = face.GetMesh(rhino.MeshType.Analysis)
            result = arrays_from_mesh(mesh, preserve_normals)
            if result:
                meshes.append(result)
        return combine(meshes)
    return None


def weld(geometry: Geometry) -> Geometry:
    # Rhino Breps contain coincident vertices on face boundaries. Welding those
    # vertices before quadric decimation preserves continuity across surfaces.
    positions, index = np.unique(np.round(geometry.positions, 7), axis=0, return_inverse=True)
    triangles = index[geometry.triangles].astype(np.int32)
    keep = (triangles[:, 0] != triangles[:, 1]) & (triangles[:, 1] != triangles[:, 2]) & (triangles[:, 2] != triangles[:, 0])
    return Geometry(positions, triangles[keep])


def simplify(geometry: Geometry, target: int, simplifier) -> Geometry:
    geometry = weld(geometry)
    if len(geometry.triangles) <= target:
        return geometry
    positions, triangles = simplifier.simplify(
        geometry.positions,
        geometry.triangles,
        target_count=target,
        agg=6.5,
        preserve_border=False,
    )
    if not len(triangles):
        raise ValueError("Mesh simplification removed a complete Rhino object")
    return Geometry(positions, triangles)


def normals_for(geometry: Geometry, faceted: bool = False) -> Geometry:
    positions, triangles = geometry.positions, geometry.triangles
    corners = positions[triangles]
    normal = np.cross(corners[:, 1] - corners[:, 0], corners[:, 2] - corners[:, 0])
    valid = np.linalg.norm(normal, axis=1) > 1e-12
    triangles, corners, normal = triangles[valid], corners[valid], normal[valid]
    if faceted:
        normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
        # Retain hard-cut facet normals, while sharing vertices between the two
        # triangles of a planar facet. This cuts gem storage almost in half.
        attributes = np.concatenate((corners.reshape(-1, 3), np.repeat(normal, 3, axis=0)), axis=1)
        _, first, index = np.unique(np.round(attributes, 6), axis=0, return_index=True, return_inverse=True)
        return Geometry(
            attributes[first, :3],
            index.astype(np.int32).reshape(-1, 3),
            attributes[first, 3:],
        )
    normals = np.zeros_like(positions)
    for corner in range(3):
        np.add.at(normals, triangles[:, corner], normal)
    # A few thin Rhino seams have coincident, opposite-facing triangles. Give
    # cancelled vertex normals the local face normal instead of a zero vector.
    cancelled = np.linalg.norm(normals, axis=1) < 1e-12
    if cancelled.any():
        for corner in range(3):
            needs_normal = cancelled[triangles[:, corner]]
            normals[triangles[needs_normal, corner]] = normal[needs_normal]
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    used, index = np.unique(triangles, return_inverse=True)
    return Geometry(positions[used], index.reshape(-1, 3).astype(np.int32), normals[used])


def preserve_polished_surface(geometry: Geometry) -> Geometry:
    """Keep Rhino's surface shading and original face-boundary vertex splits.

    Averaging normals across a thin leaf's top, bevel and underside bends a
    polished reflection toward the edge. Aggressive reduction then exposes
    broad triangular patches in that reflection. These few large surfaces are
    inexpensive enough to retain in full, with the CAD surface normals intact.
    """
    if geometry.normals is None:
        raise ValueError("A polished Rhino surface is missing its cached normals")
    lengths = np.linalg.norm(geometry.normals, axis=1, keepdims=True)
    if not np.isfinite(geometry.normals).all() or (lengths < 1e-6).any():
        raise ValueError("A polished Rhino surface has invalid cached normals")
    return Geometry(geometry.positions, geometry.triangles, geometry.normals / lengths)


def transformed(geometry: Geometry, transform) -> Geometry:
    matrix = np.array([[getattr(transform, f"M{row}{column}") for column in range(4)] for row in range(4)])
    positions = geometry.positions @ matrix[:3, :3].T + matrix[:3, 3]
    triangles = geometry.triangles.copy()
    if np.linalg.det(matrix[:3, :3]) < 0:
        triangles = triangles[:, (0, 2, 1)]
    return Geometry(positions, triangles)


def group_for(layer: str, positions: np.ndarray) -> tuple[str, int]:
    if layer.startswith("Gem"):
        return "gems", 2 if layer == "Gem 01" else 4 if layer == "Gem 04" else 3
    if layer in ("User Layer 01", "User Layer 03"):
        return "face", 0 if layer == "User Layer 01" else 1
    if layer == "Creation Curves":
        return "feather", 0
    if layer == "Heads":
        return ("feather" if positions[:, 0].mean() < -3 else "botanical"), 1
    return "botanical", 0


def target_for(layer: str, count: int) -> int:
    if layer == "User Layer 01":
        return 26000
    if layer == "User Layer 03":
        # Keep all 998 gold pavé supports; simplify each one rather than losing
        # complete settings by uniformly sampling triangles from the original.
        return min(count, 32 if count < 1500 else 64)
    if layer == "Heads":
        return min(count, 32)
    if layer == "Creation Curves":
        return max(60, int(count * 0.20))
    if layer == "Metal 02":
        return max(44, min(220, int(count * 0.025)))
    if layer.startswith("User Layer"):
        return max(100, int(count * 0.27))
    return count


def split_eye_material(scene: dict, metadata: dict) -> None:
    """Recolour the original recessed eye surfaces while retaining gold rims.

    The sculpture is one connected mesh, so there are no separate eye objects
    to assign a material to. These deliberately inset front-projection masks
    were inspected against the source eye recesses. Selecting existing faces
    keeps the positions, normals, shape and triangle count exactly unchanged.
    The depth/normal tests exclude the back of the head and steep gold rims.
    """
    gold = scene[("face", 0)]
    centers = gold.positions[gold.triangles].mean(axis=1)
    normals = gold.normals[gold.triangles].mean(axis=1)
    left_boundary = np.array([
        [-.705, 1.339], [-.659, 1.342], [-.613, 1.343], [-.565, 1.335],
        [-.516, 1.322], [-.480, 1.293], [-.485, 1.255], [-.509, 1.218],
        [-.549, 1.199], [-.585, 1.198], [-.628, 1.214], [-.664, 1.246],
        [-.687, 1.287],
    ])
    right_boundary = left_boundary.copy()
    right_boundary[:, 0] = -.28 - right_boundary[:, 0]

    def mask_for(boundary):
        x, y = centers[:, 0], centers[:, 1]
        inside = np.zeros(len(centers), dtype=bool)
        for start, end in zip(boundary, np.roll(boundary, -1, axis=0)):
            crosses = ((start[1] > y) != (end[1] > y)) & (
                x < (end[0] - start[0]) * (y - start[1]) / (end[1] - start[1] + 1e-20) + start[0]
            )
            inside ^= crosses
        return inside & (centers[:, 2] > .06) & (normals[:, 2] > .3)

    left, right = mask_for(left_boundary), mask_for(right_boundary)
    if not left.any() or not right.any() or (left & right).any():
        raise ValueError("Eye material masks must select two separate, nonempty front surfaces")
    selected = left | right

    def subset(mask):
        faces = gold.triangles[mask]
        used, indices = np.unique(faces, return_inverse=True)
        return Geometry(gold.positions[used], indices.reshape(-1, 3).astype(np.int32), gold.normals[used])

    scene[("face", 0)] = subset(~selected)
    scene[("face", 5)] = subset(selected)
    assert len(scene[("face", 0)].triangles) + len(scene[("face", 5)].triangles) == len(gold.triangles)
    metadata["eyes"] = {"material": "black-onyx-eyes", "geometryUnchanged": True}
    for name, mask in (("left", left), ("right", right)):
        positions = gold.positions[gold.triangles[mask]].reshape(-1, 3)
        metadata["eyes"][name] = {
            "triangles": int(mask.sum()),
            "center": positions.mean(axis=0).tolist(),
            "bounds": {"min": positions.min(axis=0).tolist(), "max": positions.max(axis=0).tolist()},
        }


def load_scene(source: Path, rhino, simplifier) -> tuple[dict, dict]:
    model = rhino.File3dm.Read(str(source))
    if not model:
        raise ValueError(f"Cannot read Rhino model: {source}")
    objects = {str(obj.Attributes.Id): obj for obj in model.Objects}
    definitions = {str(definition.Id): definition for definition in model.InstanceDefinitions}
    definition_geometry = {}
    definition_source_counts = {}
    buckets = defaultdict(list)
    stats = defaultdict(lambda: {"objects": 0, "sourceTriangles": 0, "exportTriangles": 0})
    started = time.monotonic()
    for object_index, obj in enumerate(model.Objects):
        attributes = obj.Attributes
        layer = model.Layers[attributes.LayerIndex]
        if attributes.Mode == rhino.ObjectMode.InstanceDefinitionObject or not attributes.Visible or not layer.Visible:
            continue
        name = layer.Name
        if name in ("User Layer 02", "Lights", "Finger Sizes", "Cutting Objects", "BelCutter"):
            continue
        geometry = obj.Geometry
        # The broad botanical leaves and ribbons are these named physical
        # Breps. Metal 02 contains the much smaller round gemstone settings.
        polished_surface = (
            isinstance(geometry, rhino.Brep)
            and name.startswith("User Layer ")
            and int(name.rsplit(" ", 1)[1]) >= 17
        )
        if isinstance(geometry, rhino.InstanceReference):
            definition_key = str(geometry.ParentIdefId)
            if definition_key not in definition_geometry:
                definition = definitions[definition_key]
                parts = [geometry_mesh(objects[str(object_id)].Geometry, rhino) for object_id in definition.GetObjectIds()]
                template = combine([part for part in parts if part])
                definition_source_counts[definition_key] = len(template.triangles) if template else 0
                definition_geometry[definition_key] = simplify(template, 80, simplifier) if template else None
            template = definition_geometry[definition_key]
            if template is None:
                raise ValueError(f"Rhino instance {definition_key} has no cached mesh")
            mesh = transformed(template, geometry.Xform)
        else:
            mesh = geometry_mesh(geometry, rhino, preserve_normals=polished_surface)
        if mesh is None:
            continue
        source_count = definition_source_counts[definition_key] if isinstance(geometry, rhino.InstanceReference) else len(mesh.triangles)
        group, material = group_for(name, mesh.positions)
        if polished_surface:
            mesh = preserve_polished_surface(mesh)
        else:
            if group != "gems":
                mesh = simplify(mesh, target_for(name, source_count), simplifier)
            mesh = normals_for(mesh, faceted=group == "gems")
        buckets[(group, material)].append(mesh)
        stats[name]["objects"] += 1
        stats[name]["sourceTriangles"] += source_count
        stats[name]["exportTriangles"] += len(mesh.triangles)
        if polished_surface:
            stats[name]["normalSource"] = "Rhino cached surface normals"
            stats[name]["meshPolicy"] = "Full source tessellation; original hard-edge vertex splits"
        if object_index % 100 == 0 or name == "User Layer 01":
            print(f"Read {object_index + 1}/{len(model.Objects)} Rhino objects ({time.monotonic() - started:.1f}s)", flush=True)

    scene = {key: combine(meshes) for key, meshes in buckets.items()}
    minimum = np.min([mesh.positions.min(axis=0) for mesh in scene.values()], axis=0)
    maximum = np.max([mesh.positions.max(axis=0) for mesh in scene.values()], axis=0)
    centre = (minimum + maximum) * 0.5
    scale = 5.0 / (maximum - minimum).max()
    for mesh in scene.values():
        mesh.positions = ((mesh.positions - centre) * scale).astype(np.float32)
        mesh.normals = mesh.normals.astype(np.float32)
    metadata = {
        "source": source.name,
        "description": "Rhino render meshes with resolved block transforms. Broad polished leaves/ribbons retain full source tessellation and cached surface normals; smaller details are simplified independently.",
        "coordinateSystem": {"front": "+Z", "up": "+Y", "frontPlane": "XY", "longestExtent": 5},
        "sourceBounds": {"min": minimum.tolist(), "max": maximum.tolist()},
        "sourceCentre": centre.tolist(),
        "sourceToSceneScale": float(scale),
        "layers": dict(stats),
        "assemblies": {},
    }
    split_eye_material(scene, metadata)
    return scene, metadata


def export_glb(scene: dict, metadata: dict, target: Path) -> None:
    document = {
        "asset": {"version": "2.0", "generator": "Panther Bloom Rhino scene exporter"},
        "scene": 0,
        "scenes": [{"name": "Panther Bloom Brooch", "nodes": [0]}],
        "nodes": [{"name": "panther-bloom", "children": []}],
        "meshes": [],
        "materials": MATERIALS,
        "accessors": [],
        "bufferViews": [],
        "buffers": [],
        "extensionsUsed": ["KHR_materials_ior", "KHR_materials_transmission"],
    }
    binary = bytearray()

    def accessor(array, component_type, kind, target_type, extrema=False):
        while len(binary) % 4:
            binary.append(0)
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer": 0, "byteOffset": len(binary), "byteLength": array.nbytes, "target": target_type})
        binary.extend(array.tobytes())
        data = {"bufferView": view, "componentType": component_type, "count": len(array), "type": kind}
        if extrema:
            data.update({"min": array.min(axis=0).tolist(), "max": array.max(axis=0).tolist()})
        index = len(document["accessors"])
        document["accessors"].append(data)
        return index

    for group in ("face", "feather", "botanical", "gems"):
        primitives = []
        group_positions = []
        triangles = 0
        vertices = 0
        for (assembly, material), geometry in scene.items():
            if assembly != group:
                continue
            position = accessor(geometry.positions.astype("<f4"), 5126, "VEC3", 34962, extrema=True)
            normal = accessor(geometry.normals.astype("<f4"), 5126, "VEC3", 34962)
            indexes = geometry.triangles.reshape(-1)
            short = len(geometry.positions) < 65536
            index = accessor(indexes.astype("<u2" if short else "<u4"), 5123 if short else 5125, "SCALAR", 34963)
            primitives.append({"attributes": {"POSITION": position, "NORMAL": normal}, "indices": index, "material": material, "mode": 4})
            group_positions.append(geometry.positions)
            triangles += len(geometry.triangles)
            vertices += len(geometry.positions)
        positions = np.concatenate(group_positions)
        bounds = {"min": positions.min(axis=0).tolist(), "max": positions.max(axis=0).tolist()}
        metadata["assemblies"][group] = {"vertices": vertices, "triangles": triangles, "bounds": bounds}
        mesh_index = len(document["meshes"])
        document["meshes"].append({"name": group, "primitives": primitives})
        node_index = len(document["nodes"])
        document["nodes"].append({"name": group, "mesh": mesh_index, "extras": {"assembly": group}})
        document["nodes"][0]["children"].append(node_index)

    while len(binary) % 4:
        binary.append(0)
    document["buffers"].append({"byteLength": len(binary)})
    json_chunk = json.dumps(document, separators=(",", ":")).encode()
    json_chunk += b" " * (-len(json_chunk) % 4)
    total_size = 12 + 8 + len(json_chunk) + 8 + len(binary)
    target.write_bytes(
        struct.pack("<4sII", b"glTF", 2, total_size)
        + struct.pack("<I4s", len(json_chunk), b"JSON") + json_chunk
        + struct.pack("<I4s", len(binary), b"BIN\0") + binary
    )
    metadata["bytes"] = total_size
    metadata["triangles"] = sum(assembly["triangles"] for assembly in metadata["assemblies"].values())


def preview_scene(scene: dict, output: Path) -> None:
    """A deterministic, temporary front projection to inspect shape completeness."""
    from PIL import Image, ImageDraw

    size = 1400
    image = Image.new("RGB", (size, size), (12, 16, 19))
    draw = ImageDraw.Draw(image)
    polygons = []
    palette = [(217, 167, 65), (235, 207, 146), (33, 93, 156), (125, 205, 239), (60, 109, 152), (15, 18, 22)]
    light = np.array([-0.3, 0.65, 0.7])
    light /= np.linalg.norm(light)
    for (_, material), geometry in scene.items():
        corners = geometry.positions[geometry.triangles]
        normal = geometry.normals[geometry.triangles].mean(axis=1)
        shade = 0.36 + 0.64 * np.clip(normal @ light, 0, 1)
        colours = np.minimum(np.array(palette[material])[None, :] * shade[:, None], 255).astype(np.uint8)
        projected = corners[:, :, :2] * np.array([size * .17, -size * .17]) + size / 2
        polygons.extend(zip(corners[:, :, 2].mean(axis=1), projected, colours))
    for _, points, colour in sorted(polygons, key=lambda item: item[0]):
        draw.polygon([tuple(point) for point in points], fill=tuple(colour))
    image.save(output)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=Path("public/models"))
    parser.add_argument("--dependency-path", action="append", default=[])
    parser.add_argument("--preview", type=Path)
    options = parser.parse_args()
    for dependency_path in options.dependency_path:
        sys.path.insert(0, dependency_path)
    import fast_simplification
    import rhino3dm

    scene, metadata = load_scene(options.source, rhino3dm, fast_simplification)
    options.output.mkdir(parents=True, exist_ok=True)
    export_glb(scene, metadata, options.output / "panther-bloom.glb")
    (options.output / "panther-bloom-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    if options.preview:
        preview_scene(scene, options.preview)
    print(json.dumps(metadata, indent=2), flush=True)


if __name__ == "__main__":
    main()
