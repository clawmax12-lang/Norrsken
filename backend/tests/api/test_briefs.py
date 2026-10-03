import pytest

from preflight.api import app as app_module
from preflight.api.app import MAX_REQUEST_BYTES
from preflight.contracts import Brief, RunRecord, RunState
from preflight.intake.images import MAX_IMAGE_BYTES
from tests.intake.imaging import image_bytes, jpeg, png

FIELDS = {
    "product_name": "Acme Notes",
    "one_liner": "Notes that organise themselves",
    "goal": "signups",
    "audience": "busy startup founders",
}


def shots(count=3, filename="whatever.exe", content_type="text/plain"):
    return [("screenshots", (filename, png(), content_type)) for _ in range(count)]


async def submit(client, fields=None, files=None):
    return await client.post(
        "/api/briefs", data=fields or FIELDS, files=shots() if files is None else files
    )


async def test_a_valid_brief_creates_a_project(client, store):
    response = await submit(
        client, {**FIELDS, "goal_note": "Launch week", "brand_color": "#00aa11"}
    )

    assert response.status_code == 201
    body = response.json()
    assert response.headers["location"] == f"/api/projects/{body['project_id']}"
    assert body["product_name"] == "Acme Notes"
    assert body["goal"] == "signups"
    assert body["goal_note"] == "Launch week"
    assert body["brand_color"] == "#00aa11"
    paths = store.paths(body["project_id"])
    assert store.read(paths.brief, Brief).screenshots == tuple(body["screenshots"])
    assert store.read(paths.run, RunRecord).state is RunState.BRIEF_RECEIVED


async def test_client_filenames_and_types_are_never_used(client, store):
    files = [("screenshots", ("../../evil.sh", jpeg(), "application/x-sh")) for _ in range(3)]

    response = await submit(client, files=files)

    body = response.json()
    assert body["screenshots"] == [f"uploads/screenshot-{n}.jpg" for n in (1, 2, 3)]
    uploads = store.paths(body["project_id"]).uploads
    assert sorted(p.name for p in uploads.iterdir()) == [
        "screenshot-1.jpg",
        "screenshot-2.jpg",
        "screenshot-3.jpg",
    ]


async def test_an_optional_logo_is_saved(client, store):
    files = [*shots(), ("logo", ("brand.png", png(), "image/png"))]

    body = (await submit(client, files=files)).json()

    assert body["logo"] == "uploads/logo.png"
    assert (store.paths(body["project_id"]).root / "uploads/logo.png").read_bytes() == png()


async def test_an_empty_nameless_logo_part_means_no_logo(client):
    files = [*shots(), ("logo", ("", b"", "application/octet-stream"))]

    response = await submit(client, files=files)

    assert response.status_code == 201
    assert response.json()["logo"] is None


async def test_a_named_but_empty_logo_is_rejected(client):
    files = [*shots(), ("logo", ("brand.png", b"", "image/png"))]

    response = await submit(client, files=files)

    assert response.status_code == 422
    assert "logo is empty" in response.json()["error"]["message"]


@pytest.mark.parametrize("missing", list(FIELDS))
async def test_a_missing_required_field_is_a_422_error_body(client, missing):
    fields = {key: value for key, value in FIELDS.items() if key != missing}

    response = await submit(client, fields)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert missing in error["message"]


async def test_an_unknown_goal_is_rejected(client):
    response = await submit(client, {**FIELDS, "goal": "go viral"})

    assert response.status_code == 422
    assert "goal" in response.json()["error"]["message"]


async def test_a_blank_product_name_is_rejected_with_the_field_named(client):
    response = await submit(client, {**FIELDS, "product_name": "  "})

    assert response.status_code == 422
    assert "product_name" in response.json()["error"]["message"]


async def test_a_141_character_one_liner_is_rejected(client):
    response = await submit(client, {**FIELDS, "one_liner": "x" * 141})

    assert response.status_code == 422
    assert "one_liner" in response.json()["error"]["message"]


@pytest.mark.parametrize("count", [0, 2, 7])
async def test_screenshot_count_outside_three_to_six_is_rejected(client, count):
    response = await submit(client, files=shots(count))

    assert response.status_code == 422


async def test_a_text_file_named_png_is_rejected(client):
    files = [*shots(2), ("screenshots", ("fake.png", b"just text", "image/png"))]

    response = await submit(client, files=files)

    assert response.status_code == 422
    assert "screenshot 3" in response.json()["error"]["message"]


async def test_an_unsupported_image_format_is_rejected(client):
    files = [*shots(2), ("screenshots", ("a.png", image_bytes("GIF"), "image/png"))]

    response = await submit(client, files=files)

    assert response.status_code == 422


async def test_an_empty_screenshot_is_rejected(client):
    files = [*shots(2), ("screenshots", ("a.png", b"", "image/png"))]

    assert (await submit(client, files=files)).status_code == 422


async def test_an_oversized_screenshot_is_rejected(client):
    files = [*shots(2), ("screenshots", ("a.png", b"0" * (MAX_IMAGE_BYTES + 1), "image/png"))]

    response = await submit(client, files=files)

    assert response.status_code == 422
    assert "larger than 10 MB" in response.json()["error"]["message"]


async def test_a_rejected_submission_leaves_no_project_behind(client, store, tmp_path):
    await submit(client, files=shots(2))

    assert not (tmp_path / "projects").exists() or not list((tmp_path / "projects").iterdir())


async def test_a_declared_oversized_request_gets_413(make_client, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_REQUEST_BYTES", 5_000)
    async with make_client() as client:
        response = await client.post(
            "/api/briefs",
            data=FIELDS,
            files=[("screenshots", ("a.png", b"0" * 6_000, "image/png"))],
        )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


async def test_a_chunked_oversized_request_gets_413(make_client, monkeypatch):
    monkeypatch.setattr(app_module, "MAX_REQUEST_BYTES", 5_000)

    async def chunks():
        yield b'--x\r\nContent-Disposition: form-data; name="screenshots"; filename="a.png"\r\n\r\n'
        for _ in range(10):
            yield b"0" * 1_000

    async with make_client() as client:
        response = await client.post(
            "/api/briefs",
            content=chunks(),
            headers={"content-type": "multipart/form-data; boundary=x"},
        )

    assert response.status_code == 413
    assert response.json()["error"]["code"] == "payload_too_large"


def test_the_request_limit_fits_six_screenshots_and_a_logo():
    assert MAX_REQUEST_BYTES > 7 * MAX_IMAGE_BYTES
