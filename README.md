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
        uvicorn main:app --reload
    
    6.  Acesse a Documentação da API:
        °   Swagger UI: http://127.0.0.1:8000/docs
        °   ReDoc: http://127.0.0.1:8000/redoc

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