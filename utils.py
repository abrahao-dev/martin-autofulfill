#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de utilidades para o Martin Autofulfill
Contém funções para validação de pedidos e estruturas de dados comuns
"""

import json
from datetime import datetime

# Definição da estrutura de location_id padrão para a loja
DEFAULT_LOCATION_ID = 1

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
            
    # Salvar pedidos válidos
    try:
        with open(arquivo, 'w', encoding='utf-8') as file:
            json.dump(pedidos_validos, file, ensure_ascii=False, indent=4)
        return True, f"Salvos {len(pedidos_validos)} pedidos em {arquivo}"
    except Exception as e:
        return False, f"Erro ao salvar pedidos: {str(e)}"

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


def formatar_endereco_shopee(pedido):
    """
    Formata o endereço no padrão exigido pela Shopee para facilitar o preenchimento
    do formulário de endereço de entrega.
    
    Args:
        pedido (dict): Dicionário contendo os dados do pedido
        
    Returns:
        str: Texto formatado com os campos no padrão da Shopee
    """
    if not pedido or not isinstance(pedido, dict) or 'endereco' not in pedido:
        return "Dados de endereço não disponíveis"
        
    endereco = pedido.get('endereco', {})
    
    # Formatar cada campo conforme padrão da Shopee
    return f"""\
Nome Completo: {pedido.get('nome', '')}
Telefone: {pedido.get('telefone', '')}
CPF: {pedido.get('cpf', '')}
CEP: {endereco.get('cep', '')}
Estado - Cidade: {endereco.get('estado', '')} - {endereco.get('cidade', '')}
Bairro: {endereco.get('bairro', '')}
Rua / Avenida: {endereco.get('rua', '')}
Número: {endereco.get('numero', '')}
Complemento: {endereco.get('complemento', '')}
"""
