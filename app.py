import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import json
import shutil
from dotenv import load_dotenv, set_key

# Importações dos nossos módulos do robô
import modulo3
import modulo4
import gerador_pautas

# Configuração da página
st.set_page_config(page_title="Dashboard IA - Seguro Estagiário", layout="wide", page_icon="🤖")

# -------------------------------------------------------
# INJEÇÃO DE SECRETS DO STREAMLIT CLOUD
# Quando o app está hospedado na nuvem, lê as chaves dos
# Streamlit Secrets (configurados no painel do Streamlit Cloud)
# e injeta em os.environ ANTES de qualquer outro módulo usar.
# -------------------------------------------------------
def injetar_streamlit_secrets():
    """Lê os Streamlit Secrets e injeta no os.environ.
    
    Funciona para todas as variáveis simples e também para o JSON do GSC,
    que pode estar armazenado como tabela TOML [GSC_CREDENTIALS_JSON_CONTENT].
    """
    try:
        secrets = st.secrets
        # Variáveis simples de texto
        mapeamento = {
            "GEMINI_API_KEY": "GEMINI_API_KEY",
            "WP_URL": "WP_URL",
            "WP_USER": "WP_USER",
            "WP_APP_PASSWORD": "WP_APP_PASSWORD",
        }
        for secret_key, env_key in mapeamento.items():
            if secret_key in secrets and not os.getenv(env_key):
                os.environ[env_key] = secrets[secret_key]

        # JSON do GSC: vem como AttrDict/dict (tabela TOML) ou string
        if "GSC_CREDENTIALS_JSON_CONTENT" in secrets and not os.getenv("GSC_CREDENTIALS_JSON_CONTENT"):
            conteudo = secrets["GSC_CREDENTIALS_JSON_CONTENT"]
            try:
                # Serializa para JSON de forma segura, convertendo o AttrDict recursivamente
                conteudo_dict = json.loads(json.dumps(dict(conteudo)))
                os.environ["GSC_CREDENTIALS_JSON_CONTENT"] = json.dumps(conteudo_dict)
            except Exception:
                # Fallback: converte item por item manualmente
                conteudo_plain = {str(k): str(v) for k, v in conteudo.items()}
                os.environ["GSC_CREDENTIALS_JSON_CONTENT"] = json.dumps(conteudo_plain)
    except Exception:
        # Fora da nuvem (rodando local), os secrets não existem — usa o .env normalmente
        pass

# Executa a injeção ANTES de qualquer outra coisa
injetar_streamlit_secrets()

# Carrega variáveis de ambiente do arquivo .env local (para desenvolvimento)
ENV_FILE = ".env"
load_dotenv(ENV_FILE)

# Inicializa o banco de dados
modulo4.inicializar_banco()

# -----------------------------------------------------
# FUNÇÕES AUXILIARES
# -----------------------------------------------------
def obter_posts_wordpress():
    """
    Busca o histórico real de posts diretamente da API do WordPress.
    Isso garante que o histórico nunca se perde, mesmo quando o servidor reinicia.
    """
    wp_url = (os.getenv("WP_URL") or "").rstrip('/')
    wp_user = os.getenv("WP_USER")
    wp_pass = os.getenv("WP_APP_PASSWORD")

    if not wp_url or not wp_user or not wp_pass:
        st.warning(
            f"⚠️ Credenciais do WordPress ausentes nos Secrets. "
            f"WP_URL={'✅' if wp_url else '❌ vazio'} | "
            f"WP_USER={'✅' if wp_user else '❌ vazio'} | "
            f"WP_APP_PASSWORD={'✅' if wp_pass else '❌ vazio'}"
        )
        return pd.DataFrame()

    try:
        import requests
        endpoint = f"{wp_url}/wp-json/wp/v2/posts"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'application/json',
        }
        resp = requests.get(
            endpoint,
            auth=(wp_user, wp_pass),
            headers=headers,
            params={"per_page": 50, "orderby": "date", "order": "desc"},
            timeout=10
        )
        if resp.status_code == 200:
            posts = resp.json()
            dados = []
            for p in posts:
                dados.append({
                    "ID": p.get("id"),
                    "Título": p.get("title", {}).get("rendered", ""),
                    "Data de Publicação": p.get("date", "")[:10],
                    "Status": p.get("status", ""),
                    "URL": p.get("link", ""),
                })
            return pd.DataFrame(dados)
        else:
            # Mostra o erro exato da API do WordPress para diagnóstico
            st.warning(
                f"⚠️ A API do WordPress retornou erro **{resp.status_code}**.\n\n"
                f"URL consultada: `{endpoint}`\n\n"
                f"Resposta: `{resp.text[:300]}`"
            )
    except Exception as e:
        st.warning(f"Não foi possível conectar ao WordPress: {e}")
    return pd.DataFrame()

