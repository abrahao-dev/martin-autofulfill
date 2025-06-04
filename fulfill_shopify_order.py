#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sys
import requests
from dotenv import load_dotenv

# Importar função para obter location_id real
from get_shopify_locations import get_default_location_id

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da API Shopify
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')
SHOPIFY_API_TOKEN = os.getenv('SHOPIFY_API_TOKEN')
SHOPIFY_API_PASSWORD = SHOPIFY_API_TOKEN  # Mantendo nomenclatura compatível com documentação
SHOPIFY_API_VERSION = os.getenv('SHOPIFY_API_VERSION', '2023-10')

# URL base para a API Shopify
# Verificar se o nome da loja já inclui '.myshopify.com'
store_domain = SHOPIFY_STORE
if '.myshopify.com' not in store_domain:
    store_domain = f"{store_domain}.myshopify.com"

# URL base para a API Shopify usando o token de acesso
BASE_URL = f"https://{store_domain}/admin/api/{SHOPIFY_API_VERSION}"

def fulfill_order(order_id, line_item_id, tracking_number, location_id=None):
    """
    Marca um item de um pedido como enviado (fulfilled) na Shopify.
    
    Args:
        order_id (int): ID do pedido na Shopify
        line_item_id (int): ID do item de linha a ser marcado como enviado
        tracking_number (str): Número de rastreio do pedido
        location_id (int, optional): ID do local de inventário. Se None, busca o padrão.
        
    Returns:
        bool: True se o envio foi registrado com sucesso, False caso contrário
        dict: Resposta da API ou mensagem de erro
    """
    # Se não foi fornecido um location_id, buscar o padrão
    if location_id is None:
        location_id = get_default_location_id()
        if location_id is None:
            return False, {"error": "Não foi possível obter o location_id padrão"}
    
    # Endpoint para fulfillment
    url = f"{BASE_URL}/orders/{order_id}/fulfillments.json"
    
    # Montar payload conforme documentação da Shopify
    payload = {
        "fulfillment": {
            "location_id": location_id,
            "tracking_number": tracking_number,
            "tracking_urls": ["https://anjunexpress.com.br/rastreio"],
            "notify_customer": True,
            "line_items": [
                {
                    "id": line_item_id,
                    "quantity": 1
                }
            ]
        }
    }
    
    # Configurar headers com o token de acesso
    headers = {
        "X-Shopify-Access-Token": SHOPIFY_API_PASSWORD,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    try:
        # Fazer a requisição POST para a API
        response = requests.post(url, json=payload, headers=headers)
        
        # Verificar se houve erro na requisição
        if response.status_code >= 200 and response.status_code < 300:
            return True, response.json()
        else:
            return False, {
                "error": f"Erro na API (status {response.status_code})",
                "details": response.text
            }
    
    except requests.exceptions.RequestException as e:
        return False, {"error": str(e)}

def main():
    """
    Função principal para testar o registro de envio em um pedido.
    """
    if len(sys.argv) < 4:
        print("Uso: python fulfill_shopify_order.py <order_id> <line_item_id> <tracking_number>")
        return
    
    try:
        order_id = int(sys.argv[1])
        line_item_id = int(sys.argv[2])
        tracking_number = sys.argv[3]
        
        print("-" * 50)
        print(" REGISTRANDO ENVIO NA SHOPIFY")
        print("-" * 50)
        print(f" Pedido: {order_id}")
        print(f" Item: {line_item_id}")
        print(f" Rastreio: {tracking_number}")
        
        # Buscar location_id real antes de registrar o envio
        location_id = get_default_location_id()
        if location_id:
            print(f" Location ID: {location_id}")
        else:
            print(" ERRO: Não foi possível obter o location_id")
            return
        
        # Registrar envio
        sucesso, resposta = fulfill_order(order_id, line_item_id, tracking_number, location_id)
        
        if sucesso:
            print("\n ✅ Envio registrado com sucesso!")
            print(f" ID do fulfillment: {resposta.get('fulfillment', {}).get('id', 'N/A')}")
        else:
            print("\n ❌ Erro ao registrar envio:")
            print(f" {resposta.get('error', 'Erro desconhecido')}")
            if 'details' in resposta:
                print(f" Detalhes: {resposta['details']}")
        
        print("-" * 50)
    
    except ValueError:
        print("Erro: order_id e line_item_id devem ser números inteiros")
    except Exception as e:
        print(f"Erro inesperado: {e}")

if __name__ == "__main__":
    main()
