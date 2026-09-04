import os
from dotenv import load_dotenv
from google.oauth2 import service_account
from googleapiclient.discovery import build

load_dotenv()
GSC_CREDENTIALS_JSON = os.getenv("GSC_CREDENTIALS_JSON")
SCOPES = ['https://www.googleapis.com/auth/webmasters.readonly']

def listar_sites():
    credentials = service_account.Credentials.from_service_account_file(
        GSC_CREDENTIALS_JSON,
        scopes=SCOPES
    )
    service = build('searchconsole', 'v1', credentials=credentials)
    
    try:
        response = service.sites().list().execute()
        sites = response.get('siteEntry', [])
        if not sites:
            print("A conta de serviço não tem acesso a NENHUM site no Search Console.")
        else:
            print("A conta de serviço tem acesso aos seguintes sites:")
            for site in sites:
                print(f"- {site['siteUrl']}")
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    listar_sites()
