"""Wraps the Lambda Cloud REST API to manage GPU instance lifecycle for the diarization pipeline."""

import logging
import os
import shlex
import time
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

LAMBDA_API_BASE = "https://cloud.lambda.ai/api/v1"


def _headers() -> dict[str, str]:
    api_key = os.environ["LAMBDA_API_KEY"]
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def _load_cloud_init_script(episode_ids: list[str]) -> str:
    """Read run_pipeline.sh and inject environment variables as a cloud-init script."""
    script_path = (
        Path(__file__).resolve().parent.parent / "diarization" / "run_pipeline.sh"
    )
    template = script_path.read_text()

    # Strip the shebang from the template since we prepend our own
    if template.startswith("#!/"):
        template = template.split("\n", 1)[1]

    env_vars = {
        "SUPABASE_URL": os.environ["SUPABASE_URL"],
        "SUPABASE_SERVICE_ROLE_KEY": os.environ["SUPABASE_SERVICE_ROLE_KEY"],
        "OPENAI_API_KEY": os.environ["OPENAI_API_KEY"],
        "HUGGING_FACE_TOKEN": os.environ["HUGGING_FACE_TOKEN"],
        "LAMBDA_API_KEY": os.environ["LAMBDA_API_KEY"],
        "EPISODE_IDS": ",".join(episode_ids),
        "GITHUB_DEPLOY_TOKEN": os.environ["GITHUB_DEPLOY_TOKEN"],
    }

    # Use shlex.quote to safely handle special characters in secret values
    export_block = "\n".join(
        f"export {key}={shlex.quote(value)}" for key, value in env_vars.items()
    )

    cloud_init = f"#!/bin/bash\n{export_block}\n{template}"
    return cloud_init


def get_available_region(
    preferred_type: str = "gpu_1x_a100",
    fallback_type: str = "gpu_1x_a10",
) -> tuple[str, str]:
    """Check Lambda API for GPU capacity and return (region_name, instance_type_name).

    Tries the preferred instance type first across all regions, then falls back
    to the fallback type. Raises RuntimeError if neither type has capacity.
    """
    response = requests.get(
        f"{LAMBDA_API_BASE}/instance-types",
        headers=_headers(),
        timeout=30,
    )
    response.raise_for_status()
    data = response.json().get("data", {})

    for instance_type, type_name in [
        (preferred_type, preferred_type),
        (fallback_type, fallback_type),
    ]:
        type_info = data.get(instance_type)
        if type_info is None:
            continue
        regions = type_info.get("regions_with_capacity_available", [])
        if regions:
            region_name = regions[0]["name"]
            if instance_type == fallback_type:
                logger.warning(
                    "Preferred type %s unavailable. Falling back to %s in %s.",
                    preferred_type,
                    fallback_type,
                    region_name,
                )
            else:
                logger.info("Found capacity for %s in %s.", instance_type, region_name)
            return (region_name, type_name)

    raise RuntimeError(
        f"No capacity available for either {preferred_type} or {fallback_type} "
        "in any region."
    )


def launch_instance(
    region_name: str,
    instance_type_name: str,
    episode_ids: list[str],
    instance_name: str = "book-of-andy-pipeline",
) -> str:
    """Launch a Lambda GPU instance with the cloud-init pipeline script.

    Returns the launched instance ID.
    """
    ssh_key_name = os.environ["LAMBDA_SSH_KEY_NAME"]
    user_data = _load_cloud_init_script(episode_ids)

    payload = {
        "region_name": region_name,
        "instance_type_name": instance_type_name,
        "ssh_key_names": [ssh_key_name],
        "name": instance_name,
        "user_data": user_data,
    }

    response = requests.post(
        f"{LAMBDA_API_BASE}/instance-operations/launch",
        headers=_headers(),
        json=payload,
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    instance_ids = data.get("instance_ids", [])
    if not instance_ids:
        raise RuntimeError("Launch succeeded but no instance ID was returned.")

    instance_id = instance_ids[0]
    logger.info(
        "Launched instance %s (type=%s, region=%s).",
        instance_id,
        instance_type_name,
        region_name,
    )
    return instance_id


def poll_until_active(
    instance_id: str,
    timeout: int = 300,
    interval: int = 10,
) -> dict:
    """Poll the Lambda API until the instance reaches 'active' status.

    Returns the instance object. Raises TimeoutError if the instance does not
    become active within the timeout window.
    """
    start = time.monotonic()

    while True:
        elapsed = time.monotonic() - start
        if elapsed >= timeout:
            raise TimeoutError(
                f"Instance {instance_id} did not become active within "
                f"{timeout} seconds."
            )

        response = requests.get(
            f"{LAMBDA_API_BASE}/instances/{instance_id}",
            headers=_headers(),
            timeout=30,
        )
        response.raise_for_status()
        instance = response.json().get("data", {})
        status = instance.get("status")

        logger.info(
            "Instance %s status: %s (%.0fs elapsed).",
            instance_id,
            status,
            elapsed,
        )

        if status == "active":
            return instance

        time.sleep(interval)


def terminate_instance(instance_id: str) -> None:
    """Terminate a Lambda GPU instance by ID."""
    payload = {"instance_ids": [instance_id]}

    try:
        response = requests.post(
            f"{LAMBDA_API_BASE}/instance-operations/terminate",
            headers=_headers(),
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Successfully terminated instance %s.", instance_id)
    except requests.RequestException:
        logger.exception("Failed to terminate instance %s.", instance_id)
