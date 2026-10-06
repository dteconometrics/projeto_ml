"""Exemplo didático adaptado da documentação oficial do Dash.

Fonte: https://dash.plotly.com/partial-properties

"""

# ========= Pacotes =========== #
from pathlib import Path
from dash import Dash, Input, Output, Patch, dcc, html
import plotly.express as px

# ========= Dados =========== #
# O Iris acompanha o Plotly: não precisamos de API nem de internet.
# Cada linha representa uma flor, com medidas em centímetros e sua espécie.
df = px.data.iris()

# ========= Gráfico inicial =========== #
# Plotly cria a figura. Dash vai exibir essa figura no navegador.
figura = px.scatter(
    df,
    x="sepal_length",
    y="sepal_width",
    color="species",
    title="Medidas das flores Iris",
    labels={
        "sepal_length": "Comprimento da sépala (cm)",
        "sepal_width": "Largura da sépala (cm)",
        "species": "Espécie",
    },
    color_discrete_sequence=["#b51227", "#566879", "#96999f"],
    template="plotly_white",
)
figura.update_layout(title_font_color="#b51227")

# ========= Aplicação =========== #
# Pasta de estilo própria para não carregar o CSS da aplicação de IPCA.
app = Dash(__name__, assets_folder=str(Path(__file__).parent / "assets_iris"))

# ========= Layout =========== #

# O layout define os componentes que aparecem na página.
# Os ids permitem que o callback encontre o botão e o gráfico.
app.layout = html.Main([
    html.H1("Como funciona uma aplicação Dash"),
    html.P("Exemplo com a base Iris, adaptado da documentação oficial."),
    html.Button("Mudar a cor do título do gráfico", id="botao-cor", n_clicks=0),
    dcc.Graph(id="grafico-iris", figure=figura),
    html.P("Clique no botão e observe o título do gráfico. Passe o mouse sobre os pontos para consultar os dados."),
])

# ========= Callback =========== #
# Input: o número de cliques do botão dispara esta função.
# Output: o retorno da função atualiza a propriedade figure do gráfico.
# prevent_initial_call=True: executamos somente depois de um clique.
@app.callback(
    Output("grafico-iris", "figure"),
    Input("botao-cor", "n_clicks"),
    prevent_initial_call=True,
)
def mudar_cor_do_titulo(numero_cliques):
    cores = ["#b51227", "#566879", "#252525"]
    nova_cor = cores[numero_cliques % len(cores)]

    # Patch altera só esta parte da figura, sem recriar os dados do gráfico.
    alteracao = Patch()
    alteracao["layout"]["title"]["font"]["color"] = nova_cor
    return alteracao

# ========= Execução =========== #
if __name__ == "__main__":
    # A porta 8051 permite abrir o exemplo junto com a Dash do IPCA (8050).
    app.run(debug=True, port=8051)
