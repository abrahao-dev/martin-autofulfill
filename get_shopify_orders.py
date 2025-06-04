#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import sys
import requests
from datetime import datetime
from dotenv import load_dotenv

# Importar módulo de utilidades para validação de pedidos
import utils

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

# Função para buscar pedidos na Shopify
def buscar_pedidos_shopify():
    # Endpoint para pedidos
    url = f"{BASE_URL}/orders.json"

    # Parâmetros para filtrar pedidos não processados a partir de 01/06/2025
    from datetime import datetime
    data_inicio = '2025-06-01T00:00:00Z'  # Formato ISO 8601

    params = {
        'financial_status': 'paid',
        'fulfillment_status': 'unfulfilled',
        'status': 'open',
        'created_at_min': data_inicio,
        'limit': 50  # Ajuste conforme necessário
    }

    try:
        # Configurar headers com o token de acesso
        headers = {
            'X-Shopify-Access-Token': SHOPIFY_API_TOKEN,
            'Content-Type': 'application/json'
        }

        # Fazer a requisição para a API
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()  # Verificar se houve erro na requisição

        # Extrair dados da resposta
        dados = response.json()
        return dados['orders']

    except requests.exceptions.RequestException as e:
        print(f"Erro ao buscar pedidos: {e}")
        return []

# Função para processar dados do pedido no formato desejado
def processar_pedido(pedido):
    try:
        # Extrair informações básicas do pedido
        processed_order = {
            'id': pedido['id'],
            'order_number': f"#{pedido['order_number']}",  # Número do pedido com # na frente
            'nome': pedido['shipping_address']['name'] if 'shipping_address' in pedido else pedido['customer']['first_name'] + ' ' + pedido['customer']['last_name'],
            'telefone': pedido['shipping_address'].get('phone', 'Não informado') if 'shipping_address' in pedido else pedido['customer'].get('phone', 'Não informado'),
            'produto': '', # Será preenchido com o primeiro item
            'endereco': {},
            'line_items': pedido.get('line_items', []),  # Preservar line_items para fulfillment
            'location_id': utils.DEFAULT_LOCATION_ID,   # Usar location_id padrão
            'cpf': 'Não informado'  # Valor padrão para CPF
        }

        # Extrair CPF dos atributos da nota
        cpf = None
        note_attributes = pedido.get('note_attributes', [])

        # Buscar CPF nos note_attributes
        for attr in note_attributes:
            if attr.get('name', '').lower() in ['cpf', 'documento', 'cpf_cnpj']:
                cpf = attr.get('value')
                break

        # Se não encontrou nos note_attributes, tentar no billing_address.company
        if not cpf and 'billing_address' in pedido:
            cpf = pedido['billing_address'].get('company')

        # Atualizar o CPF no pedido processado se foi encontrado
        if cpf:
            processed_order['cpf'] = cpf

        # Extrair o primeiro produto (assumindo que o primeiro é o principal)
        if pedido['line_items'] and len(pedido['line_items']) > 0:
            item = pedido['line_items'][0]
            produto_nome = item['name']

            # Verificar se há informações variantes (como tamanho)
            if 'variant_title' in item and item['variant_title']:
                produto_nome += f" - {item['variant_title']}"

            processed_order['produto'] = produto_nome

        # Extrair endereço de entrega
        if 'shipping_address' in pedido:
            addr = pedido['shipping_address']

            # Tenta extrair o bairro de várias fontes possíveis
            bairro = addr.get('bairro', '')  # Se vier diretamente da API

            # Se não encontrou, tenta extrair de note_attributes
            if not bairro:
                for attr in pedido.get('note_attributes', []):
                    if attr.get('name', '').lower() in ['bairro', 'neighborhood']:
                        bairro = attr.get('value', '')
                        break

            # Se ainda não encontrou, pode estar no address2
            if not bairro and addr.get('address2'):
                bairro = addr.get('address2')

            # Inicializar o dicionário de endereço com todos os campos
            processed_order['endereco'] = {
                'rua': addr.get('address1', ''),
                'numero': '', # Vamos extrair do address1
                'complemento': addr.get('address2', ''),
                'bairro': bairro,
                'cidade': addr.get('city', ''),
                'estado': addr.get('province_code', '') or addr.get('province', ''),
                'cep': addr.get('zip', ''),
                'company': addr.get('company', '')
            }

            # Tentar extrair número da rua usando várias estratégias
            address1 = addr.get('address1', '')

            # Estratégia 1: Separado por vírgula "Rua Nome, 123"
            if ',' in address1:
                parts = address1.split(',')
                processed_order['endereco']['rua'] = parts[0].strip()
                if len(parts) > 1 and parts[1].strip().isdigit():
                    processed_order['endereco']['numero'] = parts[1].strip()

            # Estratégia 2: Número como última parte "Rua Nome 123"
            else:
                address_parts = address1.split()
                if address_parts and address_parts[-1].isdigit():
                    processed_order['endereco']['numero'] = address_parts[-1]
                    processed_order['endereco']['rua'] = ' '.join(address_parts[:-1])

        # Adicionar status inicial (pendente)
        processed_order['status'] = 'pendente'

        # Adicionar a data de criação ao pedido processado
        if 'created_at' in pedido:
            processed_order['data_criacao'] = pedido['created_at']

        # Validar pedido
        valido, mensagem = utils.validar_pedido(processed_order)
        if not valido:
            print(f"Aviso: Pedido {processed_order.get('id', 'desconhecido')} inválido: {mensagem}")
            print("Tentando padronizar o pedido...")

        # Padronizar o pedido para garantir consistência
        processed_order = utils.padronizar_pedido(processed_order)

        return processed_order

    except Exception as e:
        print(f"Erro ao processar pedido {pedido.get('id', 'desconhecido')}: {e}")
        return None

