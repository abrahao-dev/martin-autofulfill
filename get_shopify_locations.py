#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sys
import requests
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da API Shopify
SHOPIFY_STORE = os.getenv('SHOPIFY_STORE')
SHOPIFY_API_TOKEN = os.getenv('SHOPIFY_API_TOKEN')
SHOPIFY_API_VERSION = os.getenv('SHOPIFY_API_VERSION', '2023-10')

# URL base para a API Shopify
# Verificar se o nome da loja já inclui '.myshopify.com'
store_domain = SHOPIFY_STORE
if '.myshopify.com' not in store_domain:
    store_domain = f"{store_domain}.myshopify.com"

# URL base para a API Shopify usando o token de acesso
BASE_URL = f"https://{store_domain}/admin/api/{SHOPIFY_API_VERSION}"

def get_shopify_locations():
    """
    Busca todos os locais de inventário (locations) disponíveis na loja Shopify.
    
    Returns:
        list: Lista de locations com seus IDs e nomes
        None: Em caso de erro
    """
    # Endpoint para locations
    url = f"{BASE_URL}/locations.json"
    
    try:
        # Configurar headers com o token de acesso
        headers = {
            'X-Shopify-Access-Token': SHOPIFY_API_TOKEN,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        # Fazer a requisição para a API
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Verificar se houve erro na requisição
        
        # Extrair dados da resposta
        dados = response.json()
        return dados['locations']
    
    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar locations: {e}")
        return None

def get_default_location_id():
    """
    Busca o ID do local principal (geralmente "Depósito Martin4shop") para fulfillment.
    
    Returns:
        int: ID do location padrão para fulfillment
        None: Em caso de erro
    """
    locations = get_shopify_locations()
    
    if not locations:
        print("Não foi possível obter os locations da Shopify")
        return None
    
    # Procurar por "Depósito Martin4shop"
    for location in locations:
        if "Depósito Martin4shop" in location['name']:
            return location['id']
    
    # Se não encontrar o depósito específico, usar o primeiro location
    if locations:
        print(f"Aviso: Location 'Depósito Martin4shop' não encontrado. Usando {locations[0]['name']}")
        return locations[0]['id']
    
    return None

def main():
    """
    Função principal que busca e exibe todos os locations disponíveis.
    """
    print("-" * 50)
    print(" CONSULTANDO LOCATIONS SHOPIFY")
    print("-" * 50)
    
    # Verificar configurações
    if not all([SHOPIFY_STORE, SHOPIFY_API_TOKEN]):
        print(" Erro: Credenciais da API Shopify não configuradas. Verifique seu arquivo .env")
        return
    
    # Buscar locations da Shopify
    locations = get_shopify_locations()
    if not locations:
        print(" Erro: Não foi possível obter os locations")
        return
    
    print(f" Encontrados {len(locations)} locations:")
    for location in locations:
        print(f" - ID: {location['id']}, Nome: {location['name']}")
    
    # Buscar o location ID padrão
    default_id = get_default_location_id()
    if default_id:
        print(f"\n ID do location padrão para fulfillment: {default_id}")
    else:
        print("\n Não foi possível determinar o location padrão")
    
    print("-" * 50)

# Executar diretamente
if __name__ == "__main__":
    try:
        # Verificar se queremos apenas retornar o ID padrão (útil para scripts)
        if '--apenas-id' in sys.argv:
            location_id = get_default_location_id()
            if location_id:
                print(location_id)
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            # Execução normal com output completo
            main()
    except Exception as e:
        print(f"Erro: {str(e)}", file=sys.stderr)
        sys.exit(1)
