# Publicar a Dash no Render gratuito

O código deve ficar na raiz do repositório dteconometrics/projeto_ml, com app.py, assets/, requirements.txt, render.yaml e os resultados liberados pelo .gitignore. Não envie a pasta inteira por upload sem revisar os arquivos: o upload pelo navegador não aplica o .gitignore.

## Antes de enviar ao GitHub

- Revogue a chave FRED anteriormente compartilhada. Guarde a substituta fora do repositório, em variável de ambiente.
- Revise fontes e saídas do notebook para remover credenciais e informações pessoais. Limpe as saídas da cópia destinada à publicação quando necessário.
- Não publique .env, ambientes Python, legado/, modelos.pkl ou bases brutas.
- Use o controle de versão do VS Code ou GitHub Desktop com a sua conta. Se o repositório remoto já tiver arquivos, clone-o e copie os arquivos revisados para essa cópia, preservando o conteúdo remoto. Não use push forçado.
- Confira a lista de arquivos antes do commit e do envio. A configuração atual libera três CSVs históricos de 05/10/2026 e três arquivos de projeções de 02/10/2026. As duas execuções são distintas.

## Hospedagem

1. Entre em https://dashboard.render.com/ com sua conta.
2. Selecione New > Blueprint e conecte o repositório dteconometrics/projeto_ml.
3. O Render lê render.yaml. Confira que o plano é Free antes de confirmar.
4. Aguarde o build e abra o endereço onrender.com informado pelo Render.
5. Confira as páginas Modelos, Projeções futuras, Simular carteira e Metodologia.

Alternativa manual: New > Web Service, runtime Python, build `pip install -r requirements.txt`, start `gunicorn app:server --bind 0.0.0.0:$PORT --workers 1 --threads 2 --timeout 120`, variável PYTHON_VERSION=3.11.11 e plano Free.

O app lê resultados prontos. Não treina modelos nem precisa de chave FRED para servir a Dash. Para renovar as previsões, execute o notebook localmente e atualize os arquivos publicados e as exceções do .gitignore.

O plano gratuito suspende o serviço após 15 minutos sem tráfego. A retomada pode levar cerca de um minuto. Abra o link antes da apresentação. O sistema de arquivos é temporário; não dependa de arquivos criados no servidor para guardar resultados.

Documentação: https://render.com/docs/free e https://render.com/docs/blueprint-spec
