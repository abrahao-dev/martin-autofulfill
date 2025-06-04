import requests
import os
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações da API Shopify
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')
SHOPIFY_API_KEY = os.getenv('SHOPIFY_API_KEY')
SHOPIFY_API_PASSWORD = os.getenv('SHOPIFY_API_PASSWORD')
SHOPIFY_API_TOKEN = os.getenv('SHOPIFY_API_TOKEN')
API_VERSION = '2023-10'

# Cache para armazenar o location_id após a primeira consulta
_location_id_cache = None

# Função para formatar corretamente a URL da loja Shopify
def formatar_shopify_url(store):
    """Garante que o domínio da loja Shopify esteja no formato correto
    
    Args:
        store (str): Nome da loja ou URL parcial (ex: 'martin4shop' ou 'martin4shop.myshopify.com')
        
    Returns:
        str: URL formatada corretamente (ex: 'martin4shop.myshopify.com')
    """
    if not store:
        return None
        
    # Remover protocolo se presente
    if store.startswith('http'):
        store = store.split('://')[-1]
        
    # Remover caminhos após o domínio
    store = store.split('/')[0]
    
    # Adicionar .myshopify.com se não estiver presente
    if '.myshopify.com' not in store:
        store = f"{store}.myshopify.com"
        
    return store

# URLs de rastreio pré-definidas
TRACKING_URLS = {
    'anjun': ['https://anjunexpress.com.br/rastreio'],
    'martin': ['https://martin4shop.com.br/pages/rastrear-pedido']
}

def criar_fulfillment(order_id, line_item_id, codigo_rastreamento, transportadora='anjun', notificar_cliente=True):
    """
    Cria um fulfillment para um pedido Shopify usando a API.
    
    Args:
        order_id (str): ID do pedido na Shopify
        line_item_id (str): ID da linha do item do pedido
        codigo_rastreamento (str): Código de rastreamento do pacote
        transportadora (str): 'anjun' ou 'martin' para selecionar a URL de rastreio
        notificar_cliente (bool): Se True, envia email de notificação ao cliente
        
    Returns:
        tuple: (sucesso, resposta_ou_erro) onde sucesso é um booleano e resposta_ou_erro é um dict ou string
    """
    # Validar parâmetros obrigatórios
    if not codigo_rastreamento or not codigo_rastreamento.strip():
        return False, "Código de rastreamento não pode estar vazio"
        
    if not line_item_id:
        return False, "line_item_id é obrigatório"
    
    # Garantir que o line_item_id seja int (a API Shopify requer int)
    try:
        line_item_id = int(line_item_id)
    except (ValueError, TypeError):
        return False, f"line_item_id inválido: {line_item_id} - deve ser um número inteiro"
        
    # Validar credenciais
    if not SHOPIFY_STORE:
        return False, "SHOPIFY_STORE não configurado no .env"
        
    if not (SHOPIFY_API_TOKEN or (SHOPIFY_API_KEY and SHOPIFY_API_PASSWORD)):
        return False, "Credenciais Shopify (API_TOKEN ou API_KEY+PASSWORD) não configuradas"
        
    # Verificar se temos as credenciais completas
    store_url = formatar_shopify_url(SHOPIFY_STORE)
    if not store_url:
        return False, f"URL da loja inválida: {SHOPIFY_STORE}"
    
    # Ajustar o order_id se necessário (remover # se presente)
    if isinstance(order_id, str) and order_id.startswith('#'):
        order_id = order_id[1:]
    
    # Ajustar o order_id para garantir que seja um número
    try:
        order_id = int(order_id)
    except (ValueError, TypeError):
        return False, f"order_id inválido: {order_id} - deve ser um número inteiro"
    
    # Obter o location_id real da Shopify
    location_id = obter_location_id()
    if not location_id:
        return False, "Não foi possível obter o location_id da Shopify. Verifique as credenciais e a conexão."
    
    # Selecionar URL de rastreio baseado na transportadora
    tracking_urls = TRACKING_URLS.get(transportadora.lower(), TRACKING_URLS['anjun'])
    
    # Montar o payload para a criação do fulfillment conforme requisitos exatos da Shopify
    # IMPORTANTE: NÃO incluir tracking_company - apenas tracking_urls para evitar o erro HTTP 406 (Not Acceptable)
    payload = {
        "fulfillment": {
            "location_id": location_id,
            "tracking_number": codigo_rastreamento,
            "tracking_urls": tracking_urls,
            "notify_customer": notificar_cliente,
            "line_items": [
                {
                    "id": line_item_id,
                    "quantity": 1
                }
            ]
        }
    }
    
    # Preparar cabeçalhos e URL
    url = f"https://{store_url}/admin/api/{API_VERSION}/orders/{order_id}/fulfillments.json"
    
    # Log para diagnóstico
    print(f"\nℹ️ DETALHES DA REQUISIÇÃO DE FULFILLMENT:")
    print(f"URL: {url}")
    print(f"Order ID: {order_id}")
    print(f"→ Headers: {json.dumps(headers, indent=2)}")
    print(f"→ Payload: {json.dumps(payload, indent=2)}")
    
    # Preparar cabeçalhos e URL
    url = f"https://{store_url}/admin/api/{API_VERSION}/orders/{order_id}/fulfillments.json"
    
    # Garantir que estamos usando o protocolo https://
    if not url.startswith('https://'):
        url = f"https://{url.split('://')[-1]}"
    
    # CORREÇÃO: Garantir que os headers estejam exatamente conforme especificado
    # pela documentação Shopify para evitar HTTP 406
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_PASSWORD,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # Enviar a requisição POST
        print(f"ℹ️ Enviando requisição para {url}...")
        response = requests.post(url, json=payload, headers=headers)
        
        # Verificar resposta
        if response.status_code in [201, 200]:
            resp_data = response.json()
            print(f"✅ Fulfillment criado com sucesso para o pedido {order_id}")
            print(f"📦 Rastreio: {codigo_rastreamento} via {transportadora}")
            return True, resp_data
        else:
            print(f"❌ Erro ao criar fulfillment: HTTP {response.status_code}")
            try:
                error_details = response.json()
                print(f"Detalhes do erro: {json.dumps(error_details, indent=2)}")
                return False, error_details
            except:
                print(f"Resposta de erro: {response.text}")
                return False, response.text
    
    except Exception as e:
        error_msg = f"❌ Erro ao enviar requisição: {str(e)}"
        print(error_msg)
        return False, error_msg

