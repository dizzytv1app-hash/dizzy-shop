"""API serverni ishga tushirish uchun (kelajakda web-sayt shu bilan gaplashadi):
python run_api.py"""
import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run("app.api.main:app", host=settings.API_HOST, port=settings.API_PORT, reload=True)
