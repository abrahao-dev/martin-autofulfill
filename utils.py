#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de utilidades para o Martin Autofulfill
Contém funções para validação de pedidos e estruturas de dados comuns
"""

import json
from datetime import datetime

# Import para obter o location ID real da Shopify
import os

# Definição da estrutura de location_id padrão para a loja
# Este valor será substituído pelo real quando get_shopify_locations.py for executado
DEFAULT_LOCATION_ID = None

# Tenta importar o ID real do módulo de locations
try:
    from get_shopify_locations import get_default_location_id
    # Obtém o ID real do location padrão (Depósito Martin4shop)
    DEFAULT_LOCATION_ID = get_default_location_id()
    # Se não conseguiu obter, usa um fallback temporário
    if DEFAULT_LOCATION_ID is None:
        DEFAULT_LOCATION_ID = 64321927735  # Valor de exemplo da documentação
        print("Aviso: Usando location_id de fallback. Execute get_shopify_locations.py para obter o ID correto.")
except ImportError:
    # Se o módulo não existe ainda, usa o fallback
    DEFAULT_LOCATION_ID = 64321927735  # Valor de exemplo da documentação

# Lista de campos obrigatórios para um pedido válido
CAMPOS_OBRIGATORIOS = [
    'id',                  # ID do pedido na Shopify
    'order_number',        # Número do pedido formatado com #
    'nome',                # Nome do cliente
    'telefone',            # Telefone do cliente
    'produto',             # Nome do produto com variantes
    'endereco',            # Dicionário com dados do endereço
    'line_items',          # Lista de itens do pedido (necessário para fulfillment)
    'status',              # Status do pedido: pendente, processado, ignorado, erro
]

# Campos opcionais que podem estar presentes no pedido
CAMPOS_OPCIONAIS = [
    'url_shopee',        # URL do produto na Shopee
    'codigo_rastreamento', # Código de rastreamento do pedido
    'transportadora',    # Nome da transportadora
    'data_criacao',     # Data de criação do pedido
    'data_processado',  # Data de processamento do pedido
    'data_ignorado',    # Data em que o pedido foi ignorado
]

# Campos obrigatórios do endereço
CAMPOS_ENDERECO = [
    'rua',
    'numero',
    'cidade',
    'estado',
    'cep',
]

def validar_pedido(pedido):
    """
    Valida se um pedido contém todos os campos obrigatórios.

    Args:
        pedido (dict): Dicionário contendo os dados do pedido

    Returns:
        tuple: (valido, mensagem_erro) - Booleano indicando se é válido e mensagem de erro se houver
    """
    # Verificar campos obrigatórios de primeiro nível
    for campo in CAMPOS_OBRIGATORIOS:
        if campo not in pedido:
            return False, f"Campo obrigatório ausente: {campo}"

        # Verificação específica para line_items
        if campo == 'line_items' and (not isinstance(pedido[campo], list) or len(pedido[campo]) == 0):
            return False, "O pedido deve ter pelo menos um item (line_items)"

    # Verificar campos do endereço
    if not isinstance(pedido['endereco'], dict):
        return False, "Campo 'endereco' deve ser um dicionário"

    for campo in CAMPOS_ENDERECO:
        if campo not in pedido['endereco']:
            return False, f"Campo de endereço ausente: {campo}"

    # Verificar line_items para ter ao menos um item com id
    if not pedido['line_items'][0].get('id'):
        return False, "O primeiro item do pedido deve ter um ID"

    return True, "Pedido válido"

def padronizar_pedido(pedido):
    """
    Padroniza um pedido, garantindo que todos os campos necessários estejam presentes
    e com o formato correto. Adiciona valores padrão para campos ausentes.

    Args:
        pedido (dict): Dicionário contendo os dados do pedido

    Returns:
        dict: Pedido padronizado
    """
    # Criar cópia para não modificar o original
    pedido_padronizado = pedido.copy()

    # Garantir que o order_number comece com #
    if 'order_number' in pedido_padronizado and not pedido_padronizado['order_number'].startswith('#'):
        pedido_padronizado['order_number'] = f"#{pedido_padronizado['order_number']}"

    # Garantir que telefone exista
    if 'telefone' not in pedido_padronizado or not pedido_padronizado['telefone']:
        pedido_padronizado['telefone'] = "Não informado"

    # Garantir que endereco seja um dicionário
    if 'endereco' not in pedido_padronizado or not isinstance(pedido_padronizado['endereco'], dict):
        pedido_padronizado['endereco'] = {}

    # Garantir campos do endereço
    for campo in CAMPOS_ENDERECO:
        if campo not in pedido_padronizado['endereco']:
            pedido_padronizado['endereco'][campo] = ""

    # Garantir que location_id esteja presente
    if 'location_id' not in pedido_padronizado:
        pedido_padronizado['location_id'] = DEFAULT_LOCATION_ID

    # Garantir que o campo status exista e seja válido
    if 'status' not in pedido_padronizado:
        pedido_padronizado['status'] = 'pendente'
    elif pedido_padronizado['status'] not in ['pendente', 'processado', 'ignorado', 'erro']:
        pedido_padronizado['status'] = 'pendente'

    # Garantir que data_criacao exista
    if 'data_criacao' not in pedido_padronizado:
        pedido_padronizado['data_criacao'] = datetime.now().isoformat()

    return pedido_padronizado

def salvar_pedidos(pedidos, arquivo):
    """
    Salva uma lista de pedidos em um arquivo JSON, garantindo que apenas pedidos válidos sejam salvos.

    Args:
        pedidos (list): Lista de dicionários de pedidos
        arquivo (str): Caminho do arquivo para salvar

    Returns:
        tuple: (sucesso, mensagem) - Indica se o salvamento foi bem-sucedido e uma mensagem
    """
    # Verificar se pedidos é uma lista
    if not isinstance(pedidos, list):
        return False, "Os pedidos devem estar em formato de lista"

    # Validar e padronizar cada pedido
    pedidos_validos = []
    pedidos_invalidos = []

    for pedido in pedidos:
        valido, mensagem = validar_pedido(pedido)
        if valido:
            # Padronizar antes de salvar
            pedidos_validos.append(padronizar_pedido(pedido))
        else:
            pedidos_invalidos.append((pedido.get('id', 'Desconhecido'), mensagem))

    # Se houver pedidos inválidos, logar informação (mas continuar salvando os válidos)
    if pedidos_invalidos:
        print(f"Aviso: {len(pedidos_invalidos)} pedidos inválidos não foram salvos:")
        for id_pedido, erro in pedidos_invalidos:
            print(f"  - Pedido {id_pedido}: {erro}")

    # Ordenar os pedidos pelo order_number antes de salvar
    # Remove o '#' e converte para int para garantir ordenação numérica correta
    pedidos_ordenados = sorted(pedidos_validos, key=lambda x: int(x.get('order_number', '0').replace('#', '')))

    try:
        with open(arquivo, 'w', encoding='utf-8') as file:
            json.dump(pedidos_ordenados, file, ensure_ascii=False, indent=4)
        return True, "Salvo com sucesso"
    except Exception as e:
        return False, str(e)

def carregar_pedidos(arquivo):
    """
    Carrega pedidos de um arquivo JSON e os padroniza.

    Args:
        arquivo (str): Caminho do arquivo para carregar

    Returns:
        list: Lista de pedidos carregados e padronizados
    """
    try:
        with open(arquivo, 'r', encoding='utf-8') as file:
            pedidos = json.load(file)

        # Padronizar cada pedido carregado
        pedidos_padronizados = []
        for pedido in pedidos:
            try:
                # Tentar padronizar mesmo que o pedido não seja totalmente válido
                pedidos_padronizados.append(padronizar_pedido(pedido))
            except Exception as e:
                print(f"Aviso: Erro ao padronizar pedido {pedido.get('id', 'Desconhecido')}: {str(e)}")

        return pedidos_padronizados
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        print(f"Erro: Arquivo {arquivo} não contém JSON válido")
        return []
    except Exception as e:
        print(f"Erro ao carregar pedidos: {str(e)}")
        return []


def extract_numero(address: str) -> str:
    """
    Extrai o número de um endereço de rua.
    
    Args:
        address (str): Endereço da rua (ex: "Rua Forte William 100")
        
    Returns:
        str: Número extraído ou string vazia se não encontrado
    """
    if not address:
        return ""
        
    # Tenta extrair o número no final do endereço
    for word in address.split():
        if word.isdigit():
            return word
    return ""

def extract_bairro(address2: str) -> str:
    """
    Tenta extrair o bairro do complemento ou outros campos de endereço.
    
    Args:
        address2 (str): Geralmente o campo de complemento que pode conter o bairro
        
    Returns:
        str: Possível bairro extraído ou string vazia
    """
    if address2:
        return address2.strip()
    return ""

def formatar_endereco_shopee(pedido):
    """
    Formata o endereço no padrão exigido pela Shopee para facilitar o preenchimento
    do formulário de endereço de entrega.

    Args:
        pedido (dict): Dicionário contendo os dados do pedido

    Returns:
        str: Texto formatado com os campos no padrão da Shopee
    """
    if not pedido or not isinstance(pedido, dict):
        return "Dados de endereço não disponíveis"

    endereco = pedido.get('endereco', {})
    
    # Tentar extrair CPF de note_attributes se não estiver já no pedido
    cpf = pedido.get('cpf', 'Não informado')
    
    # Tentar extrair ou melhorar outros campos
    bairro = endereco.get('bairro', '') or extract_bairro(endereco.get('complemento', ''))
    numero = endereco.get('numero', '') or extract_numero(endereco.get('rua', ''))
    
    # Formatar cada campo conforme padrão da Shopee na ordem solicitada
    return f"""\
Nome Completo: {pedido.get('nome', '')}
Telefone: {pedido.get('telefone', '')}
CEP: {endereco.get('cep', '')}
Estado - Cidade: {endereco.get('estado', '')} - {endereco.get('cidade', '')}
Bairro: {bairro}
Rua / Avenida: {endereco.get('rua', '')}
Número: {numero}
Complemento: {endereco.get('complemento', '')}
CPF: {cpf}
"""
