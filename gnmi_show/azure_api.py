#!/usr/bin/env python3
"""
Azure REST API client for retrieving gNMI data from SONiC switches.

Uses the Azure CLI (az rest) via subprocess to make API calls.
Requires the user to be authenticated via `az login`.

Platform: Linux and macOS only (no Windows support).
"""

import json
import os
import re
import subprocess
import tempfile
import time
from dataclasses import dataclass, field


class AzureApiError(Exception):
    """Raised when an Azure API operation fails."""

    pass


@dataclass
class AzureConfig:
    """Configuration for Azure API calls."""

    subscription_id: str
    resource_group: str
    resource_name: str
    switch: str
    api_version: str = field(default="2025-07-01-preview")

    @property
    def base_url(self) -> str:
        return (
            f"https://management.azure.com/subscriptions/{self.subscription_id}"
            f"/resourceGroups/{self.resource_group}"
            f"/providers/Microsoft.SupercomputerInfrastructure"
            f"/supercomputers/{self.resource_name}"
            f"/switches/{self.switch}"
        )

    @property
    def retrieve_data_url(self) -> str:
        return f"{self.base_url}/retrieveData?api-version={self.api_version}"


def _run_az_command(args: list) -> subprocess.CompletedProcess:
    """Run an az CLI command and return the result."""
    try:
        result = subprocess.run(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        raise AzureApiError(
            "Azure CLI (az) not found on PATH. "
            "Install it: https://aka.ms/install-azure-cli"
        )

    if result.returncode != 0:
        stderr = result.stderr.strip()
        if "AADSTS" in stderr or "401" in stderr or "403" in stderr:
            raise AzureApiError(
                "Azure authentication failed. Run 'az login' first."
            )
        raise AzureApiError(f"Azure CLI command failed (exit {result.returncode}): {stderr}")

    return result


def _post_retrieve_data(config: AzureConfig, gnmi_path: str) -> str:
    """POST to the retrieveData endpoint and return the verbose stderr output."""
    body = {"paths": [gnmi_path]}
    tmp_fd, tmp_path = tempfile.mkstemp(suffix=".json")
    try:
        with os.fdopen(tmp_fd, "w") as f:
            json.dump(body, f)
        result = _run_az_command([
            "az", "rest",
            "--method", "post",
            "--url", config.retrieve_data_url,
            "--body", f"@{tmp_path}",
            "--verbose",
        ])
    finally:
        os.unlink(tmp_path)
    return result.stderr


def _extract_async_url(verbose_output: str) -> str:
    """Extract the Azure-AsyncOperation URL from verbose az output."""
    pattern = r"['\"]?Azure-AsyncOperation['\"]?\s*[:=]\s*['\"]([^'\"]+)['\"]"
    match = re.search(pattern, verbose_output, re.IGNORECASE)
    if not match:
        raise AzureApiError(
            "Could not extract async operation URL from Azure response. "
            "The API may have changed or the request may have failed.\n"
            f"Verbose output:\n{verbose_output[:500]}"
        )
    return match.group(1)


def _poll_async_operation(
    url: str,
    initial_delay: float = 3.0,
    max_retries: int = 10,
    retry_delay: float = 1.0,
) -> dict:
    """Poll the async operation URL until it completes."""
    time.sleep(initial_delay)

    for attempt in range(max_retries):
        result = _run_az_command([
            "az", "rest",
            "--method", "get",
            "--url", url,
            "--resource", "https://management.azure.com/",
        ])

        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise AzureApiError(f"Failed to parse poll response as JSON: {e}")

        status = response.get("status", "").lower()

        if status == "succeeded":
            return response
        elif status in ("failed", "canceled", "cancelled"):
            error_msg = response.get("error", {}).get("message", "Unknown error")
            raise AzureApiError(f"Azure operation {status}: {error_msg}")

        if attempt < max_retries - 1:
            time.sleep(retry_delay)

    raise AzureApiError(
        f"Azure async operation timed out after {max_retries} retries "
        f"({initial_delay + max_retries * retry_delay:.0f}s total)."
    )


def _extract_gnmi_data(response: dict) -> dict:
    """Extract gNMI data from the async operation response."""
    try:
        value_str = response["properties"]["value"][0]["value"]
    except (KeyError, IndexError, TypeError) as e:
        raise AzureApiError(
            f"Unexpected response structure. Could not find data at "
            f"properties.value[0].value: {e}"
        )

    try:
        return json.loads(value_str)
    except json.JSONDecodeError as e:
        raise AzureApiError(f"Failed to parse gNMI data as JSON: {e}")


def _set_subscription(subscription_id: str) -> None:
    """Set the active Azure subscription."""
    _run_az_command(["az", "account", "set", "--subscription", subscription_id])


def retrieve_data(config: AzureConfig, gnmi_path: str) -> dict:
    """Retrieve gNMI data from an Azure-managed SONiC switch.

    Automatically sets the Azure subscription before making API calls.
    Requires the user to have run 'az login' beforehand.

    Args:
        config: Azure resource configuration.
        gnmi_path: The gNMI path to query (e.g., "SHOW/interfaces/status").

    Returns:
        Parsed JSON data from the switch.

    Raises:
        AzureApiError: If any step of the API interaction fails.
    """
    _set_subscription(config.subscription_id)
    verbose_output = _post_retrieve_data(config, gnmi_path)
    async_url = _extract_async_url(verbose_output)
    response = _poll_async_operation(async_url)
    return _extract_gnmi_data(response)
