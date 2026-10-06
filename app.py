"""Previsão do IPCA: aplicação em app.py e estilos em assets/style.css."""

# =========  Pacotes  =========== #
from pathlib import Path
import math
import pandas as pd
import json
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dcc, html
import dash_bootstrap_components as dbc
from dash_bootstrap_templates import load_figure_template


# =========  Configurações e tema  =========== #

ROOT = Path(__file__).resolve().parent

# Tema fixo: base Bootstrap clara; identidade vermelha em assets/style.css.
TEMA = 'flatly'
load_figure_template(TEMA)
DBC_CSS = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.1.1/dbc.min.css'


# =========  Leitura e validação dos resultados  =========== #

def carregar_resultados():
    arquivos = ['previsoes_teste.csv', 'metricas.csv', 'modelos_selecionados.csv']
    pastas = sorted(p for p in (ROOT / 'resultados').glob('*')
                    if p.is_dir() and all((p / a).is_file() for a in arquivos))
    if not pastas:
        raise ValueError('Execute a etapa 8 do notebook para gerar os resultados.')
    pasta = pastas[-1]
    previsoes = pd.read_csv(pasta / arquivos[0], parse_dates=['data_alvo'])
    metricas = pd.read_csv(pasta / arquivos[1])
    selecionados = pd.read_csv(pasta / arquivos[2])
    if previsoes.empty or metricas.empty or selecionados.empty:
        raise ValueError('Os arquivos de resultados estão vazios.')
    if previsoes.duplicated(['h', 'modelo', 'data_alvo']).any():
        raise ValueError('Há previsões duplicadas nos resultados.')
    if previsoes[['observado', 'previsto']].isna().any().any():
        raise ValueError('Há valores ausentes nas previsões.')
    previsoes['erro'] = previsoes['previsto'] - previsoes['observado']
    return pasta, previsoes, metricas, selecionados


# =========  Inicialização da aplicação  =========== #

app = Dash(__name__, title='Predição do IPCA',
           assets_folder=str(ROOT / 'assets'),
           external_stylesheets=[dbc.themes.FLATLY, DBC_CSS])
server = app.server
# Estilos personalizados: assets/style.css (carregado automaticamente pelo Dash).


# =========  Dados da aplicação  =========== #

erro_carga = None
try:
    PASTA, PREVISOES, METRICAS, SELECIONADOS = carregar_resultados()
except (OSError, ValueError, KeyError) as exc:
    erro_carga = str(exc)

# =========  Layout dos resultados  =========== #

if erro_carga:
    app.layout = html.Main([html.H1('Predição do IPCA'), html.H2('Resultados indisponíveis'), html.P(erro_carga)], className='shell')
else:
    HORIZONTES = sorted(PREVISOES['h'].unique())
    MODELOS = sorted(PREVISOES['modelo'].unique())
    PALETA = ['#b5122b', '#70676b', '#a68b91', '#713343', '#92888d', '#bbb0b4', '#493c42', '#bc737f']
    CORES = dict(zip(MODELOS, PALETA))
    TRACOS = dict(zip(MODELOS, ['solid', 'dash', 'dot', 'dashdot', 'longdash', 'longdashdot', 'solid', 'dot']))
    primeiro_h = int(HORIZONTES[0])
    primeiro_modelo = SELECIONADOS.loc[SELECIONADOS['h'] == primeiro_h, 'modelo'].iloc[0]
    app.layout = html.Main([
        html.Header([html.H1('Predição do IPCA'), html.P('Explore os resultados históricos dos modelos de inflação.')]),
        html.Div('Alvo: IPCA mensal. O horizonte indica quantos meses à frente se prevê esse valor; não é inflação acumulada.', className='notice'),
        html.Div([
            html.Div([html.Label('Horizonte', htmlFor='horizonte'), dcc.Dropdown(id='horizonte', options=[{'label': f'{h} mês(es) à frente', 'value': int(h)} for h in HORIZONTES], value=primeiro_h, clearable=False)], className='control'),
            html.Div([html.Label('Modelos no gráfico', htmlFor='modelos'), dcc.Dropdown(id='modelos', options=MODELOS, value=[primeiro_modelo, 'Focus'], multi=True)], className='control'),
            html.Div([html.Label('Métrica do ranking', htmlFor='metrica'), dcc.Dropdown(id='metrica', options=['RMSE', 'MAE'], value='RMSE', clearable=False)], className='control'),
        ], className='controls'),
        html.Div(id='resumo', className='cards'),
        html.Section([html.H2('Previsto versus observado'), dcc.Graph(id='serie')], className='panel'),
        html.Div([
            html.Section([html.H2('Comparação de todos os modelos'), html.P('Destaque: modelo escolhido na validação.'), dcc.Graph(id='ranking')], className='panel'),
            html.Section([html.H2('Erros ao longo do tempo'), html.P('Previsto − observado: positivo indica superestimação.'), dcc.Graph(id='erros')], className='panel'),
        ], className='two'),
        html.Section([html.H2('Resultados por modelo'), html.Div(id='tabela', className='table-wrap'), html.Br(), html.Button('Baixar previsões deste horizonte', id='baixar'), dcc.Download(id='download')], className='panel'),
        html.Section([html.H2('Como interpretar'),
            html.P('MAE e RMSE são erros em pontos percentuais; menor é melhor. O RMSE dá mais peso aos erros grandes. O modelo selecionado foi escolhido na validação; o líder do teste é uma comparação posterior.'),
            html.P('A avaliação usa dados históricos revisados e as divisões da seção 8 do notebook. Não representa uma simulação com todas as informações disponíveis em tempo real. Lasso Adaptativo e CSR reduzido seguem as implementações didáticas do notebook.'),
            html.P('Previsões futuras e simulação de carteira ainda não estão conectadas. Os resultados exibidos são históricos.')], className='panel'),
        html.Footer(f'Execução: {PASTA.name} · Reinicie a aplicação após gerar novos resultados no notebook.'),
    ], className='shell dbc')


