#!/usr/bin/env python3
"""Verify Odyssey top-5/top-10 retrieval across Chroma persistence reload."""

from __future__ import annotations

import argparse
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = (
    REPO_ROOT / "research" / "manifest" / "odyssey_semantic_encoder.json"
)
DEFAULT_SKILLS = (
    REPO_ROOT / "Odyssey" / "skill_library" / "skill" / "skills.json"
)
COLLECTION_NAME = "odyssey_semantic_retrieval_fixture"
KNOWN_QUERIES = [
    {
        "query": "Craft a wooden pickaxe.",
        "expected_skill": "craftWoodenPickaxe",
    },
    {
        "query": "Mine diamond ore using an iron pickaxe.",
        "expected_skill": "mineDiamond",
    },
    {
        "query": "Breed two cows using wheat.",
        "expected_skill": "breedCow",
    },
    {
        "query": "밀을 사용해서 소 두 마리를 번식시킨다.",
        "expected_skill": "breedCow",
    },
]


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def load_embedding_module():
    source_path = REPO_ROOT / "Odyssey" / "odyssey" / "retrieval_embedding.py"
    spec = importlib.util.spec_from_file_location(
        "odyssey_retrieval_embedding_fixture", source_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load retrieval_embedding.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def retrieve(vector_store, query: str, k: int) -> list[dict]:
    results = vector_store.similarity_search_with_score(query, k=k)
    return [
        {
            "rank": rank,
            "skill": document.metadata["name"],
            "score": float(score),
        }
        for rank, (document, score) in enumerate(results, start=1)
    ]


def query_profiles(vector_store, profile_sizes: dict[str, int]) -> dict:
    profiles = {}
    for profile_name, k in profile_sizes.items():
        queries = []
        for fixture in KNOWN_QUERIES:
            candidates = retrieve(vector_store, fixture["query"], k)
            expected_rank = next(
                (
                    candidate["rank"]
                    for candidate in candidates
                    if candidate["skill"] == fixture["expected_skill"]
                ),
                None,
            )
            queries.append(
                {
                    **fixture,
                    "expected_rank": expected_rank,
                    "passed": expected_rank is not None,
                    "candidates": candidates,
                }
            )
        profiles[profile_name] = {
            "k": k,
            "known_query_recall_at_k": sum(
                item["passed"] for item in queries
            )
            / len(queries),
            "queries": queries,
        }
    return profiles


def worker(args) -> int:
    manifest = read_json(args.manifest.resolve())
    skills = read_json(args.skills.resolve())
    embedding_module = load_embedding_module()
    profile_sizes = dict(embedding_module.SKILL_RETRIEVAL_PROFILES)
    model_dir = REPO_ROOT / manifest["checkpoint"]["local_path"]
    embeddings = embedding_module.build_retrieval_embeddings(
        str(model_dir), device=args.device, local_files_only=True
    )

    import chromadb
    from chromadb.config import Settings
    from langchain_community.vectorstores import Chroma

    settings = Settings(
        chroma_db_impl="duckdb+parquet",
        persist_directory=str(args.persist_directory),
        anonymized_telemetry=False,
    )
    vector_store = Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(args.persist_directory),
        client_settings=settings,
        collection_metadata={
            "hnsw:space": embedding_module.RETRIEVAL_DISTANCE_METRIC
        },
    )

    if args.worker == "build":
        names = sorted(skills)
        vector_store.add_texts(
            texts=[skills[name]["description"] for name in names],
            ids=names,
            metadatas=[{"name": name} for name in names],
        )
        if chromadb.__version__.startswith("0.3."):
            vector_store._client.persist()

    count = vector_store._collection.count()
    result = {
        "phase": args.worker,
        "index_count": count,
        "profiles": query_profiles(vector_store, profile_sizes),
    }
    print(json.dumps(result, ensure_ascii=False))
    return 0 if count == len(skills) == 183 else 1


def run_worker(args, phase: str, persist_directory: Path) -> tuple[dict, list[str]]:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        phase,
        "--manifest",
        str(args.manifest.resolve()),
        "--skills",
        str(args.skills.resolve()),
        "--persist-directory",
        str(persist_directory),
        "--device",
        args.device,
    ]
    completed = subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )
    warnings = [
        line.strip()
        for line in completed.stderr.splitlines()
        if "Warning" in line or "telemetry" in line.lower()
    ]
    return json.loads(completed.stdout), warnings


