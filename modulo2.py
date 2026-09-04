import os
import chromadb
from google import genai
from dotenv import load_dotenv

load_dotenv()

# Inicializa cliente Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

# Configura o ChromaDB na pasta local
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="padroes_sucesso")

def extrair_estrutura(texto_sucesso: str) -> str:
    """Usa o Gemini para analisar um texto e extrair sua 'fórmula'."""
    print("Extraindo estrutura do texto via Gemini...")
    
    prompt = f"""
    Analise o texto abaixo e extraia a ESTRUTURA e o TOM DE VOZ usados.
    Eu não quero o conteúdo, quero a "fórmula" deste texto.
    
    Exemplo de saída:
    - Tom de voz: Amigável e direto.
    - Estrutura: 5 parágrafos curtos, uso de 1 lista, 2 subtítulos em H2, e foco na dor do cliente.

    Texto a ser analisado:
    {texto_sucesso}
    """
    response = gemini_client.models.generate_content(
        model="gemini-3.5-flash",
        contents=prompt
    )
    return response.text.strip()

def salvar_padrao(topico: str, texto_sucesso: str, id_post: str):
    """Extrai a estrutura e a salva no banco vetorial."""
    estrutura = extrair_estrutura(texto_sucesso)
    
    collection.add(
        documents=[estrutura],
        metadatas=[{"topico": topico}],
        ids=[id_post]
    )
    print(f"SUCESSO! Padrão de sucesso salvo no ChromaDB para: '{topico}'")

def buscar_estrutura(topico_novo: str) -> str:
    """Busca a estrutura mais semelhante no banco para guiar um novo texto."""
    if collection.count() == 0:
        return "Estrutura padrão: Tom amigável, parágrafos curtos, focado na prática e sem jargões de IA."
        
    print(f"Buscando padrão na memória para: '{topico_novo}'...")
    resultados = collection.query(
        query_texts=[topico_novo],
        n_results=1
    )
    
    if resultados['documents'] and len(resultados['documents'][0]) > 0:
        melhor_estrutura = resultados['documents'][0][0]
        print("PADRÃO ENCONTRADO!")
        return melhor_estrutura
    
    return "Estrutura padrão: Tom amigável, parágrafos curtos, focado na prática e sem jargões de IA."

if __name__ == "__main__":
    # Teste isolado do Módulo 2
    texto_exemplo = "<p>O seguro estagiário é muito importante porque...</p><h2>Vantagens</h2><ul><li>Proteção</li></ul>"
    
    # Simula salvamento de um post que "performou bem"
    salvar_padrao(
        topico="Por que toda empresa precisa de um seguro estagiário",
        texto_sucesso=texto_exemplo,
        id_post="post_123"
    )
    
    # Testa a busca
    padrao = buscar_estrutura("Quais as coberturas do seguro estagiário")
    print("\n--- Padrão Recuperado ---")
    print(padrao)