# =========  Gráficos e tabela dos modelos  =========== #

def atualizar(h, modelos, metrica):
    dados = PREVISOES[PREVISOES['h'] == h].sort_values('data_alvo')
    avaliacao = METRICAS[METRICAS['h'] == h].sort_values(metrica)
    escolhido = SELECIONADOS.loc[SELECIONADOS['h'] == h, 'modelo'].iloc[0]
    observados = dados.drop_duplicates('data_alvo')
    periodo = f'{dados.data_alvo.min():%m/%Y} a {dados.data_alvo.max():%m/%Y}'
    def card(titulo, valor):
        return html.Div([html.Div(titulo), html.Div(valor, className='value')], className='card')
    resumo = [card('Selecionado na validação', escolhido), card(f'Menor {metrica} no teste', avaliacao.iloc[0]['modelo']), card('Meses avaliados', str(len(observados))), card('Período do teste', periodo)]
    serie = go.Figure(go.Scatter(x=observados.data_alvo, y=observados.observado, name='IPCA observado', line={'color': '#302a2d', 'width': 3}))
    erros = go.Figure()
    for nome in modelos or []:
        parte = dados[dados['modelo'] == nome]
        serie.add_scatter(x=parte.data_alvo, y=parte.previsto, name=nome, line={'color': CORES[nome], 'dash': TRACOS[nome], 'width': 2})
        erros.add_scatter(x=parte.data_alvo, y=parte.erro, name=nome, line={'color': CORES[nome], 'dash': TRACOS[nome], 'width': 2})
    erros.add_hline(y=0, line_color='#142d40')
    ranking = go.Figure(go.Bar(x=avaliacao[metrica], y=avaliacao['modelo'], orientation='h',
        marker_color=['#b5122b' if m == escolhido else '#c6bec2' for m in avaliacao['modelo']],
        text=avaliacao[metrica]))
    ranking.update_traces(texttemplate='%{text:.3f}', textposition='outside', cliponaxis=False)
    ranking.update_yaxes(autorange='reversed', title=None)
    ranking.update_layout(showlegend=False, xaxis_title=f'{metrica} (p.p.)')
    for fig in [serie, erros, ranking]:
        fig.update_layout(template=TEMA, margin=dict(l=20, r=30, t=20, b=30), legend=dict(orientation='h', y=-.25))
        estilo_figura(fig)
    serie.update_layout(yaxis_title='IPCA mensal (%)', hovermode='x unified')
    erros.update_layout(yaxis_title='Erro (p.p.)')
    cabecalho = html.Thead(html.Tr([html.Th(v) for v in ['Modelo', 'MAE (p.p.)', 'RMSE (p.p.)', 'Meses', 'Validação']]))
    linhas = [html.Tr([html.Td(r.modelo), html.Td(f'{r.MAE:.4f}'), html.Td(f'{r.RMSE:.4f}'), html.Td(int(r.n)), html.Td('Selecionado' if r.modelo == escolhido else '—')]) for r in avaliacao.itertuples()]
    return resumo, serie, ranking, erros, html.Table([cabecalho, html.Tbody(linhas)])


