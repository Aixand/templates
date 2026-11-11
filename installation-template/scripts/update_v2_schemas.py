#!/usr/bin/env python3
"""Generate and check the schema-2 contracts from shared, explicit definitions."""

import argparse
from copy import deepcopy
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STRING = {"type": "string", "minLength": 1}
STRINGS = {"type": "array", "items": STRING, "uniqueItems": True}
DIGEST = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
PRODUCT = {"type": "string", "pattern": "^[a-z0-9][a-z0-9_-]*(/[a-z0-9][a-z0-9_-]*)*$"}
COMMAND = {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]*$"}
PATH = {
    "type": "string",
    "minLength": 1,
    "pattern": "^(?!/)(?!.*(?:^|/)\\.\\.?(?:/|$))(?!.*[\\\\:\\r\\n])[^/]+(?:/[^/]+)*$",
}
TARGET = {
    "enum": [
        "linux-x86_64-gnu",
        "linux-arm64-gnu",
        "macos-x86_64",
        "macos-arm64",
        "windows-x86_64-msvc",
        "windows-arm64-msvc",
    ]
}
ARGV = {"type": "array", "minItems": 1, "items": {"type": "string"}}
ARGV_LIST = {"type": "array", "items": ARGV}


def obj(properties, required=()):
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": properties,
        "required": list(required),
    }


def mapping(value, names=None):
    result = {"type": "object", "additionalProperties": value}
    if names:
        result["propertyNames"] = names
    return result


BASELINE = {
    **obj(
        {
            k: {"type": "string", "pattern": r"^\d+(?:\.\d+)*$"}
            for k in ("libc", "os-version")
        }
    ),
    "minProperties": 1,
}


def ref(name):
    return {"$ref": "#/$defs/" + name}


def document(title, body, definitions):
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        **body,
        "$defs": definitions,
    }


