# Apresentação em Quarto

Edite `apresentacao.qmd` para alterar o conteúdo e `tema.scss` para mudar o visual.
O logo original fica em `assets/Logo_Cin_UFPE.png`.

Na pasta da apresentação, execute:

```powershell
quarto preview apresentacao.qmd
```

Para gerar o HTML compartilhável:

```powershell
quarto render apresentacao.qmd
```

Se `quarto` não estiver no PATH, use:

```powershell
& "$env:LOCALAPPDATA/Programs/Quarto/bin/quarto.cmd" render apresentacao.qmd
```

Abra `apresentacao.html` no navegador. As setas navegam pelos slides e S abre as notas do apresentador.
O HTML incorpora os recursos para facilitar o compartilhamento.

Autoria e duração ainda precisam ser definidas. Acrescente seu nome como texto abaixo do título da capa no QMD.
Os resultados são um retrato da execução `20261005_155457_estacionariedade`. Execute `python gerar_graficos.py` para gerar a tabela e os gráficos a partir da mesma execução e depois renderize o Quarto. Os slides não se atualizam apenas ao abrir o HTML.

Referência de formato: https://quarto.org/docs/presentations/revealjs/

## Gráficos interativos

Os slides incluem comparação de RMSE e curvas de IPCA observado versus previsto.
Use o seletor para alternar entre 1, 3, 6 e 12 meses, passe o mouse para consultar valores e clique na legenda para ocultar curvas.
Os dados e o Plotly ficam incorporados ao HTML, sem depender da Dash ou de internet.

Para regenerar os gráficos da execução documentada, execute `python gerar_graficos.py` antes de renderizar o Quarto. Dependências: pandas e plotly, já usadas no projeto.
Os arquivos em `graficos/`, incluindo `tabela.qmd`, são gerados pelo script. Se mudar a execução de origem, revise também as notas, as datas e as informações de busca de hiperparâmetros no QMD.
Documentação: https://plotly.com/python/interactive-html-export/