# =========  Callbacks dos resultados e download  =========== #

if not erro_carga:
    app.callback(Output('resumo', 'children'), Output('serie', 'figure'), Output('ranking', 'figure'), Output('erros', 'figure'), Output('tabela', 'children'), Input('horizonte', 'value'), Input('modelos', 'value'), Input('metrica', 'value'))(atualizar)

    @app.callback(Output('download', 'data'), Input('baixar', 'n_clicks'), State('horizonte', 'value'), prevent_initial_call=True)
    def baixar(n_clicks, h):
        return dcc.send_data_frame(PREVISOES[PREVISOES['h'] == h].to_csv, f'previsoes_ipca_h{h}.csv', index=False)


# =========  Formatação e cálculo da simulação  =========== #


def moeda(valor):
    return 'R$ ' + f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')


def simular(capital, aporte, meses, inflacao, taxa_fixa, taxa_real, peso):
    """Taxas anuais efetivas; aporte nominal ao fim de cada mês; rebalanceamento mensal."""
    valores = [capital, aporte, meses, inflacao, taxa_fixa, taxa_real, peso]
    if any(v is None or not math.isfinite(float(v)) for v in valores):
        raise ValueError('Preencha todos os campos com números válidos.')
    if not (0 <= capital <= 1e9 and 0 <= aporte <= 1e7 and 1 <= meses <= 360 and int(meses) == meses):
        raise ValueError('Informe capital até R$ 1 bilhão, aporte até R$ 10 milhões e prazo inteiro entre 1 e 360 meses.')
    if not (-20 <= inflacao <= 100 and -50 <= taxa_fixa <= 100 and -20 <= taxa_real <= 50 and 0 <= peso <= 100):
        raise ValueError('Confira as taxas e o peso: use valores dentro dos limites dos campos.')
    fator_inflacao = (1 + inflacao / 100) ** (1 / 12)
    fator_fixo = (1 + taxa_fixa / 100) ** (1 / 12)
    fator_indexado = fator_inflacao * (1 + taxa_real / 100) ** (1 / 12)
    fator_carteira = peso / 100 * fator_fixo + (1 - peso / 100) * fator_indexado
    saldo = capital
    contribuicoes_reais = capital
    registros = [{'Mês': 0, 'Saldo nominal': saldo, 'Poder de compra': saldo,
                  'Total aportado nominal': capital, 'Aportes em reais de hoje': capital}]
    for mes in range(1, int(meses) + 1):
        saldo = saldo * fator_carteira + aporte
        indice = fator_inflacao ** mes
        contribuicoes_reais += aporte / indice
        registros.append({'Mês': mes, 'Saldo nominal': saldo, 'Poder de compra': saldo / indice,
                         'Total aportado nominal': capital + aporte * mes,
                         'Aportes em reais de hoje': contribuicoes_reais})
    return pd.DataFrame(registros)


# =========  Componentes reutilizáveis  =========== #

def campo(titulo, ident, valor, minimo, maximo, passo=1):
    return html.Div([html.Label(titulo, htmlFor=ident), dcc.Input(id=ident, type='number', value=valor,
        min=minimo, max=maximo, step=passo, debounce=True, className='sim-input')])


# =========  Tema dos gráficos  =========== #

def estilo_figura(fig):
    # Gráficos claros com destaques vermelhos e comparações neutras.
    fig.update_layout(template=TEMA, paper_bgcolor='white', plot_bgcolor='white',
        font=dict(color='#302a2d'), hoverlabel=dict(bgcolor='white', font_color='#302a2d'),
        margin=dict(l=20, r=30, t=25, b=40),
        colorway=['#b5122b', '#81767c', '#b5adb1'],
        legend=dict(orientation='h', y=-.22))
    fig.update_xaxes(gridcolor='#eee8eb', zeroline=False)
    fig.update_yaxes(gridcolor='#eee8eb', zeroline=False)
    return fig



# =========  Projeções futuras: leitura e visualização  =========== #

