# Crew AI - Análise de Ações

Projeto de estudo (curso de IA na prática) que usa o [CrewAI](https://www.crewai.com/) pra montar um "time" de 3 agentes de IA que analisam uma ação da bolsa:

1. **Analista de Preços** — busca o histórico de preço da ação no Yahoo Finance e identifica a tendência (alta, baixa ou lateral).
2. **Analista de Notícias** — busca notícias recentes sobre a ação (e também sobre o BTC) e calcula um "termômetro" de medo/ganância do mercado.
3. **Redator** — junta as duas análises e escreve um newsletter final em formato Markdown.

O projeto tem duas formas de uso:

- **`crew-ai.ipynb`** — notebook Jupyter, pra explorar e rodar célula por célula.
- **`crew-ai.py`** — o mesmo código, num app web feito com [Streamlit](https://streamlit.io/).


O LLM usado é o **Google Gemini** (tem uma cota gratuita generosa, sem precisar de cartão de crédito).

## Pré-requisitos

- **Python 3.11 ou superior** (testado com Python 3.13 — evite o 3.14, algumas bibliotecas do projeto ainda não têm suporte completo pra ele).
- Uma **chave de API gratuita do Google Gemini**, gerada em [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

## Como instalar

1. Clone o repositório e entre na pasta do projeto.
2. Crie um ambiente virtual e ative ele:
   ```
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   source .venv/bin/activate   # Linux/Mac
   ```
3. Instale as dependências:
   ```
   pip install -r requirements.txt
   ```
4. Se for rodar o **notebook** (`.ipynb`), instale também:
   ```
   pip install python-dotenv jupyter ipykernel
   ```
   (essas duas não estão no `requirements.txt` porque ele serve pra instalar as dependências do app do Streamlit, que não usa mais o `.env`)

## Configurando sua chave de API

Cada pessoa que for rodar o projeto precisa gerar **sua própria** chave gratuita em [aistudio.google.com/apikey](https://aistudio.google.com/apikey) e configurar localmente — a chave **não** vem junto no repositório (por segurança).

- **Pra rodar o notebook** (`crew-ai.ipynb`): crie um arquivo chamado `.env` na raiz do projeto, com o conteúdo:
  ```
  GEMINI_API_KEY=sua-chave-aqui
  ```

- **Pra rodar o app do Streamlit** (`crew-ai.py`): crie a pasta/arquivo `.streamlit/secrets.toml`, com o conteúdo:
  ```toml
  GEMINI_API_KEY = "sua-chave-aqui"
  ```

Nenhum dos dois arquivos é enviado pro GitHub (estão no `.gitignore`) — por isso cada pessoa precisa criar o seu.

## Como executar

- **Notebook**: abre `crew-ai.ipynb` no VSCode, seleciona o kernel do `.venv` criado acima, e roda as células em ordem, de cima pra baixo.
- **App web (Streamlit)**:
  ```
  streamlit run crew-ai.py
  ```
  Vai abrir uma aba no navegador com um campo pra digitar o código da ação (ex: `AAPL`, `AMZN`) e gerar a análise.