def gerar_grafico_vazio(mensagem="Sem dados suficientes"):
    fig = px.line(title=mensagem)
    fig.update_layout(
        xaxis={"visible": False}, yaxis={"visible": False},
        annotations=[{"text": mensagem, "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 20}}]
    )
    return fig

# -----------------------------------------------------
# LAYOUT DO DASHBOARD
# -----------------------------------------------------
st.title("🤖 Motor de Automação de Blog & SEO")
st.markdown("Bem-vindo à *Lataria*! Acompanhe o desempenho, descubra pautas autônomas e ajuste configurações.")

tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Visão Geral",
    "📝 Linha de Produção",
    "🎯 Inteligência de Pauta",
    "⚙️ Configurações"
])

# =====================================================
# ABA 1: VISÃO GERAL (KPIs)
# =====================================================
with tab1:
    st.header("KPIs de Desempenho (Search Console)")
    st.write("Visão geral do tráfego orgânico gerado pelo Google.")

    col1, col2, col3, col4 = st.columns(4)

    try:
        service = modulo3.conectar_gsc()
        site_url = (os.getenv("WP_URL") or "").rstrip('/').split('/blog')[0] + '/'
        data_fim = datetime.now().strftime('%Y-%m-%d')
        data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        req = {'startDate': data_inicio, 'endDate': data_fim, 'dimensions': ['date']}

        sites = service.sites().list().execute().get('siteEntry', [])
        if sites:
            site_url = sites[0]['siteUrl']

        resp = service.searchanalytics().query(siteUrl=site_url, body=req).execute()
        rows = resp.get('rows', [])

        tot_clicks = sum(r['clicks'] for r in rows)
        tot_imp = sum(r['impressions'] for r in rows)
        avg_ctr = sum(r['ctr'] for r in rows) / len(rows) if rows else 0
        avg_pos = sum(r['position'] for r in rows) / len(rows) if rows else 0

        col1.metric("Cliques (30d)", f"{tot_clicks}")
        col2.metric("Impressões (30d)", f"{tot_imp}")
        col3.metric("CTR Médio", f"{avg_ctr*100:.2f}%")
        col4.metric("Posição Média", f"{avg_pos:.1f}")

        if rows:
            df_gsc = pd.DataFrame([{
                'Data': r['keys'][0],
                'Cliques': r['clicks'],
                'Impressões': r['impressions']
            } for r in rows])
            df_gsc['Data'] = pd.to_datetime(df_gsc['Data'])
            fig = px.line(df_gsc, x='Data', y=['Cliques', 'Impressões'], title="Evolução de Tráfego Orgânico", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados suficientes no Search Console nos últimos 30 dias.")

    except Exception as e:
        st.warning(f"Erro ao conectar ao Search Console. Verifique as configurações na Aba 4. Detalhe: {e}")


# =====================================================
# ABA 2: LINHA DE PRODUÇÃO
# =====================================================
with tab2:
    st.header("Histórico de Posts Publicados")
    st.caption("Histórico carregado diretamente do WordPress — nunca se perde quando o servidor reinicia.")

    with st.spinner("Carregando posts do WordPress..."):
        df_posts = obter_posts_wordpress()

    if not df_posts.empty:
        st.dataframe(df_posts, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum post encontrado ou credenciais do WordPress não configuradas.")

    st.divider()
    st.subheader("Controle Manual")
    st.write("O robô deve rodar sozinho todos os dias (via GitHub Actions). Mas você pode forçar a criação de um post agora mesmo.")

    if st.button("🚀 Gerar e Publicar Post AGORA", type="primary"):
        with st.spinner("A IA está analisando dados e escrevendo... Isso leva cerca de 30-40 segundos."):
            tema_hoje = gerador_pautas.sugerir_tema_autonomo()
            st.success(f"**Tema Escolhido:** {tema_hoje}")

            # Executa a criação
            modulo4.criar_e_publicar_novo_post(tema_hoje)
            st.success("Artigo gerado, postado no WordPress e salvo no banco de agendamentos!")
            st.rerun()

# =====================================================
# ABA 3: INTELIGÊNCIA DE PAUTA
# =====================================================
with tab3:
    st.header("Radar de SEO e GEO")
    st.write("O que as pessoas estão buscando no Google recentemente sobre o seu site:")

    with st.spinner("Puxando termos do Google..."):
        queries = gerador_pautas.obter_top_queries_gsc(limite=10)

    if queries:
        for q in queries:
            st.code(q)
    else:
        st.write("Nenhuma palavra-chave com impressões encontrada ainda.")

    st.info("A IA cruza esses dados com o banco de posts anteriores para garantir que os temas sempre sejam inéditos e focados nas dores reais.")

# =====================================================
# ABA 4: CONFIGURAÇÕES
# =====================================================
with tab4:
    st.header("⚙️ Configurações do Robô")

    # Proteção simples por senha na sessão
    if "admin_logado" not in st.session_state:
        st.session_state["admin_logado"] = False

    if not st.session_state["admin_logado"]:
        senha = st.text_input("Senha de Administrador", type="password")
        if st.button("Entrar"):
            if senha == "admin123":
                st.session_state["admin_logado"] = True
                st.rerun()
            else:
                st.error("Senha incorreta.")
    else:
        if st.button("Sair"):
            st.session_state["admin_logado"] = False
            st.rerun()

        st.success("Autenticado com sucesso.")

        # Aviso sobre Streamlit Secrets
        st.info(
            "💡 **Recomendado:** As configurações abaixo são para uso LOCAL (seu computador). "
            "Se o app está hospedado no **Streamlit Cloud**, configure as chaves diretamente no painel do Streamlit Cloud "
            "(Settings → Secrets) para que elas nunca se percam quando o servidor reiniciar."
        )

        st.write("Preencha as chaves abaixo para que o robô tenha acesso aos serviços (uso local).")

        with st.form("config_form"):
            wp_url = st.text_input("WordPress URL", value=os.getenv("WP_URL", ""))
            wp_user = st.text_input("Usuário do WordPress", value=os.getenv("WP_USER", ""))
            wp_pass = st.text_input("Senha de Aplicativo do WP", value=os.getenv("WP_APP_PASSWORD", ""), type="password")
            st.caption("No WP, vá em Usuários > Perfil > Senhas de Aplicativo.")

            gemini_key = st.text_input("Chave API do Google Gemini", value=os.getenv("GEMINI_API_KEY", ""), type="password")
            st.caption("Gere a chave gratuitamente em: https://aistudio.google.com/app/apikey")

            json_file = st.file_uploader("Arquivo .json do Google Search Console (apenas para uso local)", type=['json'])

            if st.form_submit_button("Salvar Configurações"):
                if not os.path.exists(ENV_FILE):
                    open(ENV_FILE, 'a').close()

                set_key(ENV_FILE, "WP_URL", wp_url)
                set_key(ENV_FILE, "WP_USER", wp_user)
                set_key(ENV_FILE, "WP_APP_PASSWORD", wp_pass)
                set_key(ENV_FILE, "GEMINI_API_KEY", gemini_key)

                # Aplica IMEDIATAMENTE no ambiente do servidor
                os.environ["WP_URL"] = wp_url
                os.environ["WP_USER"] = wp_user
                os.environ["WP_APP_PASSWORD"] = wp_pass
                os.environ["GEMINI_API_KEY"] = gemini_key

                if json_file is not None:
                    nome_arquivo = json_file.name
                    with open(nome_arquivo, "wb") as f:
                        f.write(json_file.getbuffer())
                    set_key(ENV_FILE, "GSC_CREDENTIALS_JSON", nome_arquivo)
                    os.environ["GSC_CREDENTIALS_JSON"] = nome_arquivo

                st.success("Configurações salvas e ativadas! Você já pode usar o gerador.")