def definitions():
    runtime_fields = {
        "path": PATH,
        "url": STRING,
        "artifact": PATH,
        "sha256": DIGEST,
        "executable": PATH,
        "role": {"enum": ["python", "node", "uv", "helper", "other"]},
        "version": STRING,
        "target": TARGET,
        "format": {"enum": ["tar", "zip"]},
        "strip": {"type": "integer", "minimum": 0, "maximum": 8},
    }
    result = {
        "v2File": obj(
            {
                "sha256": DIGEST,
                "size": {"type": "integer", "minimum": 0, "maximum": 2147483648},
            },
            ["sha256", "size"],
        ),
        "v2Command": obj(
            {
                "program": PATH,
                "args": {"type": "array", "items": {"type": "string"}},
                "env": mapping(
                    {"type": "string"}, {"pattern": "^[A-Za-z_][A-Za-z0-9_]*$"}
                ),
                "runtime": {"type": ["string", "null"]},
            },
            ["program"],
        ),
        "v2Source": obj(
            {
                "commit": {"type": ["string", "null"]},
                "dirty": {"type": "boolean"},
                "source_sha256": DIGEST,
                "locks": mapping(DIGEST),
            },
            ["commit", "dirty", "source_sha256", "locks"],
        ),
        "v2Runtime": obj(
            {k: v for k, v in runtime_fields.items() if k != "path"},
            ["sha256", "executable", "role", "target"],
        ),
        "v2RuntimeConfig": obj(
            {k: v for k, v in runtime_fields.items() if k != "artifact"},
            ["sha256", "executable", "role", "target"],
        ),
        "v2Component": obj(
            {
                "adapter": {"enum": ["payload", "python", "cargo", "legacy"]},
                "source": COMMAND,
                "path": PATH,
                "build": ARGV_LIST,
                "files": {
                    "type": "array",
                    "items": obj(
                        {
                            "source": PATH,
                            "destination": PATH,
                            "executable": {"type": "boolean"},
                        },
                        ["source", "destination"],
                    ),
                },
                "manifest": PATH,
                "binaries": STRINGS,
                "features": STRINGS,
                "dependencies": STRINGS,
                "python": {"type": "string", "pattern": "^3\\.[0-9]+(\\.[0-9]+)?$"},
                "extras": STRINGS,
                "wheels": STRINGS,
                "verification": ARGV_LIST,
                "toolchain": {
                    "type": "string",
                    "pattern": "^[0-9]+\\.[0-9]+\\.[0-9]+$",
                },
            },
            ["adapter"],
        ),
        "v2ProductConfig": obj(
            {
                "version": STRING,
                "version-from": COMMAND,
                "adapter": {"enum": ["native", "python", "hybrid", "application"]},
                "components": {**STRINGS, "minItems": 1},
                "dependencies": STRINGS,
                "commands": {**mapping(ref("v2Command"), COMMAND), "minProperties": 1},
                "verification": {**ARGV_LIST, "minItems": 1},
                "runtimes": STRINGS,
                "stateful": {"type": "boolean"},
                "targets": {"type": "array", "items": TARGET, "minItems": 1},
                "python": {"type": "string", "pattern": "^3\\.[0-9]+(\\.[0-9]+)?$"},
                "release-tag": STRING,
                "notices": STRINGS,
                "license-acceptance": PATH,
                "extras": mapping(STRINGS, COMMAND),
                "variants": mapping(
                    obj(
                        {
                            "components": STRINGS,
                            "runtimes": STRINGS,
                            "dependencies": STRINGS,
                            "commands": mapping(ref("v2Command"), COMMAND),
                            "extras": mapping(STRINGS, COMMAND),
                        }
                    ),
                    COMMAND,
                ),
            },
            ["adapter", "components", "commands", "verification"],
        ),
        "v2GroupConfig": obj(
            {
                "version": STRING,
                "products": {**STRINGS, "minItems": 1},
                "release-tag": STRING,
            },
            ["products"],
        ),
    }
    for name, keys in (
        ("v2Runtime", ("artifact", "url")),
        ("v2RuntimeConfig", ("path", "url")),
    ):
        result[name]["oneOf"] = [
            {"required": [key], "not": {"required": [other]}}
            for key, other in (keys, tuple(reversed(keys)))
        ]
    result["v2ProductFile"] = obj(
        {
            "artifact": PATH,
            "sha256": DIGEST,
            "size": {"type": "integer", "minimum": 0},
            "executable": {"type": "boolean"},
        },
        ["artifact", "sha256", "size", "executable"],
    )
    result["v2Product"] = obj(
        {
            "id": PRODUCT,
            "version": STRING,
            "adapter": {"enum": ["native", "python", "hybrid", "application"]},
            "target": TARGET,
            "baseline": BASELINE,
            "variant": {"type": ["string", "null"]},
            "dependencies": STRINGS,
            "runtimes": STRINGS,
            "stateful": {"type": "boolean"},
            "commands": {**mapping(ref("v2Command"), COMMAND), "minProperties": 1},
            "verification": {**ARGV_LIST, "minItems": 1},
            "python": {"type": ["string", "null"]},
            "files": {**mapping(ref("v2ProductFile"), PATH), "minProperties": 1},
            "sources": mapping(ref("v2Source")),
            "runtime_records": mapping(ref("v2Runtime")),
            "release": DIGEST,
            "notices": STRINGS,
            "extras": mapping(STRINGS, COMMAND),
            "license_acceptance": obj(
                {"path": PATH, "sha256": DIGEST}, ["path", "sha256"]
            ),
        },
        [
            "id",
            "version",
            "adapter",
            "target",
            "baseline",
            "variant",
            "dependencies",
            "runtimes",
            "stateful",
            "commands",
            "verification",
            "python",
            "files",
            "sources",
            "runtime_records",
            "release",
            "extras",
            "notices",
        ],
    )
    result["v2Group"] = obj(
        {
            "version": STRING,
            "products": {**STRINGS, "minItems": 1},
            "releases": mapping(DIGEST, PRODUCT),
        },
        ["version", "products", "releases"],
    )
    result["v2Entry"] = obj(
        {
            "product": ref("v2Product"),
            "payload": PATH,
            "runtimes": mapping(STRING),
            "python": {"type": ["string", "null"]},
            "explicit": {"type": "boolean"},
            "previous": {"oneOf": [{"type": "null"}, ref("v2Entry")]},
            "dependency_releases": mapping(DIGEST, PRODUCT),
            "origin": {"enum": ["source", "artifact"]},
            "python_home": {"type": "string"},
            "python_library": {"type": "string"},
            "site_packages": {"type": "string"},
        },
        [
            "product",
            "payload",
            "runtimes",
            "python",
            "explicit",
            "previous",
            "dependency_releases",
            "python_home",
            "python_library",
            "site_packages",
            "origin",
        ],
    )
    return result


