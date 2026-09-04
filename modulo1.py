import os
import requests
from datetime import datetime
from google import genai
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações dinâmicas
def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave GEMINI_API_KEY não configurada. Configure na aba Ajustes.")
    return genai.Client(api_key=api_key)

def get_wp_config():
    wp_user = os.getenv("WP_USER")
    wp_pass = os.getenv("WP_APP_PASSWORD")
    wp_url = (os.getenv("WP_URL") or "").rstrip('/')
    endpoint = f"{wp_url}/wp-json/wp/v2/posts" if wp_url else ""
    return wp_user, wp_pass, endpoint


from modulo2 import buscar_estrutura

def gerar_texto_gemini(topico: str) -> str:
    """Gera o conteúdo do post usando a API do Gemini com prompt específico para não parecer IA."""
    client = get_gemini_client()
    print(f"Gerando texto sobre: {topico}...")
    
    # Busca a estrutura de sucesso no Banco Vetorial
    estrutura_ideal = buscar_estrutura(topico)

    ano_atual = datetime.now().year

    prompt = f"""
    Escreva um artigo de blog completo e otimizado para SEO sobre o tópico: '{topico}'.
    O nicho do blog é focado estritamente em Seguros para Estagiários no Brasil.
    O ano atual é {ano_atual}. Use sempre informações, regras e leis atualizadas para o ano vigente.
    NUNCA mencione anos passados como se fossem o presente.
    
    AQUI ESTÁ A "FÓRMULA SECRETA" (ESTRUTURA E TOM DE VOZ) QUE VOCÊ DEVE SEGUIR:
    {estrutura_ideal}

    Regras estritas de formatação HTML:
    1. NÃO use jargões de inteligência artificial como: "em resumo", "no mundo de hoje", "mergulhemos", "concluindo".
    2. O texto deve ter entre 600 e 900 palavras.
    3. Retorne APENAS o HTML cru do conteúdo (sem as tags <html>, <head> ou <body>), pronto para ser inserido no WordPress.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )

    return response.text.strip()


def publicar_no_wordpress(titulo: str, conteudo_html: str):
    """Publica o texto gerado diretamente no WordPress via REST API."""
    print(f"Publicando no WordPress: '{titulo}'...")

    data = {
        'title': titulo,
        'content': conteudo_html,
        'status': 'publish'  # Publica direto, sem rascunho
    }

    wp_user, wp_pass, endpoint = get_wp_config()
    if not endpoint or not wp_user or not wp_pass:
        print("ERRO: Credenciais do WordPress não configuradas.")
        return None

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }

    response = requests.post(
        endpoint,
        auth=(wp_user, wp_pass),
        headers=headers,
        json=data
    )

    if response.status_code == 201:
        post_url = response.json().get('link')
        post_id = response.json().get('id')
        print(f"SUCESSO! Post publicado em: {post_url}")
        return (post_url, post_id)
    else:
        print(f"ERRO ao publicar: {response.status_code}")
        print(response.text)
        return None

def atualizar_no_wordpress(post_id: int, novo_conteudo: str) -> bool:
    """Atualiza (reescreve) um post existente no WordPress via REST API."""
    print(f"Atualizando o post ID {post_id} no WordPress...")
    
    wp_user, wp_pass, endpoint = get_wp_config()
    if not endpoint or not wp_user or not wp_pass:
        print("ERRO: Credenciais do WordPress não configuradas.")
        return False
        
    url = f"{endpoint}/{post_id}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    
    data = {
        "content": novo_conteudo
    }
    
    response = requests.post(
        url,
        headers=headers,
        json=data,
        auth=(WP_USER, WP_APP_PASSWORD)
    )
    
    if response.status_code == 200:
        print(f"SUCESSO! Post {post_id} atualizado e reescrito.")
        return True
    else:
        print(f"ERRO ao atualizar o post {post_id}: {response.status_code}")
        print(response.text)
        return False


if __name__ == "__main__":
    # Teste do fluxo do Módulo 1
    topico_teste = "Os principais benefícios do Seguro Estagiário para Empresas e Estudantes"

    # 1. Gerar Texto
    conteudo = gerar_texto_gemini(topico_teste)

    if conteudo:
        print("\n--- PRÉVIA DO TEXTO GERADO ---")
        print(conteudo[:500], "...\n")
        # 2. Publicar
        publicar_no_wordpress(topico_teste, conteudo)
