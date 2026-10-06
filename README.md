# IPCA Lab

## Estrutura de trabalho

- `previsao_ipca.ipynb`: coleta, tratamento, treinamento, avaliação e gráficos.
- `app.py`: toda a Dash, incluindo layout, estilo, gráficos e interações.
- `resultados/`: CSVs gerados pelo notebook, organizados por execução.
- `dados/`: dados e auxiliares da pesquisa.
- `requirements.txt`: dependências da Dash.
- `requirements-notebooks.txt`: dependências adicionais do Jupyter.

A estrutura antiga foi preservada em `legado/`. Não é necessária para abrir a Dash. A cópia `previsao_ipca_com_graficos.ipynb` também está preservada; use o notebook principal para continuar a pesquisa.

## Abrir a aplicação

No terminal, na pasta `ipca_lab`, com o ambiente Python ativado:

```powershell
python -m pip install -r requirements.txt
python app.py
```

Abra http://127.0.0.1:8050. No computador atual, o Python instalado também pode ser chamado pelo caminho `C:/Users/Usuário/anaconda3/python.exe`.

Não é necessário treinar os modelos para visualizar os resultados existentes. Ao iniciar, a aplicação lê a última pasta de `resultados/` que contenha `previsoes_teste.csv`, `metricas.csv` e `modelos_selecionados.csv`. Depois de gerar novos resultados na etapa 8 do notebook, reinicie a Dash.

## Interações

Escolha o horizonte de 1, 3, 6 ou 12 meses, os modelos que deseja comparar e a métrica do ranking (MAE ou RMSE). A tela mostra previsto versus observado, erros mensais, ranking de todos os modelos, tabela e download das previsões do horizonte. Se nenhum modelo estiver selecionado, o gráfico mantém o IPCA observado.

O modelo selecionado na validação aparece separado do líder do teste. Os erros são medidos em pontos percentuais. O alvo é o IPCA mensal futuro, não a inflação acumulada no horizonte.

## Simulador e navegação

A aplicação tem três páginas: resultados (`/`), carteira (`/simulacao`) e metodologia (`/metodologia`). Todas estão implementadas no `app.py`, incluindo o tema e a navegação lateral responsiva.

O simulador recebe capital, aporte nominal mensal, prazo, inflação anual hipotética, retorno nominal fixo, retorno real da parcela indexada e alocação. Os fatores anuais são convertidos em fatores mensais; a parcela indexada combina inflação e retorno real multiplicativamente. Há rebalanceamento mensal e aportes ao fim de cada mês. O poder de compra desconta a inflação acumulada. Para medir o ganho real, cada aporte também é descontado conforme sua data.

O gráfico de sensibilidade compara inflação 2 p.p. menor e maior, respeitando os limites de entrada. A simulação é bruta, sem custos, impostos e oscilação de preços. Usa hipóteses editáveis, não taxas de produtos nem previsões anuais derivadas dos modelos.

## Limites desta versão

São resultados históricos com dados revisados, conforme a seção 8 do notebook, não uma avaliação com todas as informações disponíveis em tempo real. A aplicação não treina modelos nem carrega os arquivos serializados. Previsões com dados novos e publicação são etapas futuras. O simulador usa um cenário anual informado pelo visitante; conectar uma trajetória futura de inflação dos modelos exige uma etapa adicional.

## Continuar a pesquisa

```powershell
python -m pip install -r requirements-notebooks.txt
python -m jupyterlab
```

Abra `previsao_ipca.ipynb`. As fontes, pacotes e tratamentos estão nas células. A coleta exige internet e algumas fontes exigem chave de API; a Dash usa apenas os resultados locais já salvos.


## Organização visual e temas

O código Python está separado por blocos `# ========= Nome da seção =========== #`.
O CSS fica em `assets/style.css`, carregado automaticamente pelo Dash.
No início de `app.py`, altere `TEMA = 'flatly'` para `lux`, `minty`, `litera`,
`darkly` ou `cyborg` e reinicie a aplicação. Bootstrap estiliza a interface;
dash-bootstrap-templates aplica o mesmo tema aos gráficos. Os estilos Bootstrap
são carregados de CDN e exigem conexão. As dependências mantêm compatibilidade
com Plotly 5 usado nesta pesquisa.


## Tratamento de estacionariedade (etapa 8)

O notebook principal e a cópia com gráficos foram atualizados e executados.
A etapa 8 contém a função `report_ndiffs`, com KPSS, ADF e Phillips–Perron em nível
e tendência, moda dos seis resultados e desempate pelo menor d. Mantém o IPCA
sem diferenciação, calcula diferenças sucessivas das demais séries, cria lags 1 e 2,
preenche somente para a frente e usa 11 dummies do mês-alvo (dezembro é referência).
Não usa imputação pela mediana. A biblioteca `arch` adapta a regra do R; isso não
garante igualdade numérica com `forecast`/`urca`.

Os testes e a padronização usam somente os dados do treino de cada divisão.
O intervalo da validação é h meses. O treino final contém apenas alvos anteriores
à primeira origem de teste. Os modelos ficam fixos nos 24 meses de teste e recebem
preditores atualizados em cada origem. O conjunto é histórico/revisado, não de
vintages completos com calendário de divulgação.

Cada pasta `_estacionariedade` inclui relatório por variável/divisão, auditoria das
datas, bases tratadas, previsões, métricas, seleção, manifesto e modelos em
`modelos.pkl`. A cópia anterior do notebook está em `legado/`.
Use o próprio notebook para repetir o treinamento. O antigo `dados/add_model_cells.py`
é da versão simplificada e não deve ser usado para reconstruir esta etapa.

Verificação: `python dados/verificar_estacionariedade.py` e
`python dados/verificar_dash.py`. Reinicie a Dash para carregar a execução nova.


## Projeções futuras e paleta sóbria

A página `/projecoes` mostra previsões diretas em 1, 3, 6 e 12 meses além do último
IPCA observado da coleta salva. A seção 10 do notebook reajusta os vencedores da
validação, congela os hiperparâmetros e usa todos os alvos disponíveis na emissão.
Não altera a avaliação histórica. Datas-base e de emissão são informadas separadamente.
Os quatro pontos não são uma trajetória mensal completa e não têm intervalos calibrados.
Os CSVs e metadados ficam em `resultados/projecoes/`; reinicie a Dash após gerar novos.
Os gráficos usam azul-acinzentado e cinzas com traços distintos. O ranking destaca
somente o modelo escolhido na validação. O simulador também segue a paleta discreta.


## Inflação acumulada projetada (atualização)

A seção 10 agora gera todos os horizontes de 1 a 12, com validação temporal para
os oito horizontes que faltavam. A aplicação exige 12 meses consecutivos e calcula
`100 * (produto(1 + taxa_mensal / 100) - 1)`. O indicador cobre os próximos 12 meses
após a data-base, não o ano-calendário. O gráfico acumulado inicia no primeiro mês
projetado. O download inclui as taxas mensais e o acumulado parcial. A composição
é um cenário pontual; não possui intervalo conjunto de previsão calibrado.
