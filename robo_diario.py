import os
import modulo4
import gerador_pautas

def executar_robo():
    print("Iniciando o robô diário do Blog Seguro Estagiário...")
    
    # 1. Garante que o banco SQLite local existe (o GitHub Actions roda em um contêiner zerado)
    modulo4.inicializar_banco()
    
    # 2. Roda as checagens de posts antigos (SEO)
    try:
        modulo4.processar_checagens_do_dia()
    except Exception as e:
        print(f"Erro ao processar checagens: {e}")
    
    # 3. Gera e publica o post do dia
    try:
        tema_do_dia = gerador_pautas.sugerir_tema_autonomo()
        print(f"\nTema escolhido pela IA para hoje: {tema_do_dia}")
        if tema_do_dia:
            modulo4.criar_e_publicar_novo_post(tema_do_dia)
    except Exception as e:
        print(f"Erro ao gerar post do dia: {e}")

if __name__ == "__main__":
    executar_robo()
