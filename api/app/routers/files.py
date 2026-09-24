import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings

router = APIRouter(tags=["files"])

_file_path_cache: dict[str, str] = {}


@router.get("/files/{file_id}")
async def get_file(file_id: str):
    """
    Mini app rasmni shu endpoint orqali ko'rsatadi: <img src="/api/files/{file_id}" />
    Diqqat: bot tokeni hech qachon brauzerga (Location/redirect orqali ham) yuborilmaydi —
    rasm baytlari serverda o'qib, shu yerdan browserga oqim (stream) qilib beriladi.
    """
    if not settings.BOT_TOKEN:
        raise HTTPException(500, "BOT_TOKEN sozlanmagan")

    file_path = _file_path_cache.get(file_id)
    if not file_path:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"https://api.telegram.org/bot{settings.BOT_TOKEN}/getFile", params={"file_id": file_id})
        data = resp.json()
        if not data.get("ok"):
            raise HTTPException(404, "Rasm topilmadi")
        file_path = data["result"]["file_path"]
        _file_path_cache[file_id] = file_path

    file_url = f"https://api.telegram.org/file/bot{settings.BOT_TOKEN}/{file_path}"
    client = httpx.AsyncClient(timeout=15)
    req = client.build_request("GET", file_url)
    resp = await client.send(req, stream=True)
    if resp.status_code != 200:
        await resp.aclose()
        await client.aclose()
        raise HTTPException(404, "Rasm topilmadi")

    content_type = resp.headers.get("content-type", "image/jpeg")

    async def body():
        try:
            async for chunk in resp.aiter_bytes():
                yield chunk
        finally:
            await resp.aclose()
            await client.aclose()

    return StreamingResponse(body(), media_type=content_type)
