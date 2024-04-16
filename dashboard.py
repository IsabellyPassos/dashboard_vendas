# packages
import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# O streamlit mostra os elementos em sequência de acordo como é escrito no código

# colocando Wide Mode como padrao para que os graficos respeitem o tamanho da coluna
st.set_page_config(layout="wide")

# criando funcao para formatar os valores
def formata_numero(valor, prefixo = ""):
    for unidade in ["", "mil"]:
        if valor < 1000:
            return f"{prefixo} {valor:.2f} {unidade}"
        valor /= 1000
    return f"{prefixo} {valor:.2f} milhões"

# colocando titulo no dashboard
st.title("DASHBOARD DE VENDAS :shopping_trolley:")

# lendo os dados para os gráficos via API
url = "https://labdados.com/produtos"

# criando filtros
# filtragem de regiao
regioes = ["Brasil", "Centro-Oeste", "Nordeste", "Norte", "Sudeste", "Sul"] # opcoes para o selectbox
st.sidebar.title('Filtros') # titulo para a barra lateral
regiao = st.sidebar.selectbox('Região', regioes) # criando filtro selecbox

if regiao == 'Brasil':
    regiao = ''

# filtragem dos anos
todos_anos = st.sidebar.checkbox("Dados de todo o período", value = True) # por padrao ele traz a informacao de todos os anos
if todos_anos: # caso value seja igual a False no checkbox, ele traz essa funcao
    ano = ""
else:
    ano = st.sidebar.slider("Ano", 2020, 2023)

# requerendo API
query_string = {"regiao": regiao.lower(), "ano": ano} # Passando modificações para a URL
response = requests.get(url, params = query_string) # passando parametro para carregar os filtros
dados = pd.DataFrame.from_dict(response.json()) #transformando requisicao para json e transformando json para dataframe

# formatando coluna de data para datetime
dados["Data da Compra"] = pd.to_datetime(dados["Data da Compra"], format = "%d/%m/%Y")

# criando filtro de vendedores
filtro_vendedores = st.sidebar.multiselect("Vendedores", dados["Vendedor"].unique())
if filtro_vendedores:
    dados = dados[dados["Vendedor"].isin(filtro_vendedores)]

## TABELAS: construindo tabelas para armazenar os graficos
### tabelas de receita
# criando receita por estado
receita_estados = dados.groupby("Local da compra")[["Preço"]].sum() # agrupando total da receita por estado
# criando tabela com estado, lat e long
receita_estados = dados.drop_duplicates(subset="Local da compra")[["Local da compra", "lat", "lon"]].merge(receita_estados, left_on="Local da compra", right_index=True).sort_values("Preço", ascending=False)

# criando total de vendas por mes
receita_mensal = dados.set_index("Data da Compra").groupby(pd.Grouper(freq = "ME"))["Preço"].sum().reset_index() # agrupando dados de data por mês
receita_mensal["Ano"] = receita_mensal["Data da Compra"].dt.year # armazeando data em anos
receita_mensal["Mês"] = receita_mensal["Data da Compra"].dt.month_name()

# criando receita por categoria 
receita_categoria = dados.groupby("Categoria do Produto")[["Preço"]].sum().sort_values("Preço", ascending=False)

### tabela de vendedores
# criando tabela de vendedores
vendedores = pd.DataFrame(dados.groupby("Vendedor")["Preço"].agg(["sum", "count"])) # metodo agg agrega soma e contagem ao mesmo tempo

## GRAFICOS: contruindo graficos
# grafico do mapa da receita
fig_mapa_receita = px.scatter_geo(receita_estados,
                                  lat = "lat",
                                  lon = "lon",
                                  scope = "south america",
                                  size = "Preço",
                                  template = "seaborn",
                                  hover_name = "Local da compra",
                                  hover_data = {"lat": False, "lon": False},
                                  title = "Receita por estado")

# grafico de receita mensal
fig_receita_mensal = px.line(receita_mensal,
                             x = "Mês",
                             y = "Preço",
                             markers = True, # marcador identificando mes
                             range_y = (0, receita_mensal.max()), # setando que o grafico comeca no 0 e termina no maximo da receita mensal
                             color = "Ano",
                             line_dash= "Ano", # alterando formato da linha de acordo com ano
                             title= "Receita Mensal")

fig_receita_mensal.update_layout(yaxis_title = "Receita") # altera label do eixo Y para dar um titulo a ela

# grafico receita por estado
fig_receita_estado = px.bar(receita_estados.head(),
                            x = "Local da compra",
                            y = "Preço",
                            text_auto = True, # valor em cima de cada coluna
                            title= "Ranking de estado com maior receita")

fig_receita_estado.update_layout(yaxis_title = "Receita") # altera label do eixo Y para dar um titulo a ela

# receita por cartegoria de produto
fig_receita_categoria = px.bar(receita_categoria,
                               text_auto= True,
                               title = "Receita por categoria")

fig_receita_categoria.update_layout(yaxis_title = "Receita") # altera label do eixo Y para dar um titulo a ela

## VISUALIZACAO NO STREAMLIT
# criando abas para dividir o dash em assuntos diferentes (receita, vendas, vendedores)
aba1, aba2, aba3 = st.tabs(["Receita", "Quantidade de vendas", "Vendedores"])

# aba 1
with aba1:
    # criando as colunas para melhorar a visualizacao dos kpi's
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
    # mostrando uma metrica (kpi) dentro do dashboard
        st.metric("Receita Total", formata_numero(valor=dados["Preço"].sum(), prefixo="R$")) # somando coluna de preços
        st.plotly_chart(fig_mapa_receita, use_container_width=True) # colocando o mapa na coluna1
        st.plotly_chart(fig_receita_estado, use_container_width=True)
    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(valor=dados.shape[0])) #contando o total de linhas
        st.plotly_chart(fig_receita_mensal, use_container_width=True)
        st.plotly_chart(fig_receita_categoria, use_container_width=True)

# aba 2
with aba2:
    # criando as colunas para melhorar a visualizacao dos kpi's
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
    # mostrando uma metrica (kpi) dentro do dashboard
        st.metric("Receita Total", formata_numero(valor=dados["Preço"].sum(), prefixo="R$")) # somando coluna de preços
    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(valor=dados.shape[0])) #contando o total de linhas

# aba 3
with aba3:
    # criando interativadade com o app
    qtd_vendedores = st.number_input("Quantidade de vendedores", 2, 10, 5)
    # criando as colunas para melhorar a visualizacao dos kpi's
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
    # mostrando uma metrica (kpi) dentro do dashboard
        st.metric("Receita Total", formata_numero(valor=dados["Preço"].sum(), prefixo="R$")) # somando coluna de preços
        fig_receita_vendedores = px.bar(vendedores[["sum"]].sort_values("sum", ascending=False).head(qtd_vendedores),
                                        x = "sum",
                                        y = vendedores[["sum"]].sort_values("sum", ascending=False).head(qtd_vendedores).index, # seleciona o nome dos vendedores
                                        text_auto=True,
                                        title= f"Top {qtd_vendedores} vendedores (receita)")
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric("Quantidade de vendas", formata_numero(valor=dados.shape[0])) #contando o total de linhas
        fig_vendas_vendedores = px.bar(vendedores[["count"]].sort_values("count", ascending=False).head(qtd_vendedores),
                                        x = "count",
                                        y = vendedores[["count"]].sort_values("count", ascending=False).head(qtd_vendedores).index, # seleciona o nome dos vendedores
                                        text_auto=True,
                                        title= f"Top {qtd_vendedores} vendedores (quantidade de vendas)")
        st.plotly_chart(fig_vendas_vendedores)