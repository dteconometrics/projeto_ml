"""Gera os gráficos dos slides sem treinar modelos nem acessar APIs.

Uso: python gerar_graficos.py [pasta_de_resultados]
Depois: quarto render apresentacao.qmd
"""
from pathlib import Path
import sys
import pandas as pd
import plotly.graph_objects as go

# ========= Dados da execução apresentada ========= #
RAIZ = Path(__file__).resolve().parent
RESULTADOS = (Path(sys.argv[1]) if len(sys.argv) > 1 else
              RAIZ.parent / 'resultados' / '20261005_155457_estacionariedade')
metricas = pd.read_csv(RESULTADOS / 'metricas.csv')
previsoes = pd.read_csv(RESULTADOS / 'previsoes_teste.csv', parse_dates=['data_alvo'])
selecionados = pd.read_csv(RESULTADOS / 'modelos_selecionados.csv').set_index('h')['modelo']
HORIZONTES = [1, 3, 6, 12]
VERMELHO, CINZA, PRETO = '#b51227', '#96999f', '#252525'

# ========= Tema dos gráficos ========= #
def tema(fig):
    fig.update_layout(
        template='plotly_white', height=440, autosize=True,
        font=dict(family='Segoe UI, Arial, sans-serif', size=19, color=PRETO),
        margin=dict(l=175, r=45, t=55, b=65),
        paper_bgcolor='white', plot_bgcolor='white',
        separators=',.',
    )
    fig.update_xaxes(gridcolor='#eeeeee', zerolinecolor='#cccccc')
    fig.update_yaxes(gridcolor='#eeeeee', zerolinecolor='#cccccc')


def menu(botoes):
    return [dict(buttons=botoes, direction='down', x=0, xanchor='left',
                 y=1.15, yanchor='top', font=dict(size=17),
                 bgcolor='white', bordercolor='#dddddd')]


# ========= Comparação de erros ========= #
rmse = go.Figure()
for h in HORIZONTES:
    dados = metricas.loc[metricas.h.eq(h)].sort_values('RMSE', ascending=False)
    rmse.add_trace(go.Bar(
        x=dados.RMSE, y=dados.modelo, orientation='h', visible=h == 1,
        marker_color=[VERMELHO if nome == selecionados[h] else CINZA for nome in dados.modelo],
        customdata=dados[['MAE']].to_numpy(),
        hovertemplate='%{y}<br>RMSE: %{x:.3f} p.p.<br>MAE: %{customdata[0]:.3f} p.p.<extra></extra>',
    ))
tema(rmse)
rmse.update_layout(showlegend=False, xaxis_title='RMSE no teste (p.p.)',
                   updatemenus=menu([dict(label=f'{h} mês' if h == 1 else f'{h} meses',
                       method='update', args=[{'visible': [v == h for v in HORIZONTES]}])
                       for h in HORIZONTES]))
rmse.update_xaxes(range=[0, float(metricas.RMSE.max()) * 1.12])

# ========= Série observada e previsões históricas ========= #
curvas = go.Figure()
for h in HORIZONTES:
    base = previsoes.loc[previsoes.h.eq(h)]
    observado = base.drop_duplicates('data_alvo').sort_values('data_alvo')
    curvas.add_trace(go.Scatter(x=observado.data_alvo, y=observado.observado,
        name='IPCA observado', mode='lines+markers', visible=h == 1,
        line=dict(color=PRETO, width=3), marker=dict(size=5)))
    for nome, cor, traco, legenda in [
        (selecionados[h], VERMELHO, 'solid', f'Selecionado: {selecionados[h]}'),
        ('Focus', CINZA, 'dash', 'Focus')]:
        dados = base.loc[base.modelo.eq(nome)].sort_values('data_alvo')
        curvas.add_trace(go.Scatter(x=dados.data_alvo, y=dados.previsto,
            name=legenda, mode='lines', visible=h == 1,
            line=dict(color=cor, width=3, dash=traco)))
tema(curvas)
curvas.update_traces(hovertemplate='%{x|%m/%Y}<br>%{y:.2f}%<extra>%{fullData.name}</extra>')
curvas.update_layout(hovermode='x unified', margin=dict(l=80, r=35, t=55, b=95),
    yaxis_title='IPCA mensal (%)',
    legend=dict(orientation='h', x=0.5, xanchor='center', y=-0.2, font=dict(size=17)),
    updatemenus=menu([dict(label=f'{h} mês' if h == 1 else f'{h} meses', method='update',
        args=[{'visible': [grupo == h for grupo in HORIZONTES for _ in range(3)]}])
        for h in HORIZONTES]))
curvas.update_xaxes(tickformat='%m/%Y', dtick='M3')

# ========= Exportação para o Quarto ========= #
destino = RAIZ / 'graficos'
destino.mkdir(exist_ok=True)
# A tabela usa os mesmos arquivos e a mesma seleção dos gráficos.
linhas = ['| Horizonte | Selecionado na validação | RMSE | Focus | Passeio aleatório |',
          '|:--|:--|--:|--:|--:|']
vitorias_focus = []
vitorias_passeio = []
for h in HORIZONTES:
    erros = metricas.loc[metricas.h.eq(h)].set_index('modelo')['RMSE']
    nome = selecionados[h]
    valores = [erros[nome], erros['Focus'], erros['Passeio aleatório']]
    numeros = ' | '.join(f'{v:.3f}'.replace('.', ',') for v in valores)
    prazo = f'{h} mês' if h == 1 else f'{h} meses'
    linhas.append(f'| {prazo} | {nome} | {numeros} |')
    if valores[0] < valores[1]:
        vitorias_focus.append(str(h))
    if valores[0] < valores[2]:
        vitorias_passeio.append(str(h))
linhas += ['', '::: {.fonte}',
           'Horizontes em que o selecionado supera o Focus: ' + (', '.join(vitorias_focus) or 'nenhum') + ' mês(es).',
           'Supera o passeio aleatório em: ' + (', '.join(vitorias_passeio) or 'nenhum') + ' mês(es).',
           ':::']
(destino / 'tabela.qmd').write_text('\n'.join(linhas) + '\n', encoding='utf-8')
for indice, (nome, figura) in enumerate([('rmse', rmse), ('previsoes', curvas)]):
    # O primeiro gráfico incorpora o Plotly para funcionar sem internet.
    html = figura.to_html(full_html=False, include_plotlyjs=indice == 0,
        div_id=f'grafico-{nome}', default_width='100%',
        config=dict(responsive=True, displaylogo=False, scrollZoom=False,
                    modeBarButtonsToRemove=['lasso2d', 'select2d']))
    html += '''<script>
    window.addEventListener('load', function () {
      function ajustar() {
        document.querySelectorAll('section.present .plotly-graph-div').forEach(function (el) {
          if (el.data) Plotly.Plots.resize(el);
        });
      }
      if (window.Reveal) {
        Reveal.on('slidechanged', ajustar);
        Reveal.on('ready', ajustar);
      }
      ajustar();
    });
    </script>'''
    (destino / f'{nome}.qmd').write_text('```{=html}\n' + html + '\n```\n', encoding='utf-8')
print('Gráficos gerados a partir de:', RESULTADOS)