def carregar_projecoes():
    pastas = sorted(p for p in (ROOT / 'resultados/projecoes').glob('*')
                    if all((p / nome).is_file() for nome in ['previsoes_futuras.csv', 'historico.csv', 'manifesto.json']))
    if not pastas:
        return None
    pasta = pastas[-1]
    previsoes = pd.read_csv(pasta / 'previsoes_futuras.csv', parse_dates=['data_origem', 'data_alvo'])
    historico = pd.read_csv(pasta / 'historico.csv', parse_dates=['date'])
    info = json.loads((pasta / 'manifesto.json').read_text(encoding='utf-8'))
    if previsoes.empty or not (previsoes.data_alvo > historico.date.max()).all():
        raise ValueError('As projeções devem avançar além do último observado.')
    if previsoes[['h', 'previsto']].isna().any().any() or previsoes.h.duplicated().any():
        raise ValueError('Projeções incompletas ou duplicadas.')
    # Exige 12 meses consecutivos antes de compor o acumulado anual.
    previsoes = previsoes.sort_values('h').copy()
    meses = pd.date_range(historico.date.max() + pd.DateOffset(months=1), periods=12, freq='MS')
    if previsoes['h'].tolist() != list(range(1, 13)) or previsoes['data_alvo'].tolist() != meses.tolist():
        raise ValueError('Gere as 12 previsões mensais na seção 10 para calcular a inflação acumulada.')
    if not previsoes['previsto'].map(math.isfinite).all() or (previsoes['previsto'] <= -100).any():
        raise ValueError('As taxas mensais precisam ser finitas e maiores que -100%.')
    previsoes['acumulado_periodo'] = ((1 + previsoes['previsto'] / 100).cumprod() - 1) * 100
    return pasta, previsoes.sort_values('data_alvo'), historico.sort_values('date'), info


def layout_projecoes():
    cabecalho = html.Header([html.P('PROJEÇÕES / INFLAÇÃO EM 12 MESES', className='eyebrow'),
        html.H1('Inflação nos próximos 12 meses'),
        html.P('A trajetória mensal projetada e seu efeito acumulado ao longo de um ano.')])
    try:
        carregado = carregar_projecoes()
    except (ValueError, OSError, KeyError) as exc:
        return html.Div([cabecalho, html.Div(str(exc), className='notice')])
    if carregado is None:
        return html.Div([cabecalho, html.P('Execute a seção 10 do notebook para gerar as projeções.')])
    pasta, futuro, historico, info = carregado
    ultimo = historico.date.max()
    grafico = go.Figure()
    recente = historico.tail(24)
    grafico.add_scatter(x=recente.date, y=recente.ipca, name='IPCA observado',
        mode='lines', line=dict(color='#75889a', width=2))
    grafico.add_scatter(x=futuro.data_alvo, y=futuro.previsto, name='IPCA mensal projetado',
        mode='lines+markers', line=dict(color='#b5122b', width=2, dash='dash'),
        marker=dict(color='#b5122b', size=6),
        customdata=futuro[['modelo', 'h']].to_numpy(),
        hovertemplate='%{x|%m/%Y}<br>IPCA: %{y:.3f}%<br>%{customdata[0]} · h=%{customdata[1]}<extra></extra>')
    grafico.add_shape(type='line', x0=ultimo, x1=ultimo, y0=0, y1=1,
        xref='x', yref='paper', line=dict(color='#9aa6b2', dash='dot', width=1))
    grafico.add_annotation(x=ultimo, y=1, xref='x', yref='paper', text='Último observado',
        showarrow=False, yshift=15, font=dict(size=10, color='#75889a'))
    grafico.update_layout(yaxis_title='IPCA mensal (%)', xaxis_title=None, hovermode='closest')
    estilo_figura(grafico)
    grafico.update_xaxes(dtick='M3', tickformat='%m/%Y')
    inicio_mes_atual = pd.Timestamp.now(tz='America/Sao_Paulo').tz_localize(None).to_period('M').to_timestamp()
    acumulada = float(futuro['acumulado_periodo'].iloc[-1])
    periodo = f'{futuro.data_alvo.min():%m/%Y} a {futuro.data_alvo.max():%m/%Y}'
    cards = [
        html.Div([html.Div('Inflação acumulada projetada'),
            html.Div(f'{acumulada:.2f}%'.replace('.', ','), className='value'),
            html.P('Composição das 12 taxas mensais')], className='card'),
        html.Div([html.Div('Período projetado'), html.Div(periodo, className='value'),
            html.P('12 meses após o último observado')], className='card'),
        html.Div([html.Div('IPCA mensal no último horizonte'),
            html.Div(f'{futuro.previsto.iloc[-1]:.2f}%'.replace('.', ','), className='value'),
            html.P(f'{futuro.data_alvo.max():%m/%Y} — taxa mensal, não anual')], className='card'),
    ]
    curva_acumulada = go.Figure(go.Scatter(x=futuro.data_alvo, y=futuro.acumulado_periodo,
        mode='lines+markers', name='Acumulado desde o primeiro mês projetado',
        line=dict(color='#b5122b', width=2), marker=dict(size=5),
        hovertemplate='%{x|%m/%Y}<br>Acumulado: %{y:.3f}%<extra></extra>'))
    curva_acumulada.update_layout(yaxis_title='Acumulado projetado (%)', xaxis_title=None)
    estilo_figura(curva_acumulada)
    curva_acumulada.update_xaxes(dtick='M1', tickformat='%m/%Y')
    tabela = html.Table([html.Thead(html.Tr([html.Th(v) for v in ['Mês previsto', 'Horizonte', 'Modelo', 'IPCA mensal', 'Acumulado no período', 'Referência temporal']])),
        html.Tbody([html.Tr([html.Td(f'{r.data_alvo:%m/%Y}'), html.Td(f'{r.h} meses'), html.Td(r.modelo),
            html.Td(f'{r.previsto:.3f}%'.replace('.', ',')),
            html.Td(f'{r.acumulado_periodo:.3f}%'.replace('.', ',')),
            html.Td('Mês encerrado; sem observado na base' if r.data_alvo < inicio_mes_atual else 'Mês atual ou futuro')])
            for r in futuro.itertuples()])])
    return html.Div([cabecalho,
        html.Div(f'Base até {ultimo:%m/%Y} · Emissão em {pd.Timestamp(info["emissao"]):%d/%m/%Y}. '
            'As projeções usam a coleta salva, que pode estar defasada em relação à data de hoje.', className='notice'),
        html.Div(cards, className='cards'),
        html.Section([html.H2('Histórico e previsões mensais'), dcc.Graph(figure=grafico, id='grafico-futuro'),
            html.P('Cada ponto corresponde a uma previsão mensal direta. A linha tracejada liga os 12 meses previstos; não há interpolação de horizontes faltantes nem bandas de confiança calibradas.')], className='panel'),
        html.Section([html.H2('Inflação acumulada projetada'), dcc.Graph(figure=curva_acumulada, id='grafico-acumulado'),
            html.P('Acúmulo desde o primeiro mês projetado: produto de (1 + taxa mensal / 100), menos 1. Não é uma soma das taxas nem o acumulado do ano-calendário.')], className='panel'),
        html.Section([html.H2('Detalhamento das projeções'), html.Div(tabela, className='table-wrap'),
            html.Br(), html.Button('Baixar projeções', id='baixar-futuro'), dcc.Download(id='download-futuro')], className='panel'),
        html.Div('Modelos e hiperparâmetros escolhidos na validação histórica, reajustados com os alvos já observados da base mais recente. '
            'O acumulado combina as 12 previsões mensais e representa um cenário central, sem intervalo de incerteza conjunta calibrado. Não é uma reconstrução do que era conhecido na data-base.', className='notice'),
        html.Footer(f'Projeções: {pasta.name} · Seleção histórica: {info["avaliacao"]}'),
    ])


