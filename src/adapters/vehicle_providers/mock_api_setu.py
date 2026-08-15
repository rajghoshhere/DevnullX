from __future__ import annotations

import os
import re
from xml.sax.saxutils import escape

from fastapi import FastAPI, Request, Response

API_KEY_HEADER = "x-apisetu-apikey"
CLIENT_ID_HEADER = "x-apisetu-clientid"
_REG_PATTERN = re.compile(r"<rc_regn_no>\s*([^<]+)\s*</rc_regn_no>", re.IGNORECASE)

app = FastAPI(title="Mock API Setu VAHAN", version="0.1.0")


def expected_api_key() -> str:
    return os.environ.get("MOCK_API_SETU_API_KEY", "test-api-key")


def rc_xml(registration_number: str) -> str:
    reg = escape(registration_number.strip().upper())
    return f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<VehicleDetails>
  <stautsMessage>OK</stautsMessage>
  <rc_regn_no>{reg}</rc_regn_no>
  <rc_regn_dt>15-Mar-2022</rc_regn_dt>
  <rc_owner_sr>1</rc_owner_sr>
  <rc_owner_name>P*I*A S*A*</rc_owner_name>
  <rc_f_name>R*M*S* S*A*</rc_f_name>
  <rc_present_address>P*N* C*T*, M*H*R*S*T*A</rc_present_address>
  <rc_permanent_address>P*N* C*T*, M*H*R*S*T*A</rc_permanent_address>
  <rc_mobile_no>9*8*7*6*5*4*</rc_mobile_no>
  <rc_vch_catg>HGV</rc_vch_catg>
  <rc_vh_class_desc>Goods Carrier(HGV)</rc_vh_class_desc>
  <rc_chasi_no>**T448030********</rc_chasi_no>
  <rc_eng_no>****4019001</rc_eng_no>
  <rc_maker_desc>TATA MOTORS LTD</rc_maker_desc>
  <rc_maker_model>SIGNA 4825.T</rc_maker_model>
  <rc_body_type_desc>TRUCK (OPEN BODY)</rc_body_type_desc>
  <rc_fuel_desc>DIESEL</rc_fuel_desc>
  <rc_manu_month_yr>01/2022</rc_manu_month_yr>
  <rc_unld_wt>12500</rc_unld_wt>
  <rc_gvw>47500</rc_gvw>
  <rc_no_cyl>6</rc_no_cyl>
  <rc_cubic_cap>6700.00</rc_cubic_cap>
  <rc_status>ACTIVE</rc_status>
</VehicleDetails>
"""


def error_xml() -> str:
    return """<?xml version="1.0" encoding="UTF-8"?>
<VehicleDetails>
  <stautsMessage>ERROR</stautsMessage>
  <error_code>RECORD_NOT_FOUND</error_code>
</VehicleDetails>
"""


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "provider": "mock-api-setu"}


@app.post("/vahan/rc")
async def lookup_rc(request: Request) -> Response:
    api_key = request.headers.get(API_KEY_HEADER)
    if api_key != expected_api_key():
        return Response(
            content="<error>unauthorized</error>",
            status_code=401,
            media_type="application/xml",
        )
    body = (await request.body()).decode("utf-8", errors="replace")
    match = _REG_PATTERN.search(body)
    registration = match.group(1).strip() if match else ""
    if not registration or "FAIL" in registration.upper():
        return Response(content=error_xml(), media_type="application/xml")
    return Response(content=rc_xml(registration), media_type="application/xml")
