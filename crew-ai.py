# Import das Libs
import os
from datetime import datetime, timedelta

import yfinance as yf

from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool

from langchain_community.tools import DuckDuckGoSearchResults
# utilizando o DuckDuckGo por não necessitar de criar uma conta

import streamlit as st


# Quantos meses de histórico buscar no Yahoo Finance.
# Menos meses = menos texto pra IA processar (mais rápido e mais barato em tokens),
MESES_HISTORICO = 3

# Criando Yahoo Finance Tool
@tool("Yahoo Finance Tool")
def fetch_stock_price(ticket: str) -> str:
    """Busca o histórico de preço da ação (ticket) no Yahoo Finance."""
    fim = datetime.now()
    inicio = fim - timedelta(days=MESES_HISTORICO * 30)
    stock = yf.download(ticket, start=inicio.strftime("%Y-%m-%d"), end=fim.strftime("%Y-%m-%d"))
    return stock.to_string()

#Chave de API
os.environ['GEMINI_API_KEY'] = st.secrets['GEMINI_API_KEY']

# Configurando o LLM
# A chave vem do st.secrets (linha acima), não mais do .env
llm = LLM(model="gemini/gemini-3.5-flash-lite")  # mesma chave GEMINI_API_KEY, cota bem maior (500 req/dia)


# Construção do primeiro Agent - Analista de Preços
stockPriceAnalyst = Agent(
    role = "Senior stock price Analyst",
    goal = "Find the {ticket} stock price and analyses trends",
    backstory = """You're highly experienced in analyzing the price of a specific stock
    and make predictions about its future price.""",
    verbose = True,
    llm = llm,
    max_iter = 5,
    memory = True,
    tools = [fetch_stock_price],
    allow_delegation = False,
)

# Criando a tarefa que será atrelada ao Agent
getStockPrice = Task(
    description = "Analyse the stock {ticket} price history and create a trend analyses of up, down or sideways",
    expected_output = """Specify the current stock price - up, down or sideways.
    eg. stock= 'AAPL, price UP' """,
    agent = stockPriceAnalyst
)

# Importando a ferramenta de pesquisa DuckDuck do langchain
# A versão atual do crewai só aceita ferramentas no formato dele (BaseTool do crewai),
# então embrulhamos a ferramenta do langchain numa função com @tool, igual fizemos com o Yahoo Finance
duckduckgo_search = DuckDuckGoSearchResults(backend='news', num_results=10)

# Criando uma ferramenta para pesquisa de Notícias
@tool("Search News Tool")
def search_tool(query: str) -> str:
    """Busca notícias recentes na internet sobre um assunto usando o DuckDuckGo."""
    return duckduckgo_search.invoke(query)


# Criando Agent - Analista de Notícias
newsAnalyst = Agent(
    role = "Stock News Analyst",
    goal = """Create a short summary of the market news related to the stock {ticket} company, Specify the current trend - up, down or sideways 
    with the news context. For each request stock asset, specify a number between 0 and 100, where 0 is extreme fear and 100 is extreme greed.""",
    backstory = """You're highly experienced in analyzing the market trends and news and have tracked assets for more then 10 years.
    
    You're also master level analyst in the traditional markets and have deep understanding of human psychology.

    You understand news, theirs titles and information, but you look at those with a health dose of skepticism.
    You consider also the source of the news articles.
    """,
    verbose = True,
    llm = llm,
    max_iter = 10,
    memory = True,
    tools = [search_tool],
    allow_delegation = False,
)


# Criando a Tarefa do Analista de Notícias
get_news = Task(
    description = f"""Take the stock and always include BTC to it (if not request).
    Use the search tool to search each one individually.

    The current date is {datetime.now()}.

    Compose the results into a helpfull report.
    """,
    expected_output = """A summary of the overall market and one sentence summary for each request asset.
    Include a fear/greed for each asset based on the news. Use format:
    <STOCK ASSET>
    <SUMMARY BASED ON NEWS>
    <TREND PREDICTION>
    <FEAR/GREED SCORE>
    """,
    agent = newsAnalyst
)

