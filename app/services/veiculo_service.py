import json
from sqlalchemy.orm import Session
from app.models.modelos import VeiculoModel
from app.schemas.schemas import CadastroVeiculoInput, ConsultaVeiculoInput

class VeiculoService:
    """Camada de Serviço Core: Isola as regras de inteligência de mercado automotivo"""
    
    @staticmethod
    def procurar_veiculo_especifico(db: Session, marca: str, modelo: str, versao: str):
        return db.query(VeiculoModel).filter(
            VeiculoModel.marca == marca,
            VeiculoModel.modelo == modelo,
            VeiculoModel.versao == versao
        ).first()

    @staticmethod
    def processar_analise_competitiva(db: Session, payload: ConsultaVeiculoInput) -> dict:
        veiculo = VeiculoService.procurar_veiculo_especifico(db, payload.marca, payload.modelo, payload.versao)
        
        # Saída Obrigatória unificada exigida pelo edital do desafio
        saida_padronizada = {
            "marca": payload.marca,
            "modelo": payload.modelo,
            "versao": payload.versao,
            "dados_tecnicos_principais": {
                "motorizacao": veiculo.motorizacao if veiculo else "vazio / não disponível",
                "potencia": veiculo.potencia if veiculo else "vazio / não disponível",
                "transmissao": veiculo.transmissao if veiculo else "vazio / não disponível",
                "tracao": veiculo.tracao if veiculo else "vazio / não disponível",
                "preco_sugerido": veiculo.preco_sugerido if veiculo else "vazio / não disponível"
            },
            "equipamentos_pesquisados_livres": {}
        }
        
        equipamentos_map = {}
        if veiculo and veiculo.pacote_equipamentos:
            try:
                equipamentos_map = json.loads(veiculo.pacote_equipamentos)
            except Exception:
                pass
                
        for atributo in payload.atributos_desejados:
            saida_padronizada["equipamentos_pesquisados_livres"][atributo] = equipamentos_map.get(atributo, "vazio / não disponível")
            
        return saida_padronizada

    @staticmethod
    def registar_novo_veiculo(db: Session, v: CadastroVeiculoInput):
        novo = VeiculoModel(
            marca=v.marca, modelo=v.modelo, versao=v.versao,
            motorizacao=v.motorizacao, potencia=v.potencia,
            transmissao=v.transmissao, tracao=v.tracao,
            preco_sugerido=v.preco_sugerido,
            pacote_equipamentos=json.dumps(v.pacote_equipamentos)
        )
        db.add(novo)
        db.commit()
        return novo