"""Shared semantic-encoder contract for Odyssey retrieval paths."""

from langchain_community.embeddings.huggingface import HuggingFaceEmbeddings


# Keep the public-code behavior explicit so dependency upgrades cannot silently
# change the vector scale or batching used by skill and planner retrieval.
ENCODER_ENCODE_KWARGS = {
    "batch_size": 32,
    "normalize_embeddings": False,
    "precision": "float32",
}

SKILL_RETRIEVAL_PROFILES = {
    "top5": 5,
    "top10": 10,
}
DEFAULT_SKILL_RETRIEVAL_PROFILE = "top5"
RETRIEVAL_DISTANCE_METRIC = "l2"


def build_retrieval_embeddings(
    model_name: str,
    *,
    device: str | None = None,
    local_files_only: bool = False,
) -> HuggingFaceEmbeddings:
    if not model_name:
        raise ValueError("semantic encoder model path or model ID is required")
    model_kwargs = {}
    if device is not None:
        model_kwargs["device"] = device
    if local_files_only:
        model_kwargs["local_files_only"] = True
    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs=model_kwargs,
        encode_kwargs=dict(ENCODER_ENCODE_KWARGS),
        show_progress=False,
    )