# Função principal
def main(apenas_retornar=False):
    # No modo silencioso, não exibir mensagens de log
    if not apenas_retornar:
        print("-" * 50)
        print(" CONSULTANDO PEDIDOS SHOPIFY")
        print("-" * 50)

    # Verificar configurações
    if not all([SHOPIFY_STORE, SHOPIFY_API_TOKEN]):
        if not apenas_retornar:
            print(" Erro: Credenciais da API Shopify não configuradas. Verifique seu arquivo .env")
        return

    # Buscar pedidos da Shopify
    pedidos_shopify = buscar_pedidos_shopify()
    if not apenas_retornar:
        print(f" Encontrados {len(pedidos_shopify)} pedidos não processados desde 01/06/2025")

    # Processar os pedidos obtidos
    pedidos_processados = []
    for pedido in pedidos_shopify:
        pedido_processado = processar_pedido(pedido)
        if pedido_processado:
            # Adicionar o pedido processado à lista
            pedidos_processados.append(pedido_processado)

    if not apenas_retornar:
        print(f" Processados {len(pedidos_processados)} pedidos com sucesso")
        print(f" Resultado final: {len(pedidos_processados)} pedidos pendentes")
        print("-" * 50)

    # Se a flag apenas_retornar estiver ativa, retornar os pedidos processados
    if apenas_retornar:
        # Ordenar pedidos pelo mais antigo primeiro
        pedidos_processados.sort(key=lambda x: x.get('data_criacao', ''), reverse=False)
        # Retornar a lista de pedidos
        return pedidos_processados

    # Caso contrário, retornar os pedidos processados
    return pedidos_processados

# Executar diretamente
if __name__ == "__main__":
    import sys
    # Verificar se o argumento --apenas-retornar foi passado
    apenas_retornar = '--apenas-retornar' in sys.argv
    try:
        # Se estamos apenas retornando JSON, não exibir mensagens extras
        if apenas_retornar:
            # Retornar pedidos como JSON diretamente para stdout
            pedidos = main(apenas_retornar=True)
            if pedidos:
                print(json.dumps(pedidos, ensure_ascii=False))
            else:
                print("[]")
            sys.exit(0)
        else:
            # Execução normal com saída para o console
            main(apenas_retornar=False)
    except Exception as e:
        print(f"Erro: {str(e)}", file=sys.stderr)
        sys.exit(1)