def compare_profiles(build: dict, reload: dict, tolerance: float) -> dict:
    comparisons = {}
    for profile_name, build_profile in build["profiles"].items():
        reload_profile = reload["profiles"][profile_name]
        query_checks = []
        for build_query, reload_query in zip(
            build_profile["queries"], reload_profile["queries"], strict=True
        ):
            build_names = [
                item["skill"] for item in build_query["candidates"]
            ]
            reload_names = [
                item["skill"] for item in reload_query["candidates"]
            ]
            score_deltas = [
                abs(before["score"] - after["score"])
                for before, after in zip(
                    build_query["candidates"],
                    reload_query["candidates"],
                    strict=True,
                )
            ]
            max_score_delta = max(score_deltas, default=0.0)
            query_checks.append(
                {
                    "query": build_query["query"],
                    "candidate_order_equal": build_names == reload_names,
                    "max_score_delta": max_score_delta,
                    "scores_equal_within_tolerance": max_score_delta
                    <= tolerance,
                }
            )
        comparisons[profile_name] = {
            "k": build_profile["k"],
            "queries": query_checks,
            "passed": all(
                item["candidate_order_equal"]
                and item["scores_equal_within_tolerance"]
                for item in query_checks
            ),
        }
    return comparisons


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--skills", type=Path, default=DEFAULT_SKILLS)
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--score-tolerance", type=float, default=0.000001)
    parser.add_argument("--worker", choices=["build", "reload"])
    parser.add_argument("--persist-directory", type=Path)
    args = parser.parse_args()

    if args.worker:
        if args.persist_directory is None:
            parser.error("--persist-directory is required for worker mode")
        return worker(args)

    manifest = read_json(args.manifest.resolve())
    embedding_module = load_embedding_module()
    profile_sizes = dict(embedding_module.SKILL_RETRIEVAL_PROFILES)
    default_profile = embedding_module.DEFAULT_SKILL_RETRIEVAL_PROFILE

    with tempfile.TemporaryDirectory(
        prefix="odyssey-retrieval-fixture-"
    ) as temp_dir:
        persist_directory = Path(temp_dir) / "index"
        build, build_warnings = run_worker(
            args, "build", persist_directory
        )
        reload, reload_warnings = run_worker(
            args, "reload", persist_directory
        )

    comparisons = compare_profiles(
        build, reload, args.score_tolerance
    )
    prefix_checks = []
    for phase in (build, reload):
        for top5_query, top10_query in zip(
            phase["profiles"]["top5"]["queries"],
            phase["profiles"]["top10"]["queries"],
            strict=True,
        ):
            prefix_checks.append(
                {
                    "phase": phase["phase"],
                    "query": top5_query["query"],
                    "top5_is_top10_prefix": [
                        item["skill"] for item in top5_query["candidates"]
                    ]
                    == [
                        item["skill"]
                        for item in top10_query["candidates"][:5]
                    ],
                }
            )

    profile_contract = {
        "default_profile": default_profile,
        "profile_sizes": profile_sizes,
        "default_is_top5": default_profile == "top5"
        and profile_sizes.get("top5") == 5,
        "top10_is_separate": profile_sizes.get("top10") == 10,
    }
    passed = (
        build["index_count"] == reload["index_count"] == 183
        and profile_contract["default_is_top5"]
        and profile_contract["top10_is_separate"]
        and all(item["passed"] for item in comparisons.values())
        and all(item["top5_is_top10_prefix"] for item in prefix_checks)
        and all(
            profile["known_query_recall_at_k"] == 1.0
            for phase in (build, reload)
            for profile in phase["profiles"].values()
        )
    )
    output = {
        "profile": "odyssey-semantic-retrieval-persist-reload",
        "encoder_revision": manifest["checkpoint"]["revision"],
        "corpus": str(args.skills.resolve().relative_to(REPO_ROOT)),
        "corpus_count": 183,
        "distance_metric": embedding_module.RETRIEVAL_DISTANCE_METRIC,
        "canonical_device": args.device,
        "score_tolerance": args.score_tolerance,
        "profile_contract": profile_contract,
        "build": build,
        "reload": reload,
        "reload_comparisons": comparisons,
        "profile_prefix_checks": prefix_checks,
        "warnings": sorted(set(build_warnings + reload_warnings)),
        "passed": passed,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    print(
        f"{'PASS' if passed else 'FAIL'}: "
        "Odyssey semantic retrieval profiles and reload fixture"
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
