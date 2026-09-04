import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import os
import shutil
from dotenv import load_dotenv, set_key

# Importações dos nossos módulos do robô
import modulo3
import modulo4
import gerador_pautas

# Configuração da página
st.set_page_config(page_title="Dashboard IA - Seguro Estagiário", layout="wide", page_icon="🤖")

# Carrega variáveis de ambiente
ENV_FILE = ".env"
load_dotenv(ENV_FILE)

# -----------------------------------------------------
# FUNÇÕES AUXILIARES
# -----------------------------------------------------
def obter_dados_sqlite():
    """Lê os posts do banco de dados e retorna em um DataFrame."""
    try:
        conn = sqlite3.connect("agendamentos.db")
        df = pd.read_sql_query("SELECT * FROM posts", conn)
        conn.close()
        return df
    except Exception:
        return pd.DataFrame()

def gerar_grafico_vazio(mensagem="Sem dados suficientes"):
    fig = px.line(title=mensagem)
    fig.update_layout(xaxis={"visible": False}, yaxis={"visible": False}, annotations=[{"text": mensagem, "xref": "paper", "yref": "paper", "showarrow": False, "font": {"size": 20}}])
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
    # Aqui, em um cenário real, você faria uma busca agregada no GSC.
    # Como exemplo, vamos simular que pegamos o total.
    
    try:
        service = modulo3.conectar_gsc()
        site_url = modulo3.WP_URL.split('/blog')[0] + '/'
        # Busca últimos 30 dias do site todo
        data_fim = datetime.now().strftime('%Y-%m-%d')
        data_inicio = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        req = {'startDate': data_inicio, 'endDate': data_fim, 'dimensions': ['date']}
        
        sites = service.sites().list().execute().get('siteEntry', [])
        if sites: site_url = sites[0]['siteUrl']
        
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
    st.header("Histórico de Posts Gerados")
    df_posts = obter_dados_sqlite()
    
    if not df_posts.empty:
        # Renomeando e ajustando exibição
        df_exibicao = df_posts[['topico', 'data_publicacao', 'status_7d', 'status_30d', 'status_60d', 'url']]
        st.dataframe(df_exibicao, use_container_width=True)
    else:
        st.info("Nenhum post publicado pelo robô ainda.")
        
    st.divider()
    st.subheader("Controle Manual")
    st.write("O robô deve rodar sozinho todos os dias (via Agendador). Mas você pode forçar a criação de um post agora mesmo.")
    
    if st.button("🚀 Gerar e Publicar Post AGORA", type="primary"):
        with st.spinner("A IA está analisando dados e escrevendo... Isso leva cerca de 30-40 segundos."):
            tema_hoje = gerador_pautas.sugerir_tema_autonomo()
            st.success(f"**Tema Escolhido:** {tema_hoje}")
            
            # Executa a criação
            modulo4.criar_e_publicar_novo_post(tema_hoje)
            st.success("Artigo gerado, postado no WordPress e salvo no banco de agendamentos!")
            st.rerun() # Atualiza a tela

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
            # Senha simples fixa para o exemplo (poderia vir de .env)
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
        st.write("Preencha as chaves abaixo para que o robô tenha acesso aos serviços.")
        
        with st.form("config_form"):
            wp_url = st.text_input("WordPress URL", value=os.getenv("WP_URL", ""))
            wp_user = st.text_input("Usuário do WordPress", value=os.getenv("WP_USER", ""))
            wp_pass = st.text_input("Senha de Aplicativo do WP", value=os.getenv("WP_APP_PASSWORD", ""), type="password")
            st.caption("No WP, vá em Usuários > Perfil > Senhas de Aplicativo.")
            
            gemini_key = st.text_input("Chave API do Google Gemini", value=os.getenv("GEMINI_API_KEY", ""), type="password")
            st.caption("Gere a chave gratuitamente em: https://aistudio.google.com/app/apikey")
            
            json_file = st.file_uploader("Arquivo .json do Google Search Console", type=['json'])
            
            if st.form_submit_button("Salvar Configurações"):
                set_key(ENV_FILE, "WP_URL", wp_url)
                set_key(ENV_FILE, "WP_USER", wp_user)
                set_key(ENV_FILE, "WP_APP_PASSWORD", wp_pass)
                set_key(ENV_FILE, "GEMINI_API_KEY", gemini_key)
                
                if json_file is not None:
                    nome_arquivo = json_file.name
                    with open(nome_arquivo, "wb") as f:
                        f.write(json_file.getbuffer())
                    set_key(ENV_FILE, "GSC_CREDENTIALS_JSON", nome_arquivo)
                    
                st.success("Configurações salvas no arquivo oculto `.env`! Reinicie a página para aplicar.")
