from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings
from app.core.security import verificar_palavra_passe
from app.models.modelos import UtilizadorModel
from sqlalchemy.orm import Session

class AuthService:
    @staticmethod
    def autenticar_utilizador(db: Session, username: str, palavra_passe: str):
        user = db.query(UtilizadorModel).filter(UtilizadorModel.username == username).first()
        if not user or not verificar_palavra_passe(palavra_passe, user.password_hash):
            return None
        return user

    @staticmethod
    def criar_token_jwt(username: str, role: str) -> str:
        dados_encriptar = {
            "sub": username,
            "role": role,
            "exp": datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        }
        return jwt.encode(dados_encriptar, settings.SECRET_KEY, algorithm=settings.ALGORITHM)