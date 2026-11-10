#!/usr/bin/env python3
"""Inspect a GLB with the standard library; structural checks do not replace playback QA."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import struct
import sys


def read_glb(path):
    raw = path.read_bytes()
    if len(raw) < 20:
        raise ValueError('File is too short for a GLB')
    magic, version, total = struct.unpack_from('<4sII', raw)
    if magic != b'glTF' or version != 2 or total != len(raw):
        raise ValueError('Invalid GLB v2 header or file length')
    offset, doc, binary = 12, None, b''
    while offset < total:
        if offset + 8 > total:
            raise ValueError('Truncated chunk header')
        size, kind = struct.unpack_from('<I4s', raw, offset)
        offset += 8
        if size % 4 or offset + size > total:
            raise ValueError('Invalid chunk length')
        chunk = raw[offset:offset + size]
        offset += size
        if kind == b'JSON' and doc is None:
            doc = json.loads(chunk.rstrip(b' \x00').decode('utf-8'))
        elif kind == b'BIN\x00':
            binary = chunk
    if doc is None or str(doc.get('asset', {}).get('version')) != '2.0':
        raise ValueError('Missing glTF 2.0 JSON')
    return raw, doc, binary


def time_bounds(doc, binary, index):
    accessor = doc['accessors'][index]
    if accessor.get('min') and accessor.get('max'):
        return [accessor['min'][0], accessor['max'][0]]
    if accessor.get('componentType') != 5126 or accessor.get('type') != 'SCALAR' or 'sparse' in accessor or 'bufferView' not in accessor:
        return None
    view = doc['bufferViews'][accessor['bufferView']]
    if doc.get('buffers', [{}])[view.get('buffer', 0)].get('uri'):
        return None
    offset = view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    stride = view.get('byteStride', 4)
    count = accessor.get('count', 0)
    if not count or offset + (count - 1) * stride + 4 > len(binary):
        return None
    values = [struct.unpack_from('<f', binary, offset + k * stride)[0] for k in range(count)]
    return [min(values), max(values)]


def inspect(path):
    raw, doc, binary = read_glb(path)
    nodes, meshes, skins = (doc.get(k, []) for k in ('nodes', 'meshes', 'skins'))
    used_skins = {n['skin'] for n in nodes if 'mesh' in n and 'skin' in n}
    if any(i >= len(skins) or i < 0 for i in used_skins):
        raise ValueError('Mesh node refers to a missing skin')
    joint_nodes = {j for i in used_skins for j in skins[i].get('joints', [])}
    animations = []
    for animation in doc.get('animations', []):
        bounds = [time_bounds(doc, binary, s['input']) for s in animation.get('samplers', [])]
        bounds = [b for b in bounds if b is not None]
        channels = animation.get('channels', [])
        paths = collections.Counter(c.get('target', {}).get('path', '') for c in channels)
        bone_channels = sum(c.get('target', {}).get('node') in joint_nodes and c.get('target', {}).get('path') in {'translation', 'rotation', 'scale'} for c in channels)
        animations.append({'name': animation.get('name', ''), 'channels': len(channels), 'joint_transform_channels': bone_channels, 'target_paths': dict(paths), 'time_range': [min(b[0] for b in bounds), max(b[1] for b in bounds)] if bounds else None})
    primitives = []
    for mesh in meshes:
        for primitive in mesh.get('primitives', []):
            attributes = primitive.get('attributes', {})
            vertices = doc['accessors'][attributes['POSITION']]['count'] if 'POSITION' in attributes else 0
            indices = doc['accessors'][primitive['indices']]['count'] if 'indices' in primitive else vertices
            mode = primitive.get('mode', 4)
            triangles = indices // 3 if mode == 4 else max(0, indices - 2) if mode in (5, 6) else 0
            primitives.append({'vertices': vertices, 'triangles': triangles, 'has_joints': 'JOINTS_0' in attributes, 'has_weights': 'WEIGHTS_0' in attributes})
    structural_animation = bool(used_skins and joint_nodes and any(p['has_joints'] and p['has_weights'] for p in primitives) and any(a['joint_transform_channels'] for a in animations))
    return {'file': str(path.resolve()), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest(), 'mesh_count': len(meshes), 'triangle_count': sum(p['triangles'] for p in primitives), 'declared_skin_count': len(skins), 'used_skin_count': len(used_skins), 'joint_count': len(joint_nodes), 'animations': animations, 'image_count': len(doc.get('images', [])), 'external_images': [i.get('uri') for i in doc.get('images', []) if i.get('uri') and not i['uri'].startswith('data:')], 'required_extensions': doc.get('extensionsRequired', []), 'structural_skeletal_animation': structural_animation, 'visual_playback_verified': False, 'note': 'Structure only. Reimport and inspect actual motion, textures and clothing deformation.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('model', type=Path)
    parser.add_argument('--out', type=Path, help='Save JSON under the current project Codex directory')
    parser.add_argument('--require-animation', action='store_true', help='Exit 2 if no used skin and joint animation are present')
    args = parser.parse_args()
    try:
        result = inspect(args.model)
    except (OSError, ValueError, KeyError, IndexError, struct.error) as exc:
        print(json.dumps({'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text + '\n', encoding='utf-8')
    print(text)
    return 2 if args.require_animation and not result['structural_skeletal_animation'] else 0


if __name__ == '__main__':
    sys.exit(main())
