# Exemplo Iris para explicar o Dash

O código está em `exemplo_iris.py`. O estilo fica em `assets_iris/iris.css`.
É uma aplicação didática própria, que usa os mesmos pacotes já presentes no projeto.

## Como abrir

Na pasta `ipca_lab`, com seu ambiente Python ativo:

```powershell
python exemplo_iris.py
```

Abra http://127.0.0.1:8051. Encerre pelo terminal com Ctrl+C.
Não é necessário coletar dados nem treinar os modelos do IPCA.

## Roteiro para apresentar à turma

1. **Dados:** `px.data.iris()` carrega uma base local de 150 flores, com três espécies e medidas das pétalas e sépalas. Abra `df.head()` no console ou notebook para mostrar as colunas.
2. **Gráfico:** `px.scatter()` cria uma figura de dispersão. Cada ponto é uma flor e as cores indicam as espécies.
3. **Aplicação:** `Dash()` cria a aplicação que recebe as interações e entrega a página ao navegador.
4. **Layout:** `app.layout` organiza título, texto, botão e gráfico. `html` contém elementos HTML e `dcc` contém componentes como o gráfico.
5. **Input:** `Input("botao-cor", "n_clicks")` acompanha os cliques. Quando o valor muda, Dash executa `mudar_cor_do_titulo`.
6. **Output:** `Output("grafico-iris", "figure")` indica qual componente e propriedade receberão a atualização.
7. **Patch:** a função devolve apenas a alteração da cor do título. Os pontos e as medidas permanecem na mesma figura.
8. **Execução:** `app.run()` inicia o servidor local. `debug=True` facilita o desenvolvimento e não é a configuração de publicação.

Comece no layout e identifique os ids. Depois leia o decorator `@app.callback`, clique no botão e acompanhe a função. A cor percorre uma sequência fixa, para facilitar a demonstração.

Na aplicação de IPCA, o mesmo mecanismo conecta os seletores de horizonte e modelos aos gráficos. Neste exemplo não há treinamento de aprendizado de máquina, o objetivo é explicar a interação do Dash.

## Documentação de referência

- Exemplo Iris adaptado: https://dash.plotly.com/partial-properties, seção “Updating Title Color with a Partial Update”.
- Fundamentos de callbacks: https://dash.plotly.com/basic-callbacks.

Adaptações: textos em português, comentários por seção, cores determinísticas, CSS separado e porta 8051.
