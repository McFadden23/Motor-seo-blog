import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()

# Configuracoes do Google Search Console
GSC_CREDENTIALS_JSON = os.getenv("GSC_CREDENTIALS_JSON")
WP_URL = os.getenv("WP_URL").rstrip('/')

# Escopo necessario para leitura do Search Console
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']


def conectar_gsc():
    """Cria e retorna o cliente autenticado do Google Search Console."""
    credentials = service_account.Credentials.from_service_account_file(
        GSC_CREDENTIALS_JSON,
        scopes=SCOPES
    )
    service = build('searchconsole', 'v1', credentials=credentials)
    return service


def obter_metricas_post(url_post: str, dias_atras: int = 30) -> dict:
    """
    Consulta o Search Console e retorna as metricas de SEO de um post especifico.
    
    Retorna:
        dict com 'impressoes', 'cliques', 'ctr', 'posicao_media'
    """
    service = conectar_gsc()
    
    data_fim = datetime.now().strftime('%Y-%m-%d')
    data_inicio = (datetime.now() - timedelta(days=dias_atras)).strftime('%Y-%m-%d')
    
    # Monta a requisicao para a API
    request_body = {
        'startDate': data_inicio,
        'endDate': data_fim,
        'dimensions': ['page'],
        'dimensionFilterGroups': [{
            'filters': [{
                'dimension': 'page',
                'operator': 'equals',
                'expression': url_post
            }]
        }],
        'rowLimit': 1
    }
    
    # Obtém a propriedade correta (URL) que a conta de serviço tem acesso
    site_url = ""
    try:
        sites = service.sites().list().execute().get('siteEntry', [])
        if sites:
            site_url = sites[0]['siteUrl']
        else:
            print("ERRO: Conta de serviço não tem acesso a nenhum site.")
            return None
    except Exception as e:
        print(f"ERRO ao listar sites: {e}")
        return None
        
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        if 'rows' in response and len(response['rows']) > 0:
            row = response['rows'][0]
            metricas = {
                'impressoes': row['impressions'],
                'cliques': row['clicks'],
                'ctr': round(row['ctr'] * 100, 2),  # Converte para percentual
                'posicao_media': round(row['position'], 1)
            }
            print(f"Metricas de '{url_post}':")
            print(f"  Impressoes: {metricas['impressoes']}")
            print(f"  Cliques: {metricas['cliques']}")
            print(f"  CTR: {metricas['ctr']}%")
            print(f"  Posicao Media: {metricas['posicao_media']}")
            return metricas
        else:
            print(f"Sem dados para '{url_post}' nos ultimos {dias_atras} dias.")
            return {
                'impressoes': 0,
                'cliques': 0,
                'ctr': 0,
                'posicao_media': 0
            }
    except Exception as e:
        print(f"ERRO ao consultar o Search Console: {e}")
        return None


def avaliar_performance(metricas: dict) -> str:
    """
    Avalia se o post foi um sucesso ou fracasso com base nas metricas.
    
    Regra de Negocio:
    - SUCESSO: Posicao media < 10 (primeira pagina do Google)
    - OPORTUNIDADE: Posicao entre 10 e 20 (segunda pagina, quase la)
    - FRACASSO: Posicao > 20 ou sem impressoes
    """
    if metricas is None or metricas['impressoes'] == 0:
        return "SEM_DADOS"
    
    posicao = metricas['posicao_media']
    
    if posicao > 0 and posicao < 10:
        print(f"RESULTADO: SUCESSO! Posicao {posicao} (Pagina 1 do Google)")
        return "SUCESSO"
    elif posicao >= 10 and posicao <= 20:
        print(f"RESULTADO: OPORTUNIDADE. Posicao {posicao} (Pagina 2, quase la!)")
        return "OPORTUNIDADE"
    else:
        print(f"RESULTADO: FRACASSO. Posicao {posicao} (Muito longe da pagina 1)")
        return "FRACASSO"


if __name__ == "__main__":
    # Teste isolado do Modulo 3
    print("=== Teste do Modulo 3: Analise de Performance SEO ===\n")
    
    # Testa conexao e busca de metricas do post publicado pelo Modulo 1
    url_teste = "https://nautiplus.com.br/blog/os-principais-beneficios-do-seguro-estagiario-para-empresas-e-estudantes/"
    
    metricas = obter_metricas_post(url_teste, dias_atras=7)
    
    if metricas:
        resultado = avaliar_performance(metricas)
        print(f"\nVeredicto final: {resultado}")