# =========  Layout das páginas e navegação  =========== #

if not erro_carga:
    pagina_resultados = app.layout
    # As notas metodológicas ganham sua própria página.
    pagina_resultados.children = pagina_resultados.children[:-2]
    pagina_resultados.children[0] = html.Header([html.P('PESQUISA / AVALIAÇÃO', className='eyebrow'),
        html.H1('Modelos'), html.P('Compare previsões, entenda os erros e explore cada horizonte.')])
    pagina_simulacao = html.Div([
        html.Header([html.P('EXPERIMENTO / PODER DE COMPRA', className='eyebrow'), html.H1('O valor do dinheiro no tempo'),
            html.P('Monte uma carteira hipotética e descubra como a inflação muda o resultado.')]),
        html.Div([
            html.Aside([html.H2('Seu cenário'),
                campo('Capital inicial (R$)', 'sim-capital', 10000, 0, 1e9, 100),
                campo('Aporte mensal (R$)', 'sim-aporte', 500, 0, 1e7, 50),
                campo('Prazo (meses)', 'sim-meses', 24, 1, 360),
                campo('Inflação anual hipotética (%)', 'sim-inflacao', 4.5, -20, 100, .1),
                campo('Retorno nominal fixo (% ao ano)', 'sim-fixa', 10, -50, 100, .1),
                campo('Retorno acima da inflação (% ao ano)', 'sim-real', 5, -20, 50, .1),
                html.Label('Peso da parcela nominal fixa (%)', htmlFor='sim-peso'),
                dcc.Slider(id='sim-peso', min=0, max=100, step=5, value=50,
                    marks={0: '0%', 50: '50%', 100: '100%'}, tooltip={'placement': 'bottom', 'always_visible': True}),
                html.P('O restante é aplicado à parcela indexada à inflação.'),
            ], className='panel'),
            html.Div([html.Div(id='sim-erro', className='error', role='status'), html.Div(id='sim-cards', className='cards'),
                html.Section([html.H2('1. Como interpretar seu resultado'),
                    html.Div(id='sim-leitura', role='status')], className='panel'),
                html.Section([html.H2('2. De onde vem o saldo?'),
                    html.P('Aportes são o dinheiro que você colocou. Rendimentos são a diferença entre o saldo final e esses aportes, em valores nominais.'),
                    dcc.Graph(id='sim-composicao')], className='panel'),
                html.Section([html.H2('3. O que acontece com os preços?'),
                    html.P('Acompanhe uma cesta que custa R$ 100 hoje. A quantidade de produtos permanece igual; o preço acompanha a inflação informada.'),
                    dcc.Graph(id='sim-precos')], className='panel'),
                html.Section([html.H2('4. Saldo e poder de compra'),
                    html.P('A linha nominal mostra os reais no saldo. A linha real converte esse saldo para o poder de compra de hoje. A linha pontilhada soma os aportes nominais; use o ganho real acima para comparar valores na mesma referência de preços.'),
                    dcc.Graph(id='sim-trajetoria')], className='panel'),
                html.Section([html.H2('E se a inflação mudar?'), html.P('Mesmo capital, aportes, prazo e alocação. A inflação varia 2 pontos percentuais para baixo e para cima, dentro dos limites de −20% a 100%.'),
                    dcc.Graph(id='sim-cenarios')], className='panel'),
                html.Div('Cenário educativo com taxas constantes, aportes no fim do mês e rebalanceamento mensal. Valores brutos, sem impostos, custos ou oscilação de preços. As taxas são hipóteses editáveis, não cotações de produtos.', className='notice'),
                html.Section([html.H2('Experimente e explique para a turma'), html.Ol([
                    html.Li('Coloque a inflação em 0%. O saldo nominal e o poder de compra ficam iguais.'),
                    html.Li('Use 100% na parcela nominal fixa. Iguale o retorno fixo à inflação e coloque o aporte em zero: o poder de compra do capital inicial fica constante.'),
                    html.Li('Ainda com 100% na parcela fixa, aumente a inflação acima do retorno. O saldo pode crescer enquanto o poder de compra diminui.'),
                    html.Li('Passe o peso da parcela fixa para 0%. A parcela indexada acompanha a inflação mais o retorno real informado; compare o resultado.')
                ])], className='panel'),
            ]),
        ], className='sim-grid'),
    ])
    pagina_metodo = html.Div([
        html.P('TRANSPARÊNCIA / METODOLOGIA', className='eyebrow'), html.H1('Da pesquisa à interpretação'),
        html.Section([html.H2('01 · O que os modelos preveem'), html.P('O alvo é o IPCA mensal em um mês futuro. Horizontes de 1, 3, 6 e 12 meses não correspondem a inflação acumulada nesses períodos.'),
            html.H2('02 · Como ler os resultados'), html.P('MAE e RMSE medem erros em pontos percentuais. Menor é melhor. A escolha do modelo vem da validação; o ranking do teste é descritivo. A avaliação usa dados revisados e as divisões da seção 8 do notebook, não um histórico completo das informações disponíveis em cada data.'),
            html.H2('03 · Como funciona a carteira'), html.P('Uma parcela recebe um retorno nominal fixo hipotético. A outra acompanha a inflação mais um retorno real, compostos multiplicativamente. As taxas anuais efetivas são convertidas em fatores mensais. A carteira é rebalanceada mensalmente e recebe o aporte ao fim de cada mês.'),
            html.P('Saldo real = saldo nominal ÷ inflação acumulada. O ganho real desconta também cada aporte para reais de hoje, respeitando sua data. A sensibilidade recalcula a carteira para três cenários de inflação.'),
            html.H2('04 · Relação com os modelos'), html.P('O simulador utiliza uma hipótese anual informada por você. Não convertemos uma previsão mensal isolada em inflação anual nem tratamos resultados históricos como previsões futuras. A página Projeções futuras estima os 12 meses seguintes e compõe as taxas para obter a inflação acumulada projetada. O simulador continua usando sua hipótese anual editável, sem substituição automática pela projeção.'),
            html.H2('05 · Fonte dos resultados'), html.P(f'Execução {PASTA.name}. Os CSVs são lidos ao iniciar a aplicação. Reinicie a Dash após gerar novos resultados no notebook. Lasso Adaptativo e CSR reduzido seguem as implementações didáticas da pesquisa.'),
        ], className='panel explanation'),
    ])
    app.layout = html.Div([
        dcc.Location(id='url', refresh=False),
        html.Aside([html.Div(['Previsão do IPCA'], className='brand'),
            html.Div('Inflação', className='brand-caption'),
            html.Nav([dcc.Link('01   Visão dos modelos', href='/', id='nav-modelos'),
                      dcc.Link('02   Projeções futuras', href='/projecoes', id='nav-futuro'),
                      dcc.Link('03   Simular carteira', href='/simulacao', id='nav-simulacao'),
                      dcc.Link('04   Metodologia', href='/metodologia', id='nav-metodo')]),
            html.Div([html.Div('● DADOS DA PESQUISA', className='status-dot'),
                html.Div('Python · Machine learning'), html.Div('Aplicações de ML')], className='sidebar-bottom'),
        ], className='sidebar'),
        html.Main([html.Div([html.Span('OBSERVATÓRIO DE INFLAÇÃO'), html.Span('AMBIENTE DE PESQUISA', className='badge')], className='topbar'),
            html.Div(pagina_resultados, id='pagina-resultados'),
            html.Div(layout_projecoes(), id='pagina-futuro', style={'display': 'none'}),
            html.Div(pagina_simulacao, id='pagina-simulacao', style={'display': 'none'}),
            html.Div(pagina_metodo, id='pagina-metodo', style={'display': 'none'}),
            html.Div([html.H1('Página não encontrada'), dcc.Link('Voltar aos modelos', href='/')], id='pagina-404', style={'display': 'none'}),
        ], className='workspace'),
    ], className='dbc')


