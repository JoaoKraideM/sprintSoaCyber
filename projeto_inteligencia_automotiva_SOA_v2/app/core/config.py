import os

class Settings:
    SERVER_HOST: str = os.getenv("SERVER_HOST", "127.0.0.1")
    SERVER_PORT: int = int(os.getenv("SERVER_PORT", 8000))
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "ChavePadraoDeSegurancaParaDesenvolvimento2026")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    PAYLOAD_SECRET_HMAC: bytes = os.getenv("PAYLOAD_SECRET_HMAC", "IntegrityKeyDefault").encode()
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH_KB", 50)) * 1024

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./inteligencia_automotiva.db")

settings = Settings()