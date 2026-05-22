import asyncio
from io import BytesIO
import os
import unittest
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.datastructures import Headers

# Evita dependencia de MySQL/PyMySQL no bootstrap de imports durante os testes.
_BOOTSTRAP_DB = (Path(__file__).resolve().parent / "tests_bootstrap.db").as_posix()
os.environ["DB_DRIVER"] = "sqlite"
os.environ["SQLITE_DATABASE_URL"] = f"sqlite:///{_BOOTSTRAP_DB}"
os.environ["DATABASE_URL"] = f"sqlite:///{_BOOTSTRAP_DB}"

from app.api.deps import verificar_rbac
from app.db.session import Base
from app.models.modelos import LogModel, MarcaModel, MetricaVeiculoModel, ModeloModel, VeiculoModel, VersaoModel
from app.services.auth_service import AuthService
from app.services.upload_service import ImportacaoExcelError, UploadService


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

            metrica = db.query(MetricaVeiculoModel).first()
            self.assertIsNone(metrica.preco_sugerido)
            self.assertIn("Engine & Transmission", metrica.pacote_equipamentos)
            self.assertIn("Wheels", metrica.pacote_equipamentos)
            self.assertIn("Potência", metrica.pacote_equipamentos["Engine & Transmission"])

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


if __name__ == "__main__":
    unittest.main()
