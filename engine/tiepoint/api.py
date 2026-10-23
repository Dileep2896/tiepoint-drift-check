"""HTTP API for the tie-point workspace; also serves the built web app when web/dist exists."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .checker import run_checks
from .extract import Extractor, default_extractor
from .models import Party
from .seed import SAMPLE_TABLE_TEXT, build_project
from .store import Conflict, InMemoryRepository, NotFound, Repository

Rev = Literal["B", "C"]


class AcceptBody(BaseModel):
    stream_tag: str | None = None


class AttestBody(BaseModel):
    party: Party
    by: str | None = None


class ExtractBody(BaseModel):
    text: str = Field(min_length=1, max_length=200_000)


def create_app(repo: Repository | None = None, extractor: Extractor | None = None, static_dir: Path | None = None) -> FastAPI:
    app = FastAPI(title="Tie-Point Drift Check")
    store = repo or InMemoryRepository()

    def guard(fn):
        try:
            return fn()
        except NotFound as e:
            raise HTTPException(404, f"not found: {e.args[0]}") from None
        except Conflict as e:
            raise HTTPException(409, str(e)) from None

    @app.get("/api/health")
    def health():
        return {"ok": True}

    @app.get("/api/project")
    def project(rev: Rev = Query("C")):
        return store.project(rev).model_dump()

    @app.get("/api/check")
    def check(rev: Rev = Query("C")):
        return run_checks(store.project(rev)).model_dump()

    @app.post("/api/tiepoints/{tp_id}/accept")
    def accept(tp_id: str, body: AcceptBody, rev: Rev = Query("C")):
        return guard(lambda: store.accept(tp_id, rev, body.stream_tag)).model_dump()

    @app.post("/api/tiepoints/{tp_id}/attest")
    def attest(tp_id: str, body: AttestBody, rev: Rev = Query("C")):
        return guard(lambda: store.attest(tp_id, body.party, rev, body.by)).model_dump()

    @app.post("/api/deliverables/{number}/redraft")
    def redraft(number: str, rev: Rev = Query("C")):
        return guard(lambda: store.redraft(number, rev)).model_dump()

    @app.post("/api/reset")
    def reset():
        store.reset()
        return {"ok": True}

    @app.get("/api/story")
    def story():
        """Measured numbers for the explainer, always from a fresh seed (independent of edits)."""
        before, after = run_checks(build_project("B")), run_checks(build_project("C"))
        return {
            "before": before.summary.model_dump(),
            "after": after.summary.model_dump(),
            "findings": [{"id": r.id, "status": r.status, "headline": r.headline} for r in after.tie_points if r.status != "current"],
        }

    @app.get("/api/extract/sample")
    def sample():
        return {"text": SAMPLE_TABLE_TEXT}

    @app.post("/api/extract")
    def extract(body: ExtractBody):
        return (extractor or default_extractor()).extract(body.text).model_dump()

    dist = static_dir or Path(__file__).resolve().parents[2] / "web" / "dist"
    if dist.is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

        @app.get("/{path:path}")
        def spa(path: str):
            f = dist / path
            return FileResponse(f if path and f.is_file() else dist / "index.html")

    return app


app = create_app()
