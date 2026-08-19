from app.db.database import SessionLocal
from app.db.models import Categoria, Subcategoria, Time, Produto, VariacaoProduto, TamanhoEnum

def popular_banco():
    db = SessionLocal()
    try:
        cat_futebol = Categoria(nome="Futebol", slug="futebol")
        db.add(cat_futebol)
        db.commit()

        sub_nacionais = Subcategoria(categoria_id=cat_futebol.id, nome="Clubes Nacionais", slug="clubes-nacionais")
        db.add(sub_nacionais)
        db.commit()

        flamengo = Time(subcategoria_id=sub_nacionais.id, nome="Flamengo", slug="flamengo", escudo_url="https://via.placeholder.com/150")
        db.add(flamengo)
        db.commit()

        camisa = Produto(
            time_id=flamengo.id,
            nome="Camisa Flamengo I 24/25 - Torcedor",
            descricao="Camisa oficial do Mengão",
            preco=349.90,
            imagem_capa="https://via.placeholder.com/300",
            ativo=True
        )
        db.add(camisa)
        db.commit()

        var_g = VariacaoProduto(produto_id=camisa.id, tamanho=TamanhoEnum.G, estoque=10)
        var_gg = VariacaoProduto(produto_id=camisa.id, tamanho=TamanhoEnum.GG, estoque=5)
        db.add_all([var_g, var_gg])
        db.commit()

        print("Dados de teste inseridos com sucesso!")
    except Exception as e:
        print(f"Erro ao popular banco: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    popular_banco()