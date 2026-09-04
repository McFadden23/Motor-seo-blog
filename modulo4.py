import sqlite3
from datetime import datetime, timedelta
import modulo1
import modulo2
import modulo3

# Nome do arquivo do banco de dados
DB_FILE = "agendamentos.db"

def inicializar_banco():
    """Cria a tabela de controle de posts se ela não existir."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id_wp INTEGER PRIMARY KEY,
            url TEXT NOT NULL,
            topico TEXT NOT NULL,
            data_publicacao DATE NOT NULL,
            status_7d TEXT DEFAULT 'PENDENTE',
            status_30d TEXT DEFAULT 'PENDENTE',
            status_60d TEXT DEFAULT 'PENDENTE'
        )
    ''')
    conn.commit()
    conn.close()

def registrar_post(id_wp: int, url: str, topico: str):
    """Registra um novo post no banco de dados para acompanhamento."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    hoje = datetime.now().strftime('%Y-%m-%d')
    cursor.execute('''
        INSERT INTO posts (id_wp, url, topico, data_publicacao)
        VALUES (?, ?, ?, ?)
    ''', (id_wp, url, topico, hoje))
    conn.commit()
    conn.close()
    print(f"Post {id_wp} registrado na agenda de checagem SEO.")

def processar_checagens_do_dia():
    """Roda diariamente para checar posts que completaram 7, 30 ou 60 dias."""
    print(f"\n=== Iniciando Motor de Checagem SEO ({datetime.now().strftime('%Y-%m-%d')}) ===")
    
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    
    hoje = datetime.now().date()
    
    for post in posts:
        id_wp, url, topico, data_pub_str, s7, s30, s60 = post
        data_pub = datetime.strptime(data_pub_str, '%Y-%m-%d').date()
        dias_passados = (hoje - data_pub).days
        
        # Determina qual marco estamos checando
        marco_atual = None
        coluna_status = None
        
        if dias_passados == 7 and s7 == 'PENDENTE':
            marco_atual = 7
            coluna_status = 'status_7d'
        elif dias_passados == 30 and s30 == 'PENDENTE':
            marco_atual = 30
            coluna_status = 'status_30d'
        elif dias_passados == 60 and s60 == 'PENDENTE':
            marco_atual = 60
            coluna_status = 'status_60d'
            
        if marco_atual:
            print(f"\n[Checagem de {marco_atual} dias] Analisando: {url}")
            
            # 1. Puxar métricas do Módulo 3
            metricas = modulo3.obter_metricas_post(url, dias_atras=marco_atual)
            resultado = modulo3.avaliar_performance(metricas)
            
            # Atualiza o status no banco provisoriamente
            cursor.execute(f"UPDATE posts SET {coluna_status} = ? WHERE id_wp = ?", (resultado, id_wp))
            conn.commit()
            
            # 2. Tomar Ação (O Feedback Loop)
            if resultado == "SUCESSO":
                print("-> Ação: Post fez sucesso! Extraindo padrão (Módulo 2)...")
                # Baixa o conteúdo do post atual
                import requests
                try:
                    wp_response = requests.get(f"{modulo1.WP_API_ENDPOINT}/{id_wp}", auth=(modulo1.WP_USER, modulo1.WP_APP_PASSWORD))
                    if wp_response.status_code == 200:
                        conteudo_html = wp_response.json().get('content', {}).get('rendered', '')
                        modulo2.salvar_padrao(topico, conteudo_html, str(id_wp))
                except Exception as e:
                    print(f"Erro ao baixar conteúdo do WP para extrair padrão: {e}")
                
            elif resultado == "FRACASSO" and marco_atual >= 30: # 7 dias é muito cedo para reescrever
                print("-> Ação: Post não performou. Acionando Módulo 1 para reescrita automática...")
                novo_texto = modulo1.gerar_texto_gemini(topico)
                if novo_texto:
                    modulo1.atualizar_no_wordpress(id_wp, novo_texto)

    conn.close()
    print("\n=== Checagens finalizadas ===")

def criar_e_publicar_novo_post(topico: str):
    """Fluxo principal que usa todos os módulos para criar um post do zero."""
    # 1. Módulo 1 + 2: Gera o texto usando a memória
    conteudo = modulo1.gerar_texto_gemini(topico)
    
    if conteudo:
        # 2. Módulo 1: Publica
        # Precisamos modificar modulo1 para retornar (url, id_wp)
        resultado = modulo1.publicar_no_wordpress(topico, conteudo)
        
        if resultado and isinstance(resultado, tuple):
            post_url, post_id = resultado
            # 3. Módulo 4: Agenda para o futuro
            registrar_post(post_id, post_url, topico)
        else:
            print("Postado, mas modulo1 não retornou o formato (url, id) esperado.")

if __name__ == "__main__":
    inicializar_banco()
    print("Banco de dados SQLite inicializado com sucesso!")
    # Para rodar a rotina diária:
    # processar_checagens_do_dia()
