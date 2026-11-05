# ⚽ WM_Imports API - Backend RESTful (Python / FastAPI)

![Python](https://img.shields.io/badge/Python-3.13+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15.x-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)
![Status](https://img.shields.io/badge/Status-Em_Desenvolvimento_(Sprint_2)-yellow?style=for-the-badge)

API RESTful desenvolvida em **Python** e **FastAPI** para a sustentação da plataforma de e-commerce **WM_Imports**, especializada na comercialização de camisas de futebol (Seleções, Clubes Nacionais e Internacionais). Projeto de Extensão Universitária com entrega final agendada para **07/12/2026**.

---

## 📌 Visão Geral da API

A **WM_Imports API** provê todos os serviços e regras de negócio essenciais para o funcionamento do e-commerce. A aplicação é responsável por gerenciar o catálogo de camisas, controlar o estoque relacional por tamanhos (P, M, G, GG), autenticar usuários e administradores com segurança, calcular fretes em tempo real, processar pagamentos assíncronos via Webhooks do Mercado Pago e enviar notificações operacionais.

---

## 🚀 Funcionalidades Principais (Backend)

* **🔐 Autenticação & Segurança (JWT / RBAC):** Criptografia de senhas com `bcrypt`, geração de Tokens JWT e controle de permissões por perfil (*Cliente* vs. *Administrador*).
* **📦 Gestão de Produtos e Estoque:** CRUD relacional no PostgreSQL com controle por tamanho (P, M, G, GG) e categorias (Seleções, Nacionais e Internacionais).
* **🚚 Integração de Frete:** Integração com a API do **ViaCEP** para autocompletar endereços e cálculo dinâmico de envio (Normal e Expressa).
* **💳 Gateway de Pagamento & Webhooks:** Comunicação assíncrona com Mercado Pago para geração de QR Code PIX/Cartão e atualização automática de status do pedido.
* **⚡ Upload de Mídias na Nuvem:** Envio e otimização de imagens de produtos e banners diretamente para Cloud Storage (Supabase Storage/Cloudinary).
* **📄 Documentação Interativa:** Interfaces Swagger UI (`/docs`) e ReDoc (`/redoc`) geradas nativamente pelo FastAPI.

---

## 🛠️ Tecnologias e Bibliotecas

* **Linguagem:** Python 3.13+
* **Framework Web:** [FastAPI](https://fastapi.tiangolo.com/)
* **Servidor ASGI:** [Uvicorn](https://www.uvicorn.org/)
* **Validação de Dados:** Pydantic v2
* **Banco de Dados:** PostgreSQL (SQLAlchemy ORM / Alembic para migrations)
* **Variáveis de Ambiente:** `python-dotenv`
* **Criptografia e Autenticação:** `passlib`, `bcrypt`, `python-jose` (JWT)

---

## 📂 Estrutura do Projeto

```text
WM_imports_api/
├── app/
│   ├── api/            # Endpoints e roteadores da API (v1)
│   ├── core/           # Configurações globais, segurança (JWT) e variáveis
│   ├── db/             # Conexão com banco PostgreSQL e modelos SQLAlchemy
│   ├── schemas/        # Schemas Pydantic de validação de dados
│   └── services/       # Regras de negócio e integrações externas (ViaCEP, Mercado Pago)
├── .env.example        # Modelo de configuração de variáveis de ambiente
├── .gitignore          # Arquivos ignorados pelo Git
├── main.py             # Ponto de entrada da aplicação FastAPI
├── requirements.txt    # Lista de dependências Python
└── README.md           # Documentação técnica do backend


⚙️ Como Executar a API Localmente
Pré-requisitos
 °  Python 3.13+ instalado no sistema.

 °  Gerenciador de pacotes pip.

 °  Banco de dados PostgreSQL instalado localmente ou instância no Supabase.

Passo a Passo
    1.  Clone o repositório:
        Bash
        git clone [https://github.com/samuelvaleriano/WM_imports_api.git](https://github.com/          samuelvaleriano/WM_imports_api.git)
        cd WM_imports_api

    2.  Crie e ative o Ambiente Virtual (.venv):
        °   Cmder / CMD:

            DOS
            .\.venv\Scripts\activate

        °   Windows PowerShell:

            PowerShell
            .\.venv\Scripts\Activate.ps1
        
        °   Linux / macOS / Git Bash:

            Bash
            source .venv/bin/activate

    3.  Instale as dependências do projeto:
        Bash
        pip install -r requirements.txt
    
    4.  Configure as Variáveis de Ambiente:
        Crie um arquivo .env na raiz do projeto com a seguinte estrutura:

        Snippet de código

        PORT=8000
        DATABASE_URL=postgresql://usuario:senha@localhost:5432/wmimports_db
        SECRET_KEY=sua_chave_secreta_jwt_aqui
        ALGORITHM=HS256
        ACCESS_TOKEN_EXPIRE_MINUTES=1440

    5.  Execute a aplicação (Uvicorn):
        Bash
        uvicorn app.main:app --reload
    
    6.  Acesse a Documentação da API:
        °   Swagger UI: http://127.0.0.1:8000/docs
        °   ReDoc: http://127.0.0.1:8000/redoc

### Login padrão do lojista (desenvolvimento)

Na inicialização, o backend cria o administrador caso ele ainda não exista:

```text
E-mail: admin@wmimports.com
Senha: Admin@123456
Perfil: admin
```

O cadastro é idempotente: reiniciar a API não duplica o usuário. Para alterar as
credenciais, defina `ADMIN_EMAIL`, `ADMIN_PASSWORD` e `ADMIN_NAME` no arquivo
`.env` antes de iniciar o backend. Em produção, use uma senha diferente.

### Upload de imagens e cadastro de produtos

Configure no `.env` as credenciais do Supabase Storage:

```text
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...
SUPABASE_STORAGE_BUCKET=product-images
```

Crie no Supabase um bucket público chamado `product-images` (ou use o nome
definido em `SUPABASE_STORAGE_BUCKET`). O endpoint protegido para upload aceita
somente PNG/WEBP com até 5 MB:

```text
POST /api/v1/admin/upload
POST /api/admin/upload
```

Envie `multipart/form-data` com o campo `arquivo`. A resposta contém `url` e
`imagem_url`. Use esse valor no cadastro do produto:

```json
{
  "nome": "Camisa Flamengo",
  "preco": 349.9,
  "imagem_url": "https://seu-projeto.supabase.co/storage/v1/object/public/product-images/products/arquivo.webp",
  "time_id": 1,
  "descricao": "Camisa oficial",
  "ativo": true,
  "variacoes": [
    {"tamanho": "M", "estoque": 10},
    {"tamanho": "G", "estoque": 5}
  ]
}
```

O backend salva a URL em `produtos.imagem_url` e também em
`produtos.imagem_capa` para manter o catálogo atual compatível.

O cadastro também aceita `desconto_percentual`, com valor entre `0` e `100`.
O campo é persistido em `produtos.desconto_percentual`; `0` significa que o
produto não está em promoção. O frontend pode calcular o preço promocional com:

```text
preco_promocional = preco * (1 - desconto_percentual / 100)
```

Endpoints administrativos para preencher o formulário:

```text
GET /api/v1/admin/catalog/categories
GET /api/v1/admin/catalog/subcategories?categoria_id=1
GET /api/v1/admin/catalog/teams?subcategoria_id=1
```

Todos exigem `Authorization: Bearer <access_token>` de um usuário `admin`.

### Banner principal

O banner principal é persistido na tabela `hero_banners` e pode ser gerenciado
pelo lojista:

```text
GET   /api/v1/admin/hero-banner
PATCH /api/v1/admin/hero-banner
POST  /api/v1/admin/upload
```

O `PATCH` recebe `{ "campanhas": [...] }`. Cada campanha pode ter `id` para
atualizar uma existente ou omitir o campo para criar uma nova. Campanhas que
não vierem na lista são removidas. `imagem_url` deve ser uma URL HTTP/HTTPS
pública e `frase_promocional` não pode ser vazia. O upload retorna
`imagem_url` e aceita somente PNG/WEBP com até 5 MB. O `GET` sempre retorna
`{ "campanhas": [...] }`, inclusive quando a lista está vazia.

### Consulta de CEP

Use `GET /api/v1/cep/{cep}` para consultar o ViaCEP pelo backend. O CEP pode ser enviado com ou sem hífen, por exemplo:

```text
GET http://127.0.0.1:8000/api/v1/cep/01001-000
```

A resposta inclui `cep`, `logradouro`, `complemento`, `bairro`, `localidade` e `uf`. O endpoint retorna `422` para formato inválido, `404` quando o CEP não é encontrado e `502` quando o ViaCEP está indisponível ou retorna dados inválidos.

📝 Padrão de Commits (Conventional Commits)

Neste repositório utilizaremos a convenção Conventional Commits:

°   feat: Nova funcionalidade (ex: feat: adiciona rota de login com JWT)

°   fix: Correção de bug (ex: fix: ajusta validacao no schema de produto)

°   docs: Alterações em documentação (ex: docs: atualiza README com instruçoes de execução)

°   refactor: Melhoria no código sem alterar regras de negócio (ex: refactor: otimiza conexao com banco)

°   chore: Tarefas de manutenção ou dependências (ex: chore: adiciona dependencias no requirements)

📜 Licença e Contexto Acadêmico

Desenvolvido como Projeto de Extensão Universitária.

Data Limite para Entrega: 07 de Dezembro de 2026.