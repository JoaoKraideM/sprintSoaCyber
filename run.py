import uvicorn
from app.core.config import settings

if __name__ == "__main__":
    ssl_config = {}
    if settings.SSL_CERTFILE and settings.SSL_KEYFILE:
        ssl_config = {
            "ssl_certfile": settings.SSL_CERTFILE,
            "ssl_keyfile": settings.SSL_KEYFILE,
        }

    # Inicialização transparente alinhada com as configurações do arquivo .env
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=settings.APP_ENV != "production",
        **ssl_config,
    )
