# 🤖 Motor Autônomo de Blog & Gestão de SEO com IA

Sistema completo e autônomo para geração de conteúdo ranqueável, publicação automática no WordPress e otimização contínua baseada em dados reais do **Google Search Console** e memória vetorial (**RAG**).

Possui uma interface web moderna construída em **Streamlit** (*a Lataria*), permitindo que qualquer pessoa acompanhe KPIs de SEO, visualize oportunidades de novas pautas e configure credenciais de forma intuitiva.

---

## 🚀 Principais Recursos

- **Geração Inteligente de Conteúdo (Módulo 1):** Utiliza Google Gemini 2.5 Flash para escrever artigos formatados em HTML com boas práticas de SEO (H2/H3, FAQ, CTA, tabelas, meta description) e publica direto no WordPress via REST API.
- **Memória de Fórmulas de Sucesso (Módulo 2):** ChromaDB armazena a estrutura e tópicos dos artigos que atingiram alta performance, retroalimentando o gerador para replicar o sucesso.
- **Radar de Métricas GSC (Módulo 3):** Conexão direta com a API do Google Search Console para auditar Cliques, Impressões, CTR e Posição Média de cada post.
- **Ciclo Autônomo de Otimização (Módulo 4):** Acompanhamento em 7, 30 e 60 dias via SQLite. Posts com boa performance geram fórmulas de sucesso; posts de baixo desempenho são automaticamente reescritos com nova abordagem de SEO.
- **Radar Autônomo de Novas Pautas:** Analisa pesquisas em alta no Search Console e cruza com o histórico do blog para sugerir tópicos de alto potencial sem canibalização.
- **Dashboard Web (Streamlit):** Visualização de KPIs com gráficos Plotly, histórico de publicações e painel de configurações protegido por senha.

---

## 🛠️ Como Rodar Localmente

1. **Clone o repositório:**
   ```bash
   git clone https://github.com/SEU_USUARIO/SEU_REPOSITORIO.git
   cd SEU_REPOSITORIO
   ```

2. **Crie e ative um ambiente virtual:**
   ```bash
   python -m venv venv
   # No Windows:
   venv\Scripts\activate
   # No Linux/Mac:
   source venv/bin/activate
   ```

3. **Instale as dependências:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuração de Credenciais:**
   - Copie `.env.example` para `.env`:
     ```bash
     copy .env.example .env
     ```
   - Preencha com sua chave do Gemini, credenciais do WordPress e o arquivo JSON da conta de serviço do Google Search Console.
   - *Dica:* Você também pode preencher tudo direto pela aba **⚙️ Ajustes** no próprio dashboard!

5. **Inicie o Dashboard:**
   ```bash
   streamlit run app.py
   ```

---

## ☁️ Como Hospedar Online Gratuitamente

A forma mais simples e recomendada de hospedar este sistema é através do **[Streamlit Community Cloud](https://share.streamlit.io/)**:

1. Crie uma conta gratuita em [share.streamlit.io](https://share.streamlit.io/) usando seu login do GitHub.
2. Clique em **"New app"**.
3. Selecione o seu repositório no GitHub, a branch `main`, e defina o arquivo principal como `app.py`.
4. Clique em **"Deploy!"**.
5. Pronto! Em 1 a 2 minutos seu dashboard estará online com um link público (ou protegido por senha através do painel de ajustes).

---

## 🔒 Segurança de Credenciais

- Os arquivos `.env`, bancos de dados `.db` e credenciais `.json` do Google **estão no `.gitignore`** e nunca devem ser enviados ao GitHub público.
- Para configurar em produção ou transferir para outro usuário, basta fornecer o arquivo `.env` ou utilizar a aba de configurações da própria aplicação.