def obter_location_id():
    """
    Obtém o ID do local de estoque para fulfillment na Shopify.
    Faz uma chamada à API para listar todos os locais e retorna o primeiro ID encontrado,
    ou o location_id com o nome "Depósito" se existir.
    
    Returns:
        int: ID do location para fulfillment ou None em caso de erro
    """
    global _location_id_cache
    
    # Se já temos o location_id em cache, retorná-lo
    if _location_id_cache is not None:
        return _location_id_cache
    
    # Verificar se temos as credenciais necessárias
    store_url = formatar_shopify_url(SHOPIFY_STORE)
    if not store_url or not (SHOPIFY_API_PASSWORD or SHOPIFY_API_TOKEN):
        print("⚠️ Credenciais da API Shopify não configuradas")
        return None
    
    # Configurar URL e headers
    url = f"https://{store_url}/admin/api/{API_VERSION}/locations.json"
    
    # CORREÇÃO: Garantir que os headers estejam exatamente conforme especificado
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_PASSWORD,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
        
    try:
        # Fazer a requisição GET
        print(f"ℹ️ Obtendo locais da Shopify: {url}")
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            locations = response.json().get('locations', [])
            if not locations:
                print("❌ Nenhum local encontrado na Shopify")
                return None
                
            # Procurar por um local com "Depósito" no nome
            for location in locations:
                location_name = location.get('name', '').lower()
                if 'depósito' in location_name or 'deposito' in location_name:
                    _location_id_cache = location['id']
                    print(f"✅ Location ID encontrado: {_location_id_cache} - {location['name']}")
                    return _location_id_cache
            
            # Se não encontrar um depósito, usar o primeiro location encontrado
            _location_id_cache = locations[0]['id']
            print(f"✅ Usando primeiro location encontrado: {_location_id_cache} - {locations[0]['name']}")
            return _location_id_cache
        else:
            print(f"❌ Erro ao obter locations: HTTP {response.status_code}")
            print(f"Detalhes: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Erro ao buscar locations: {str(e)}")
        return None


def verificar_conexao_shopify():
    """
    Verifica se a conexão com a API da Shopify está funcionando.
    
    Returns:
        bool: True se a conexão estiver funcionando, False caso contrário
    """
    if not all([SHOPIFY_STORE, SHOPIFY_API_TOKEN]):
        print("⚠️ Credenciais da API Shopify não configuradas")
        return False
        
    # Usar um endpoint simples para verificar
    # Verificar se temos as credenciais completas
    store_url = formatar_shopify_url(SHOPIFY_STORE)
    
    # Preparar URL da API com autenticação apropriada
    if SHOPIFY_API_KEY and SHOPIFY_API_PASSWORD:
        # Usar API Key e senha se disponíveis
        url = f"https://{SHOPIFY_API_KEY}:{SHOPIFY_API_PASSWORD}@{store_url}/admin/api/{API_VERSION}/shop.json"
    else:
        # Usar token de acesso se API Key e senha não estiverem disponíveis
        url = f"https://{store_url}/admin/api/{API_VERSION}/shop.json"
    
    headers = {
        'X-Shopify-Access-Token': SHOPIFY_API_PASSWORD,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            shop_data = response.json()['shop']
            print(f"✅ Conectado à loja: {shop_data['name']}")
            return True
        else:
            print(f"❌ Falha na conexão: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erro de conexão: {str(e)}")
        return False

# Executar como script
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--verificar":
            # Verificar conexão
            verificar_conexao_shopify()
        elif sys.argv[1] == "--locations":
            # Exibir locations disponíveis
            location_id = obter_location_id()
            if location_id:
                print(f"✅ Location ID para fulfillment: {location_id}")
    else:
        print("Uso: python shopify_fulfillment.py [--verificar|--locations]")
        print("  --verificar  : Testa a conexão com a Shopify")
        print("  --locations  : Obtém o location_id para fulfillment")
        print("Este script é para ser usado como módulo em outros scripts.")
