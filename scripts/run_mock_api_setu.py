"""Run a local mock API Setu VAHAN endpoint for populate/review testing."""

from __future__ import annotations

import os

import uvicorn


def main() -> None:
    host = os.environ.get("MOCK_API_SETU_HOST", "0.0.0.0")
    port = int(os.environ.get("MOCK_API_SETU_PORT", "8099"))
    uvicorn.run(
        "adapters.vehicle_providers.mock_api_setu:app",
        host=host,
        port=port,
        reload=False,
    )


if __name__ == "__main__":
    main()
