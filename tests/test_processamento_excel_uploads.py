import asyncio
from datetime import date, datetime, timedelta
from io import BytesIO
import os
import unittest
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.requests import Request
from starlette.datastructures import Headers

# Evita dependencia de MySQL/PyMySQL no bootstrap de imports durante os testes.
_BOOTSTRAP_DB = (Path(__file__).resolve().parent / "tests_bootstrap.db").as_posix()
os.environ["DB_DRIVER"] = "sqlite"
os.environ["SQLITE_DATABASE_URL"] = f"sqlite:///{_BOOTSTRAP_DB}"
os.environ["DATABASE_URL"] = f"sqlite:///{_BOOTSTRAP_DB}"

from app.api.deps import verificar_rbac
from app.core.config import settings
from app.core.middleware import _validar_assinatura_payload
from app.core.privacy import descriptografar_bytes
from app.db.session import Base
from app.models.modelos import (
    LogAuthModel,
    LogModel,
    MarcaModel,
    MetricaVeiculoModel,
    ModeloModel,
    PasswordResetTokenModel,
    VeiculoModel,
    VersaoModel,
)
from app.services.auth_service import AuthService
from app.services.retencao_service import RetencaoService
from app.services.upload_service import ImportacaoExcelError, UploadService
from app.services.veiculo_service import VeiculoService


class ProcessamentoExcelUploadsTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db_path = Path(__file__).resolve().parent / "tmp_test_uploads.db"
        cls.db_path = db_path
        if db_path.exists():
            db_path.unlink()

        cls.engine = create_engine(
            f"sqlite:///{db_path.as_posix()}",
            connect_args={"check_same_thread": False},
            pool_pre_ping=True,
        )
        cls.SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        cls.engine.dispose()
        if cls.db_path.exists():
            cls.db_path.unlink()

    def setUp(self):
        Base.metadata.drop_all(bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
        self.admin_user_id, self.admin_token = self._criar_utilizador_e_token(
            email="admin@sistema.local",
            password="Admin1234",
            role="admin",
        )
        self.user_user_id, self.user_token = self._criar_utilizador_e_token(
            email="user@sistema.local",
            password="User12345",
            role="user",
        )

    def _criar_utilizador_e_token(self, email: str, password: str, role: str) -> tuple[int, str]:
        with self.SessionTesting() as db:
            user = AuthService.cadastrar_utilizador(db, email=email, password=password, role=role, nome=role)
            fingerprint = AuthService.fingerprint_atual_do_utilizador(user)
            token = AuthService.criar_token_jwt(user.email, user.role, fingerprint)
            return int(user.id), token

    @staticmethod
    def _gerar_excel_bytes(valido: bool = True) -> bytes:
        from openpyxl import Workbook

        workbook = Workbook()
        worksheet = workbook.active
        worksheet.title = "BASE" if valido else "OUTRA_ABA"

        worksheet.append(["Equipamentos", "XLT 3.0L V6 AT 26MY", "Limited 3.0L V6 26MY", "Limited + 3.0L V6 26MY"])
        worksheet.append([None, "RANGER 26MY", "RANGER 26MY", "RANGER 26MY"])
        worksheet.append(["Engine & Transmission", "Coluna1", "Coluna2", "Coluna3"])
        worksheet.append(["Peso em ordem de marchas", 2283, 2357, 2357])
        worksheet.append(["Cilindrada", 3, 3, 3])
        worksheet.append(["Potência", 250, 250, 250])
        worksheet.append(["Torque", 600, 600, 600])
        worksheet.append(["Transmissão Automática", "X", "X", "X"])
        worksheet.append(["Motor Flex vs Gasolina", 0, 0, 0])
        worksheet.append(["Quantidade de marchas", 10, 10, 10])
        worksheet.append(["Motor Diesel", "X", "X", "X"])
        worksheet.append(["Motor Elétrico", 0, 0, 0])
        worksheet.append(["Tração 4x4 (high/low)", 0, 0, 0])
        worksheet.append(["Tração integral (AWD)", "X", "X", "X"])
        worksheet.append(["Tração Traseira", 0, 0, 0])
        worksheet.append(["Wheels", None, None, None])
        worksheet.append(["Polegadas", 17, 18, 20])
        worksheet.append(["Pneus ATR (50/50)", "X", "X", 0])
        worksheet.append(["<script>alert(1)</script>Campo XSS", "<img src=x onerror=alert(1)>", "OK", "OK"])

        buffer = BytesIO()
        workbook.save(buffer)
        return buffer.getvalue()

    @staticmethod
    def _novo_upload_excel(excel_bytes: bytes) -> UploadFile:
        return UploadFile(
            filename="fiap_ford.xlsx",
            file=BytesIO(excel_bytes),
            headers=Headers({"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"}),
        )

    def test_processa_excel_e_cria_catalogo_com_metricas(self):
        with self.SessionTesting() as db:
            resultado = asyncio.run(
                UploadService.processar_importacao_excel(
                    db=db,
                    user_id=self.admin_user_id,
                    arquivo=self._novo_upload_excel(self._gerar_excel_bytes(valido=True)),
                    ip_origem="127.0.0.1",
                    user_agent="tests",
                )
            )

            self.assertEqual(resultado["status"], "sucesso")
            self.assertEqual(resultado["marca"], "FORD")
            self.assertEqual(resultado["modelo"], "RANGER 26MY")
            self.assertEqual(resultado["versoes_processadas"], 3)
            self.assertEqual(resultado["veiculos_criados"], 3)
            self.assertEqual(resultado["metricas_criadas"], 3)
            self.assertEqual(resultado["erros_validacao"], [])

            self.assertEqual(db.query(MarcaModel).count(), 1)
            self.assertEqual(db.query(ModeloModel).count(), 1)
            self.assertEqual(db.query(VersaoModel).count(), 3)
            self.assertEqual(db.query(VeiculoModel).count(), 3)
            self.assertEqual(db.query(MetricaVeiculoModel).count(), 3)
            self.assertEqual(db.query(LogModel).filter(LogModel.acao == "IMPORTACAO_EXCEL_PROCESSADA").count(), 3)
            self.assertEqual(db.query(LogModel).filter(LogModel.acao == "ENVIO_INFORMACOES_EXCEL").count(), 1)

            metrica = db.query(MetricaVeiculoModel).first()
            self.assertIsNone(metrica.preco_sugerido)
            self.assertIn("Engine & Transmission", metrica.pacote_equipamentos)
            self.assertIn("Wheels", metrica.pacote_equipamentos)
            self.assertNotIn("<script>", str(metrica.pacote_equipamentos))
            self.assertNotIn("<img", str(metrica.pacote_equipamentos))

            log_envio = db.query(LogModel).filter(LogModel.acao == "ENVIO_INFORMACOES_EXCEL").first()
            self.assertEqual(log_envio.dados_depois["tipo_arquivo"], "datasheet_ford_excel")
            self.assertEqual(log_envio.dados_depois["nome_arquivo"], "fiap_ford.xlsx")
            self.assertEqual(log_envio.dados_depois["aba_origem"], "BASE")
            self.assertEqual(log_envio.dados_depois["status_envio"], "PROCESSADO")
            self.assertEqual(log_envio.dados_depois["versoes_processadas"], 3)
            self.assertEqual(log_envio.dados_depois["metricas_criadas"], 3)
            self.assertIn("Potência", metrica.pacote_equipamentos["Engine & Transmission"])

    def test_upload_simples_cria_log_mesmo_sem_metrica(self):
        caminho_criado = None
        excel_bytes = self._gerar_excel_bytes(valido=True)
        try:
            with self.SessionTesting() as db:
                resultado = asyncio.run(
                    UploadService.processar_upload_excel(
                        db=db,
                        user_id=self.user_user_id,
                        user_email="user@sistema.local",
                        arquivo=self._novo_upload_excel(excel_bytes),
                        ip_origem="127.0.0.1",
                        user_agent="tests",
                    )
                )
                caminho_criado = Path(resultado["caminho_arquivo"])

                self.assertIsNone(resultado["metrica_id"])
                self.assertEqual(db.query(LogModel).count(), 1)
                self.assertTrue(caminho_criado.name.endswith(".enc"))
                self.assertNotEqual(caminho_criado.read_bytes(), excel_bytes)
                self.assertEqual(descriptografar_bytes(caminho_criado.read_bytes()), excel_bytes)

                log_envio = db.query(LogModel).filter(LogModel.acao == "ENVIO_INFORMACOES_EXCEL").first()
                self.assertIsNone(log_envio.metrica_veiculo_id)
                self.assertEqual(log_envio.dados_depois["nome_arquivo"], "fiap_ford.xlsx")
                self.assertEqual(log_envio.dados_depois["status_envio"], "ARQUIVO_RECEBIDO")
                self.assertTrue(log_envio.dados_depois["criptografado_em_repouso"])
        finally:
            if caminho_criado:
                try:
                    caminho_criado.unlink(missing_ok=True)
                except PermissionError:
                    pass

    def test_reimport_cria_historico_sem_duplicar_veiculo(self):
        arquivo = self._gerar_excel_bytes(valido=True)
        with self.SessionTesting() as db:
            asyncio.run(
                UploadService.processar_importacao_excel(
                    db=db,
                    user_id=self.admin_user_id,
                    arquivo=self._novo_upload_excel(arquivo),
                    ip_origem="127.0.0.1",
                    user_agent="tests",
                )
            )
            asyncio.run(
                UploadService.processar_importacao_excel(
                    db=db,
                    user_id=self.admin_user_id,
                    arquivo=self._novo_upload_excel(arquivo),
                    ip_origem="127.0.0.1",
                    user_agent="tests",
                )
            )

            self.assertEqual(db.query(VeiculoModel).count(), 3)
            self.assertEqual(db.query(MetricaVeiculoModel).count(), 6)
            self.assertEqual(db.query(LogModel).filter(LogModel.acao == "IMPORTACAO_EXCEL_PROCESSADA").count(), 6)
            self.assertEqual(db.query(LogModel).filter(LogModel.acao == "ENVIO_INFORMACOES_EXCEL").count(), 2)

    def test_retorna_erro_quando_nao_existe_aba_base(self):
        with self.SessionTesting() as db:
            with self.assertRaises(ImportacaoExcelError) as contexto:
                asyncio.run(
                    UploadService.processar_importacao_excel(
                        db=db,
                        user_id=self.admin_user_id,
                        arquivo=self._novo_upload_excel(self._gerar_excel_bytes(valido=False)),
                        ip_origem="127.0.0.1",
                        user_agent="tests",
                    )
                )

            erro = contexto.exception
            self.assertIn("BASE", " ".join(erro.erros_validacao))
            self.assertEqual(db.query(MarcaModel).count(), 0)
            self.assertEqual(db.query(MetricaVeiculoModel).count(), 0)
            self.assertEqual(db.query(LogModel).count(), 0)

    def test_rbac_bloqueia_user_no_processamento(self):
        validador = verificar_rbac(["admin", "analista"])

        with self.SessionTesting() as db:
            with self.assertRaises(HTTPException) as contexto:
                validador(authorization=f"Bearer {self.user_token}", db=db)

            self.assertEqual(contexto.exception.status_code, 403)

    def test_busca_veiculo_resiste_sql_injection(self):
        with self.SessionTesting() as db:
            asyncio.run(
                UploadService.processar_importacao_excel(
                    db=db,
                    user_id=self.admin_user_id,
                    arquivo=self._novo_upload_excel(self._gerar_excel_bytes(valido=True)),
                    ip_origem="127.0.0.1",
                    user_agent="tests",
                )
            )

            tentativa = VeiculoService.procurar_veiculo_especifico(
                db,
                marca="FORD' OR 1=1 --",
                modelo="RANGER 26MY",
                versao="XLT 3.0L V6 AT 26MY",
            )

            self.assertIsNone(tentativa)
            self.assertEqual(db.query(VeiculoModel).count(), 3)

    def test_logs_auth_pseudonimizam_dados_pessoais(self):
        with self.SessionTesting() as db:
            AuthService.registar_log_auth(
                db,
                user_id=self.user_user_id,
                address="user@sistema.local",
                ip="127.0.0.1",
                user_agent="pytest-agent",
                status=False,
            )

            log_auth = db.query(LogAuthModel).first()
            self.assertTrue(log_auth.address.startswith("pseudo:"))
            self.assertTrue(log_auth.ip.startswith("pseudo:"))
            self.assertTrue(log_auth.user_agent.startswith("pseudo:"))
            self.assertNotIn("user@sistema.local", log_auth.address)

    def test_retencao_remove_logs_antigos_tokens_expirados_e_uploads(self):
        upload_dir_original = settings.UPLOAD_DIR
        upload_dir_teste = Path(__file__).resolve().parent / "tmp_uploads_retencao"
        upload_dir_teste.mkdir(exist_ok=True)
        arquivo_antigo = upload_dir_teste / "antigo.xlsx"
        arquivo_antigo.write_bytes(b"teste")
        antigo_timestamp = datetime.now().timestamp() - ((settings.UPLOAD_RETENTION_DAYS + 1) * 24 * 60 * 60)
        os.utime(arquivo_antigo, (antigo_timestamp, antigo_timestamp))
        settings.UPLOAD_DIR = str(upload_dir_teste)

        try:
            with self.SessionTesting() as db:
                log_antigo = LogModel(
                    user_id=self.user_user_id,
                    acao="TESTE_RETENCAO",
                    create_date=date.today() - timedelta(days=settings.AUDIT_LOG_RETENTION_DAYS + 1),
                    hour_date=datetime.now().time().replace(microsecond=0),
                )
                log_auth_antigo = LogAuthModel(
                    user_id=self.user_user_id,
                    status=False,
                    create_date=date.today() - timedelta(days=settings.AUTH_LOG_RETENTION_DAYS + 1),
                    hour_date=datetime.now().time().replace(microsecond=0),
                )
                token_expirado = PasswordResetTokenModel(
                    user_id=self.user_user_id,
                    token="token-expirado",
                    expires_at=datetime.now() - timedelta(days=1),
                )
                db.add_all([log_antigo, log_auth_antigo, token_expirado])
                db.commit()

                resultado = RetencaoService.expurgar_dados_antigos(db)

                self.assertEqual(resultado["logs_removidos"], 1)
                self.assertEqual(resultado["logs_auth_removidos"], 1)
                self.assertEqual(resultado["tokens_expirados_removidos"], 1)
                self.assertEqual(resultado["uploads_removidos"], 1)
                self.assertFalse(arquivo_antigo.exists())
        finally:
            settings.UPLOAD_DIR = upload_dir_original
            try:
                upload_dir_teste.rmdir()
            except OSError:
                pass

    def test_middleware_exige_assinatura_quando_configurado(self):
        valor_original = settings.REQUIRE_PAYLOAD_SIGNATURE
        settings.REQUIRE_PAYLOAD_SIGNATURE = True
        try:
            corpo = b'{"marca":"FORD","modelo":"RANGER 26MY","versao":"XLT","atributos_desejados":[]}'

            async def receive():
                return {"type": "http.request", "body": corpo, "more_body": False}

            request = Request(
                {
                    "type": "http",
                    "method": "POST",
                    "path": "/api/v1/veiculos/comparar",
                    "query_string": b"",
                    "headers": [(b"content-type", b"application/json")],
                    "scheme": "http",
                    "client": ("127.0.0.1", 12345),
                    "server": ("testserver", 80),
                },
                receive,
            )

            resposta = asyncio.run(_validar_assinatura_payload(request))
            self.assertEqual(resposta.status_code, 401)
            self.assertIn("Assinatura", resposta.body.decode("utf-8"))
        finally:
            settings.REQUIRE_PAYLOAD_SIGNATURE = valor_original

    def test_middleware_nao_exige_assinatura_para_auth_publico(self):
        valor_original = settings.REQUIRE_PAYLOAD_SIGNATURE
        settings.REQUIRE_PAYLOAD_SIGNATURE = True
        try:
            corpo = b'{"email":"user@sistema.local","password":"User12345"}'

            async def receive():
                return {"type": "http.request", "body": corpo, "more_body": False}

            request = Request(
                {
                    "type": "http",
                    "method": "POST",
                    "path": "/api/v1/auth/login",
                    "query_string": b"",
                    "headers": [(b"content-type", b"application/json")],
                    "scheme": "http",
                    "client": ("127.0.0.1", 12345),
                    "server": ("testserver", 80),
                },
                receive,
            )

            resposta = asyncio.run(_validar_assinatura_payload(request))
            self.assertIsNone(resposta)
        finally:
            settings.REQUIRE_PAYLOAD_SIGNATURE = valor_original


if __name__ == "__main__":
    unittest.main()