# Criando o Agente Analista que vai escrever a analise
stockAnalystWrite = Agent(
    role = "Senior Stock Analyst Writer",
    goal = """Analyze the trends price and write an insightful compelling and informative 3 paragraph long newsletter based on the stock report and price trend.""",
    backstory = """You're widely accepted as the best stock analyst in the market. You undertand complex concepts and create compelling stories and narratives that resonate wider audiences.
    You understand macro factors and combine multiple theories - eg. cycle theory and fundamental analyses. You're able to hold multiple opinions when analyzing.""",
    verbose = True,
    llm = llm,
    max_iter = 5,
    memory = True,
    allow_delegation = True,    
)

# Criando a tarefa do Agent Redator
writeAnalyses = Task(
    description = """Use the stock price trend and the news report to create an analyses and write the newsletter about the {ticket} company 
        that is brief and highlights the most important points.
        Focus on the stock price trend, news and fear/greed score. What are the near future considerations?
        Include the previous analyses of stock trend and news summary.""",
        expected_output = """
        - A title for the article
        - Introduction - set the overall picture and spike up the interest in one paragraph
        - A subtitle with 3 bullets executive summary
        - Another paragraph
        - Another subtitle with 3 bullets main analysis
        - Main part provies the meat of the analysis including the news summary and fear/greed scores
        - Summary - key facts concrete future trend prediction - up, down or sideways.
        """,
    agent = stockAnalystWrite,
    context = [getStockPrice, get_news]
)


# Criando o grupo de Agentes
crew = Crew(
    agents = [stockPriceAnalyst, newsAnalyst, stockAnalystWrite],
    tasks = [getStockPrice, get_news, writeAnalyses],
    verbose = True,
    process = Process.hierarchical,
    manager_llm = llm,
)


def ticker_valido(ticket: str) -> bool:
    """Confere rapidamente se o ticker existe de verdade no Yahoo Finance, ANTES de gastar
    chamadas de IA (e tempo) numa análise que não vai servir pra nada por falta de dado real."""
    try:
        dados = yf.download(ticket, period="5d", progress=False)
        return not dados.empty
    except Exception:
        return False


with st.sidebar:
    st.header('Enter the Stock to Research')

    with st.form(key='research_form'):
        topic = st.text_input("Select the ticket")
        periodo_meses = st.selectbox(
            "History period", options=[3, 6], index=0, format_func=lambda x: f"Last {x} months"
        )
        submit_button = st.form_submit_button(label = "Run research")

if submit_button:
    if not topic:
        st.error("Please fill the ticket field")
    elif not ticker_valido(topic):
        st.error(f"Couldn't find data for ticket '{topic}'. Check if the code is correct (e.g. AAPL, MSFT).")
    else:
        # A ferramenta fetch_stock_price é chamada pelo próprio agente de IA, não por este
        # código diretamente - por isso não dá pra "passar" o período escolhido como argumento
        # dela com segurança. Em vez disso, atualizamos a variável global ANTES de rodar o
        # crew, e a ferramenta lê esse valor quando for chamada.
        MESES_HISTORICO = periodo_meses

        # Um script .py rodado pelo Streamlit não tem o "event loop" do Jupyter rodando,
        # então usamos a versão síncrona normal (sem await)
        # st.spinner mostra um "carregando..." enquanto o código de dentro do "with" roda -
        # sem ele, a tela fica parada e parece travada enquanto os 3 agentes trabalham
        results = None
        with st.spinner("Agents are working on your request... this can take a few minutes"):
            try:
                results = crew.kickoff(inputs={'ticket': topic})
            except Exception as e:
                # Pega qualquer erro que aconteça DURANTE a análise (cota da API estourada,
                # falha de rede, etc) e mostra uma mensagem amigável em vez da tela de erro feia
                # padrão do Streamlit
                st.error(f"Something went wrong while running the analysis: {e}")

        if results:
            st.subheader("Results of your research")
            st.write(results.raw)