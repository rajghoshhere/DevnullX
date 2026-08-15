from uuid import uuid4


async def _create_tenant(client, name: str = "Acme Logistics") -> dict:
    response = await client.post("/v1/tenants", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()


def _headers(tenant_id: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant_id}


async def test_onboarding_happy_path_reaches_verified(client) -> None:
    tenant = await _create_tenant(client)
    headers = _headers(tenant["id"])

    owner = await client.post("/v1/owners", json={"name": "Ravi"}, headers=headers)
    assert owner.status_code == 201
    fetched_owner = await client.get(f"/v1/owners/{owner.json()['id']}", headers=headers)
    assert fetched_owner.status_code == 200
    assert fetched_owner.json()["name"] == "Ravi"

    fleet = await client.post("/v1/fleets", json={"name": "North Fleet"}, headers=headers)
    assert fleet.status_code == 201

    vehicle = await client.post(
        "/v1/vehicles",
        json={
            "fleet_id": fleet.json()["id"],
            "registration_number": "MH12AB1234",
            "gvw_kg": 47500,
        },
        headers=headers,
    )
    assert vehicle.status_code == 201
    assert vehicle.json()["vehicle_status"] == "DRAFT"

    verified = await client.post(
        f"/v1/vehicles/{vehicle.json()['id']}/verify",
        json={},
        headers=headers,
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["vehicle_status"] == "VERIFIED"

    fetched = await client.get(f"/v1/vehicles/{vehicle.json()['id']}", headers=headers)
    assert fetched.json()["vehicle_status"] == "VERIFIED"
    assert fetched.json()["fuel_type"] == "DIESEL"
    assert fetched.json()["body_type"] == "OPEN"
    assert fetched.json()["gvw_kg"] == 47500


async def test_verify_captures_registration_in_request_body(client) -> None:
    tenant = await _create_tenant(client, "Capture Co")
    headers = _headers(tenant["id"])
    fleet = await client.post("/v1/fleets", json={"name": "Fleet"}, headers=headers)
    vehicle = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"]},
        headers=headers,
    )
    verified = await client.post(
        f"/v1/vehicles/{vehicle.json()['id']}/verify",
        json={"registration_number": "TN09AB4321"},
        headers=headers,
    )
    assert verified.status_code == 200
    assert verified.json()["registration_number"] == "TN09AB4321"
    assert verified.json()["vehicle_status"] == "VERIFIED"
    assert verified.json()["fuel_type"] == "DIESEL"


async def test_batch_verify_by_vehicle_ids(client) -> None:
    tenant = await _create_tenant(client, "Batch Co")
    headers = _headers(tenant["id"])
    fleet = await client.post("/v1/fleets", json={"name": "Fleet"}, headers=headers)
    first = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"], "registration_number": "MH12AB1111"},
        headers=headers,
    )
    second = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"], "registration_number": "MH12FAIL22"},
        headers=headers,
    )
    missing = str(uuid4())
    response = await client.post(
        "/v1/vehicles/verify-batch",
        json={"vehicle_ids": [first.json()["id"], second.json()["id"], missing]},
        headers=headers,
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["requested"] == 3
    assert body["verified"] == 1
    assert body["failed"] == 2
    by_id = {item["vehicle_id"]: item for item in body["results"]}
    assert by_id[first.json()["id"]]["ok"] is True
    assert by_id[first.json()["id"]]["vehicle"]["fuel_type"] == "DIESEL"
    assert by_id[second.json()["id"]]["ok"] is False
    assert by_id[second.json()["id"]]["vehicle"]["vehicle_status"] == "MANUAL_REVIEW"
    assert by_id[missing]["ok"] is False


async def test_verification_failure_goes_to_manual_review(client) -> None:
    tenant = await _create_tenant(client, "Fail Co")
    headers = _headers(tenant["id"])
    fleet = await client.post("/v1/fleets", json={"name": "Fleet"}, headers=headers)
    vehicle = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"], "registration_number": "KA01FAIL99"},
        headers=headers,
    )
    verified = await client.post(
        f"/v1/vehicles/{vehicle.json()['id']}/verify",
        json={},
        headers=headers,
    )
    assert verified.status_code == 200
    assert verified.json()["vehicle_status"] == "MANUAL_REVIEW"


async def test_duplicate_registration_conflict(client) -> None:
    tenant = await _create_tenant(client, "Dup Co")
    headers = _headers(tenant["id"])
    fleet = await client.post("/v1/fleets", json={"name": "Fleet"}, headers=headers)
    first = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"], "registration_number": "MH12AB9999"},
        headers=headers,
    )
    assert first.status_code == 201
    duplicate = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"], "registration_number": "mh12ab9999"},
        headers=headers,
    )
    assert duplicate.status_code == 409


async def test_invalid_state_conflict_on_second_verify(client) -> None:
    tenant = await _create_tenant(client, "State Co")
    headers = _headers(tenant["id"])
    fleet = await client.post("/v1/fleets", json={"name": "Fleet"}, headers=headers)
    vehicle = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"], "registration_number": "DL01AB1001"},
        headers=headers,
    )
    first = await client.post(
        f"/v1/vehicles/{vehicle.json()['id']}/verify",
        json={},
        headers=headers,
    )
    assert first.status_code == 200
    second = await client.post(
        f"/v1/vehicles/{vehicle.json()['id']}/verify",
        json={},
        headers=headers,
    )
    assert second.status_code == 409


async def test_missing_tenant_header(client) -> None:
    response = await client.post("/v1/owners", json={"name": "Ravi"})
    assert response.status_code == 422


async def test_vehicle_not_found_for_other_tenant(client) -> None:
    tenant = await _create_tenant(client, "A")
    other = await _create_tenant(client, "B")
    headers = _headers(tenant["id"])
    fleet = await client.post("/v1/fleets", json={"name": "Fleet"}, headers=headers)
    vehicle = await client.post(
        "/v1/vehicles",
        json={"fleet_id": fleet.json()["id"]},
        headers=headers,
    )
    response = await client.get(
        f"/v1/vehicles/{vehicle.json()['id']}",
        headers=_headers(other["id"]),
    )
    assert response.status_code == 404


async def test_unknown_fleet_is_not_found(client) -> None:
    tenant = await _create_tenant(client, "Missing Fleet")
    response = await client.post(
        "/v1/vehicles",
        json={"fleet_id": str(uuid4())},
        headers=_headers(tenant["id"]),
    )
    assert response.status_code == 404