def outputs():
    defs = definitions()
    runtime_target = dict(defs["v2RuntimeConfig"])
    runtime_target["properties"] = {
        k: v
        for k, v in runtime_target["properties"].items()
        if k not in {"role", "target"}
    }
    runtime_target["required"] = ["sha256", "executable"]
    defs["v2RuntimeMatrix"] = obj(
        {
            "role": {"enum": ["python", "node", "uv", "helper", "other"]},
            "version": STRING,
            "targets": {**mapping(runtime_target, TARGET), "minProperties": 1},
        },
        ["role", "targets"],
    )
    config = obj(
        {
            "schema": {"const": 2},
            "profile": {"const": "workspace"},
            "workspace": obj(
                {
                    "name": PRODUCT,
                    "version": STRING,
                    "default-product": PRODUCT,
                    "targets": {
                        "type": "array",
                        "items": TARGET,
                        "minItems": 1,
                        "uniqueItems": True,
                    },
                    "release-tag": STRING,
                    "baselines": mapping(BASELINE, TARGET),
                },
                ["name", "version", "default-product", "targets"],
            ),
            "sources": mapping(obj({"path": STRING}, ["path"]), COMMAND),
            "commands": obj({k: ARGV_LIST for k in ("develop", "check", "test")}),
            "components": mapping(ref("v2Component"), COMMAND),
            "products": {
                **mapping(ref("v2ProductConfig"), PRODUCT),
                "minProperties": 1,
            },
            "groups": mapping(ref("v2GroupConfig"), PRODUCT),
            "runtimes": mapping(
                {"oneOf": [ref("v2RuntimeConfig"), ref("v2RuntimeMatrix")]}, COMMAND
            ),
        },
        ["schema", "profile", "workspace", "components", "products"],
    )
    release = obj(
        {
            "schema": {"const": 2},
            "helper_revision": {"const": 2},
            "component": {
                "oneOf": [
                    {"type": "null"},
                    obj(
                        {
                            "id": COMMAND,
                            "adapter": {
                                "enum": ["payload", "python", "cargo", "legacy"]
                            },
                            "python": {"type": ["string", "null"]},
                            "verification": ARGV_LIST,
                        },
                        ["id", "adapter", "python", "verification"],
                    ),
                ]
            },
            "kind": {"enum": ["component", "product", "group"]},
            "name": PRODUCT,
            "version": STRING,
            "selection": PRODUCT,
            "variant": {"type": ["string", "null"]},
            "target": TARGET,
            "baseline": BASELINE,
            "sources": mapping(ref("v2Source")),
            "products": mapping(ref("v2Product"), PRODUCT),
            "groups": mapping(ref("v2Group"), PRODUCT),
            "runtimes": mapping(ref("v2Runtime"), COMMAND),
            "files": {**mapping(ref("v2File"), PATH), "minProperties": 1},
            "helpers": mapping(
                obj(
                    {
                        "artifact": PATH,
                        "sha256": DIGEST,
                        "size": {"type": "integer", "minimum": 0},
                    },
                    ["artifact", "sha256", "size"],
                )
            ),
            "builds": mapping(mapping({"type": "string"}), COMMAND),
        },
        [
            "schema",
            "helper_revision",
            "kind",
            "name",
            "version",
            "selection",
            "variant",
            "target",
            "baseline",
            "sources",
            "products",
            "groups",
            "runtimes",
            "files",
            "helpers",
            "component",
            "builds",
        ],
    )
    receipt = obj(
        {
            "schema": {"const": 2},
            "origin": {"const": "artifact-helper"},
            "scope": {"enum": ["shared", "private"]},
            "owner": PRODUCT,
            "products": mapping(ref("v2Entry"), PRODUCT),
            "groups": mapping(ref("v2Group"), PRODUCT),
            "requests": mapping(
                obj(
                    {
                        "input": DIGEST,
                        "status": {"enum": ["running", "interrupted", "complete"]},
                        "completed": STRINGS,
                    },
                    ["input", "status", "completed"],
                )
            ),
            "shims": mapping(
                {
                    "oneOf": [
                        {"type": "string"},
                        obj(
                            {
                                "file": PATH,
                                "sha256": DIGEST,
                                "size": {"type": "integer", "minimum": 0},
                            },
                            ["file", "sha256", "size"],
                        ),
                    ]
                },
                COMMAND,
            ),
        },
        [
            "schema",
            "origin",
            "scope",
            "owner",
            "products",
            "groups",
            "requests",
            "shims",
        ],
    )
    descriptor = obj(
        {
            "schema": {"const": 2},
            "kind": {"const": "release-export"},
            "name": PRODUCT,
            "version": STRING,
            "selection": PRODUCT,
            "target": TARGET,
            "manifest": PATH,
            "manifest_sha256": DIGEST,
            "products": mapping(
                obj(
                    {
                        "version": STRING,
                        "release": DIGEST,
                        "extras": mapping(STRINGS, COMMAND),
                        "commands": STRINGS,
                    },
                    ["version", "release", "commands"],
                ),
                PRODUCT,
            ),
            "groups": mapping(ref("v2Group"), PRODUCT),
            "publication": {"const": "not-published"},
            "verification": obj(
                {
                    "static": {"const": True},
                    "runtime": {"type": "boolean"},
                    "report": {"type": ["string", "null"]},
                },
                ["static", "runtime", "report"],
            ),
        },
        [
            "schema",
            "kind",
            "name",
            "version",
            "selection",
            "target",
            "manifest",
            "manifest_sha256",
            "products",
            "groups",
            "publication",
            "verification",
        ],
    )
    event = obj(
        {
            "schema": {"const": 2},
            "request": STRING,
            "stage": {
                "enum": [
                    "checking",
                    "preparing-runtime",
                    "downloading",
                    "installing",
                    "verified",
                    "reused",
                    "activated",
                    "interrupted",
                    "complete",
                    "result",
                ]
            },
            "product": {"type": ["string", "null"]},
            "version": STRING,
            "runtime": STRING,
            "completed": STRINGS,
            "bytes": {"type": "integer", "minimum": 0},
            "total": {"type": ["integer", "null"], "minimum": 0},
            "result": {"type": "object"},
        },
        ["schema", "stage"],
    )
    report = obj(
        {
            "schema": {"const": 2},
            "kind": {"const": "installation-verification"},
            "verified": {"const": True},
            "installation_tested": {"type": "boolean"},
            "manifest_sha256": DIGEST,
            "target": TARGET,
            "helper_python": STRING,
            "checks": mapping({"type": "integer", "minimum": 0}, PRODUCT),
            "component": COMMAND,
            "global_commands_created": {"const": False},
        },
        [
            "schema",
            "kind",
            "verified",
            "installation_tested",
            "manifest_sha256",
            "target",
            "helper_python",
            "checks",
        ],
    )
    result = {
        "installation-v2.schema.json": document(
            "Workspace configuration, schema 2", config, defs
        ),
        "product-release.schema.json": document(
            "Portable product release, schema 2", release, defs
        ),
        "product-receipt.schema.json": document(
            "Product store receipt, schema 2", receipt, defs
        ),
        "product-descriptor.schema.json": document(
            "Publication handoff, schema 2", descriptor, defs
        ),
        "operation-event.schema.json": document(
            "Installation progress event, schema 2", event, {}
        ),
        "verification-report.schema.json": document(
            "Executed/static verification evidence, schema 2", report, {}
        ),
    }
    current = json.loads((ROOT / "schemas/installation.schema.json").read_text())
    legacy = (
        current["oneOf"][0]
        if "oneOf" in current
        else {
            k: v for k, v in current.items() if k not in {"$schema", "title", "$defs"}
        }
    )
    legacy_defs = {k: v for k, v in current["$defs"].items() if not k.startswith("v2")}
    result["installation.schema.json"] = document(
        "Installation configuration, schemas 1 and 2",
        {"oneOf": [legacy, config]},
        {**legacy_defs, **defs},
    )
    return result


def main(write=False):
    for name, schema in outputs().items():
        path = ROOT / "schemas" / name
        expected = json.dumps(deepcopy(schema), indent=2, sort_keys=True) + "\n"
        if write:
            path.write_text(expected)
        elif not path.is_file() or path.read_text() != expected:
            raise ValueError("Generated schema differs: " + name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    main(parser.parse_args().write)
