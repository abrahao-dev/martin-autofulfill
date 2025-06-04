#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de processamento de pedidos do Martin Autofulfill
Contém as funções centrais para tratamento de pedidos
"""

import os
import json
from datetime import datetime

# Importar módulos do projeto
import utils
import shopify_fulfillment
import logger

def processar_pedido_completo(pedido, codigo_rastreamento="", transportadora="", notificar_cliente=True):
    """
    Função central para processamento de um pedido.
    
    Args:
        pedido (dict): Dicionário do pedido
        codigo_rastreamento (str): Código de rastreamento do pedido
        transportadora (str): Nome da transportadora
        notificar_cliente (bool): Se deve notificar o cliente via Shopify
        
    Returns:
        tuple: (sucesso, mensagem) onde sucesso é um booleano e mensagem é texto informativo
    """
    try:
        # Validar pedido
        if not pedido or not isinstance(pedido, dict) or 'id' not in pedido:
            return False, "Pedido inválido"

        # Validar pedido com função utils
        valido, mensagem = utils.validar_pedido(pedido)
        if not valido:
            return False, f"Pedido inválido: {mensagem}"
        
        # Criar cópia do pedido para não modificar o original
        pedido_processado = pedido.copy()
        
        # Validar e padronizar o pedido
        pedido_processado = utils.padronizar_pedido(pedido_processado)
        
        # Atualizar status e data de processamento
        pedido_processado['status'] = 'processado'
        pedido_processado['data_processado'] = datetime.now().isoformat()
        pedido_processado['codigo_rastreamento'] = codigo_rastreamento
        pedido_processado['transportadora'] = transportadora
        
        # Criar o fulfillment na Shopify se solicitado
        sucesso_fulfillment = False
        mensagem_fulfillment = ""
        
        if notificar_cliente and 'line_items' in pedido_processado and len(pedido_processado['line_items']) > 0:
            sucesso_fulfillment, mensagem_fulfillment = shopify_fulfillment.criar_fulfillment(
                pedido_processado,
                codigo_rastreamento=codigo_rastreamento,
                transportadora=transportadora
            )
            
            # Adicionar status de fulfillment
            pedido_processado['fulfillment_status'] = 'concluido' if sucesso_fulfillment else 'erro'
        
        # Gerenciar persistência de dados
        pedidos_atuais = utils.carregar_pedidos("data/pedidos_pendentes.json")
        gerenciar_persistencia_pedidos(
            pedido_processado['id'],
            pedidos_atuais,
            pedido_processado=pedido_processado
        )
        
        return True, "Pedido processado com sucesso" + \
              (". Fulfillment criado na Shopify." if sucesso_fulfillment else 
               ". Fulfillment não criado ou com falha.")
                
    except Exception as e:
        return False, f"Erro ao processar pedido: {str(e)}"

def ignorar_pedido_completo(pedido):
    """
    Função central para marcar um pedido como ignorado.
    
    Args:
        pedido (dict): Dicionário contendo os dados do pedido
        
    Returns:
        tuple: (sucesso, mensagem) - Indica se o processamento foi bem-sucedido e uma mensagem
    """
    # Verificar se o pedido é válido
    if not pedido or not isinstance(pedido, dict) or 'id' not in pedido:
        return False, "Pedido inválido"
    
    try:
        # Validar pedido com função utils
        valido, mensagem = utils.validar_pedido(pedido)
        if not valido:
            return False, mensagem
            
        # Criar cópia do pedido para não modificar o original
        pedido_ignorado = pedido.copy()
        
        # Atualizar status do pedido
        pedido_ignorado['status'] = 'ignorado'
        pedido_ignorado['data_ignorado'] = datetime.now().isoformat()
        
        # Gerenciar persistência dos pedidos
        gerenciar_persistencia_pedidos(pedido_ignorado)
        
        # Registrar no log
        logger.registrar_operacao(
            pedido_id=pedido_ignorado['id'],
            pedido_numero=pedido_ignorado['order_number'],
            cliente=pedido_ignorado['nome'],
            operacao="ignorar",
            resultado="sucesso",
            detalhes="Pedido marcado como ignorado pelo usuário"
        )
        
        return True, "Pedido marcado como ignorado com sucesso"
        
    except Exception as e:
        return False, f"Erro ao ignorar pedido: {str(e)}"

def gerenciar_persistencia_pedidos(pedido_id, pedidos_atuais, pedido_processado=None, pedido_ignorado=None):
    """
    Gerencia a persistência de pedidos entre as diferentes listas (pendentes, processados, ignorados)
    
    Args:
        pedido_id (str): ID do pedido a ser gerenciado
        pedidos_atuais (list): Lista atual de pedidos pendentes
        pedido_processado (dict): Pedido processado, se houver
        pedido_ignorado (dict): Pedido ignorado, se houver
        
    Returns:
        list: Lista atualizada de pedidos pendentes
    """
    # Remover o pedido da lista de pendentes
    pedidos_pendentes = [p for p in pedidos_atuais if str(p['id']) != str(pedido_id)]
    
    # Salvar a nova lista de pedidos pendentes
    utils.salvar_pedidos(pedidos_pendentes, "data/pedidos_pendentes.json")
    
    # Se temos um pedido processado, adicioná-lo à lista correspondente
    if pedido_processado:
        # Carregar lista existente
        pedidos_processados = utils.carregar_pedidos("data/pedidos_processados.json")
        pedidos_processados.append(pedido_processado)
        # Salvar lista atualizada
        utils.salvar_pedidos(pedidos_processados, "data/pedidos_processados.json")
    
    # Se temos um pedido ignorado, adicioná-lo à lista correspondente  
    if pedido_ignorado:
        # Carregar lista existente
        pedidos_ignorados = utils.carregar_pedidos("data/pedidos_ignorados.json")
        pedidos_ignorados.append(pedido_ignorado)
        # Salvar lista atualizada
        utils.salvar_pedidos(pedidos_ignorados, "data/pedidos_ignorados.json")
    
    return pedidos_pendentes
