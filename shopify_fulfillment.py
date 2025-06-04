import requests
import os
import json
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configurações da API Shopify
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')
SHOPIFY_API_TOKEN = os.getenv('SHOPIFY_API_TOKEN')
API_VERSION = '2023-10'

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
        dict: Resposta da API ou None se ocorrer erro
    """
    if not all([SHOPIFY_STORE, SHOPIFY_API_TOKEN]):
        print("⚠️ Credenciais da API Shopify não configuradas")
        return None
        
    # Preparar URL da API
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/orders/{order_id}/fulfillments.json"
    
    # Selecionar URL de rastreio baseado na transportadora
    tracking_urls = TRACKING_URLS.get(transportadora.lower(), TRACKING_URLS['anjun'])
    
    # Identificar a empresa de rastreio para exibição (será "Other" mas mostramos o nome real)
    tracking_company = "Other"
    
    # Nome para exibição na Shopify
    tracking_company_display = "Anjun Express" if transportadora.lower() == 'anjun' else "Martin4Shop"
    
    # Preparar payload
    payload = {
        "fulfillment": {
            "location_id": 1,  # Use o ID do seu depósito (geralmente é 1 para lojas pequenas)
            "tracking_number": codigo_rastreamento,
            "tracking_company": tracking_company,
            "tracking_urls": tracking_urls,
            "notify_customer": notificar_cliente,
            "line_items": [
                {
                    "id": line_item_id
                }
            ]
        }
    }
    
    # Configurar cabeçalhos
    headers = {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': SHOPIFY_API_TOKEN
    }
    
    try:
        # Fazer requisição POST
        response = requests.post(url, headers=headers, json=payload)
        
        # Verificar resposta
        if response.status_code in [201, 200]:
            print(f"✅ Fulfillment criado com sucesso para o pedido {order_id}")
            print(f"📦 Rastreio: {codigo_rastreamento} via {tracking_company_display}")
            return response.json()
        else:
            print(f"❌ Erro ao criar fulfillment: {response.status_code}")
            print(response.text)
            return None
    
    except Exception as e:
        print(f"❌ Erro ao enviar requisição: {str(e)}")
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
    url = f"https://{SHOPIFY_STORE}/admin/api/{API_VERSION}/shop.json"
    
    headers = {
        'X-Shopify-Access-Token': SHOPIFY_API_TOKEN
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
    
    if len(sys.argv) > 1 and sys.argv[1] == "--verificar":
        # Verificar conexão
        verificar_conexao_shopify()
    else:
        print("Uso: python shopify_fulfillment.py --verificar")
        print("Este script é para ser usado como módulo em outros scripts.")
