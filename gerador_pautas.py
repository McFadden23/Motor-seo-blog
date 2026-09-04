import os
import sqlite3
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google import genai
import modulo3  # Reutiliza conexão do GSC

load_dotenv()
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return None
    return genai.Client(api_key=api_key)

def obter_top_queries_gsc(dias=30, limite=15):
    """Obtém as palavras-chave mais buscadas do site no Search Console."""
    try:
        service = modulo3.conectar_gsc()
    except Exception as e:
        print(f"Aviso ao conectar GSC (Pautas): {e}")
        return []
        
    wp_url = (os.getenv("WP_URL") or "").rstrip('/')
    site_url = wp_url.split('/blog')[0] + '/' if wp_url else ""
    
    # Tenta descobrir o URL real
    try:
        sites = service.sites().list().execute().get('siteEntry', [])
        if sites: site_url = sites[0]['siteUrl']
    except: pass
    
    if not site_url:
        return []

    data_fim = datetime.now().strftime('%Y-%m-%d')
    data_inicio = (datetime.now() - timedelta(days=dias)).strftime('%Y-%m-%d')
    
    request_body = {
        'startDate': data_inicio,
        'endDate': data_fim,
        'dimensions': ['query'],
        'rowLimit': limite
    }
    
    queries = []
    try:
        response = service.searchanalytics().query(siteUrl=site_url, body=request_body).execute()
        if 'rows' in response:
            for row in response['rows']:
                # Retorna a palavra, impressoes e posicao
                queries.append(f"{row['keys'][0]} (Pos: {round(row['position'], 1)}, Impressões: {row['impressions']})")
    except Exception as e:
        print(f"Erro ao buscar queries no GSC: {e}")
        
    return queries

def obter_historico_temas():
    """Obtém a lista de tópicos já gerados para não repetir."""
    temas = []
    try:
        conn = sqlite3.connect("agendamentos.db")
        cursor = conn.cursor()
        cursor.execute("SELECT topico FROM posts")
        rows = cursor.fetchall()
        for r in rows:
            temas.append(r[0])
        conn.close()
    except Exception:
        pass
    return temas

def sugerir_tema_autonomo() -> str:
    """Usa o Gemini para analisar os dados e decidir a melhor pauta do dia."""
    historico = obter_historico_temas()
    top_queries = obter_top_queries_gsc()
    
    str_historico = "\n".join(f"- {t}" for t in historico) if historico else "Nenhum histórico."
    str_queries = "\n".join(f"- {q}" for q in top_queries) if top_queries else "Sem dados do GSC."
    
    prompt = f"""
    Você é um especialista em SEO e Estrategista de Conteúdo.
    Seu cliente é um blog brasileiro focado estritamente no nicho de "Seguro Estagiário".
    Sua missão é escolher o ÚNICO melhor tema para o post de hoje.
    
    CONTEXTO DO MERCADO (GEO/Dúvidas):
    - Lei do Estágio 11.788 obriga o seguro.
    - Buscas regionais funcionam bem (ex: São Paulo, RJ, Curitiba).
    - Dúvidas comuns: preço, o que cobre, acidente de trajeto, morte acidental, quem paga (empresa vs escola).
    
    HISTÓRICO RECENTE (NÃO REPITA ESTES TEMAS):
    {str_historico}
    
    O QUE AS PESSOAS JÁ ESTÃO BUSCANDO NO GOOGLE (Use como inspiração para resolver dores reais):
    {str_queries}
    
    REGRAS DA SUA RESPOSTA:
    1. Retorne APENAS UMA FRASE contendo o título/tópico perfeito e focado.
    2. Não explique a estratégia, não dê opções. Apenas o tópico final.
    3. Exemplo de bom formato: "Seguro de vida para estagiário em São Paulo: Regras e Preços em 2024"
    """
    
    print("Gerando pauta com IA com base no Search Console e Histórico...")
    
    gemini_client = get_gemini_client()
    if not gemini_client:
        return "Configure sua chave Gemini na aba Ajustes"
        
    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    tema = response.text.strip().replace('"', '')
    print(f"Pauta escolhida pela IA: {tema}")
    return tema

if __name__ == "__main__":
    sugerir_tema_autonomo()