# =========  Callbacks  =========== #

   
    # =========  Callback de navegação  =========== #

    @app.callback(Output('pagina-resultados', 'style'), Output('pagina-simulacao', 'style'),
        Output('pagina-metodo', 'style'), Output('pagina-404', 'style'),
        Output('nav-modelos', 'className'), Output('nav-simulacao', 'className'), Output('nav-metodo', 'className'), Input('url', 'pathname'))
    def navegar(caminho):
        indice = {'/': 0, '/simulacao': 1, '/metodologia': 2, '/projecoes': 4}.get(caminho or '/', 3)
        return tuple([{'display': 'block' if i == indice else 'none'} for i in range(4)] +
                     ['active' if i == indice else '' for i in range(3)])

   
    # =========  Callback da simulação  =========== #

    @app.callback(Output('sim-cards', 'children'), Output('sim-trajetoria', 'figure'),
        Output('sim-cenarios', 'figure'), Output('sim-erro', 'children'),
        *[Input('sim-' + nome, 'value') for nome in ['capital', 'aporte', 'meses', 'inflacao', 'fixa', 'real', 'peso']])
    def atualizar_simulacao(capital, aporte, meses, inflacao, fixa, real, peso):
        try:
            df = simular(capital, aporte, meses, inflacao, fixa, real, peso)
            final = df.iloc[-1]
            cards = [html.Div([html.Div(titulo), html.Div(moeda(valor), className='value')], className='card')
                for titulo, valor in [('Saldo nominal final', final['Saldo nominal']),
                                     ('Em poder de compra de hoje', final['Poder de compra']),
                                     ('Ganho real sobre aportes', final['Poder de compra'] - final['Aportes em reais de hoje'])]]
            trajetoria = go.Figure()
            for coluna, cor, tracejado in [('Saldo nominal', '#b5122b', 'solid'), ('Poder de compra', '#81767c', 'solid'), ('Total aportado nominal', '#b5adb1', 'dot')]:
                trajetoria.add_scatter(x=df['Mês'], y=df[coluna], name=coluna, line=dict(color=cor, width=3, dash=tracejado))
            trajetoria.update_layout(xaxis_title='Meses', yaxis_title='Valor (R$)', hovermode='x unified')
            cenarios = go.Figure()
            taxas = [max(-20, inflacao - 2), inflacao, min(100, inflacao + 2)]
            rotulos = [f'{nome} · {taxa:g}% a.a.' for nome, taxa in zip(['Menor inflação', 'Seu cenário', 'Maior inflação'], taxas)]
            finais = [simular(capital, aporte, meses, taxa, fixa, real, peso).iloc[-1] for taxa in taxas]
            for coluna, cor in [('Saldo nominal', '#b5122b'), ('Poder de compra', '#81767c')]:
                cenarios.add_bar(x=rotulos, y=[f[coluna] for f in finais], name=coluna, marker_color=cor)
            cenarios.update_layout(barmode='group', yaxis_title='Valor final (R$)')
            return cards, estilo_figura(trajetoria), estilo_figura(cenarios), ''
        except (ValueError, TypeError) as exc:
            vazio = estilo_figura(go.Figure())
            return [], vazio, vazio, str(exc)



    # =========  Explicação didática da carteira  =========== #

    @app.callback(Output('sim-leitura', 'children'), Output('sim-composicao', 'figure'),
        Output('sim-precos', 'figure'),
        *[Input('sim-' + nome, 'value') for nome in ['capital', 'aporte', 'meses', 'inflacao', 'fixa', 'real', 'peso']])
    def explicar_carteira(capital, aporte, meses, inflacao, fixa, real, peso):
        try:
            dados = simular(capital, aporte, meses, inflacao, fixa, real, peso)
            fim = dados.iloc[-1]
            indice = (1 + inflacao / 100) ** (int(meses) / 12)
            total = fim['Total aportado nominal']
            rendimento = fim['Saldo nominal'] - total
            ganho_real = fim['Poder de compra'] - fim['Aportes em reais de hoje']
            leitura = [
                html.P(f"Você colocou {moeda(total)}: {moeda(capital)} no início e {int(meses)} aportes de {moeda(aporte)}."),
                html.P(f"O saldo final é {moeda(fim['Saldo nominal'])}. A diferença nominal entre o saldo e o total aportado é {moeda(rendimento)}."),
                html.P(f"Nesse período, a inflação acumulada é {(indice - 1) * 100:.2f}%. Uma cesta de R$ 100 passa a custar {moeda(100 * indice)}."),
                html.P(f"Convertendo o saldo final para os preços de hoje: {moeda(fim['Saldo nominal'])} ÷ {indice:.4f} = {moeda(fim['Poder de compra'])}."),
                html.P('Essa conversão mede poder de compra; a diferença entre nominal e real não é uma cobrança descontada da conta.'),
                html.P(f"Seus aportes, cada um convertido pelos preços de sua data, somam {moeda(fim['Aportes em reais de hoje'])} em reais de hoje. O ganho real sobre esses aportes é {moeda(ganho_real)}."),
                html.P('A parcela indexada tem retorno nominal que acompanha a inflação neste modelo. Por isso, nos cenários abaixo, tanto os preços quanto o rendimento dessa parcela mudam.'),
            ]
            composicao = go.Figure(go.Waterfall(
                x=['Capital inicial', 'Aportes mensais', 'Rendimentos nominais', 'Saldo final'],
                y=[capital, aporte * int(meses), rendimento, 0],
                measure=['absolute', 'relative', 'relative', 'total'],
                increasing={'marker': {'color': '#75889a'}},
                decreasing={'marker': {'color': '#a45460'}},
                totals={'marker': {'color': '#b5122b'}},
                connector={'line': {'color': '#a0a29d'}},
            ))
            composicao.update_layout(yaxis_title='Valores nominais (R$)', showlegend=False)
            indices = [(1 + inflacao / 100) ** (m / 12) for m in dados['Mês']]
            precos = go.Figure()
            precos.add_scatter(x=dados['Mês'], y=[100 * v for v in indices],
                name='Preço da mesma cesta', line={'color': '#b5122b', 'width': 3})
            precos.add_scatter(x=dados['Mês'], y=[100] * len(dados),
                name='Preço de hoje', line={'color': '#a0a29d', 'dash': 'dot'})
            precos.update_layout(xaxis_title='Meses', yaxis_title='Preço da cesta (R$)', hovermode='x unified')
            return leitura, estilo_figura(composicao), estilo_figura(precos)
        except (ValueError, TypeError):
            return html.P('Preencha os campos com valores válidos para ver a explicação.'), estilo_figura(go.Figure()), estilo_figura(go.Figure())

    # =========  Callbacks das projeções  =========== #

    @app.callback(Output('pagina-futuro', 'style'), Output('nav-futuro', 'className'), Input('url', 'pathname'))
    def navegar_futuro(caminho):
        ativo = caminho == '/projecoes'
        return {'display': 'block' if ativo else 'none'}, 'active' if ativo else ''

    @app.callback(Output('download-futuro', 'data'), Input('baixar-futuro', 'n_clicks'), prevent_initial_call=True)
    def baixar_futuro(n_clicks):
        carregado = carregar_projecoes()
        if carregado is None:
            from dash import no_update
            return no_update
        return dcc.send_data_frame(carregado[1].to_csv, 'ipca_mensal_e_acumulado_12_meses.csv', index=False)


# =========  Run Server   =========== #

# =========  Execução  =========== #

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8050, debug=False)
