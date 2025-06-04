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
            # Extrair order_id e line_item_id do pedido
            order_id = str(pedido_processado['id'])
            
            # Pegar o ID do primeiro item do pedido
            line_item_id = None
            if pedido_processado['line_items'] and len(pedido_processado['line_items']) > 0:
                if isinstance(pedido_processado['line_items'][0], dict) and 'id' in pedido_processado['line_items'][0]:
                    line_item_id = str(pedido_processado['line_items'][0]['id'])
            
            # Verificar se temos o line_item_id necessário
            if not line_item_id:
                return False, "Não foi possível processar o pedido: line_item_id não encontrado"
            
            # Chamar a função corretamente com todos os parâmetros necessários
            sucesso_fulfillment = False
            try:
                # A função agora retorna uma tupla (sucesso, resultado)
                sucesso_fulfillment, resultado = shopify_fulfillment.criar_fulfillment(
                    order_id=order_id,
                    line_item_id=line_item_id,
                    codigo_rastreamento=codigo_rastreamento,
                    transportadora=transportadora,
                    notificar_cliente=notificar_cliente
                )
                
                if sucesso_fulfillment:
                    mensagem_fulfillment = "Fulfillment criado com sucesso"
                else:
                    # Se não teve sucesso, o resultado pode conter detalhes do erro
                    erro_detalhes = resultado
                    if isinstance(erro_detalhes, dict) and 'errors' in erro_detalhes:
                        mensagem_fulfillment = f"Falha ao criar fulfillment: {erro_detalhes['errors']}"
                    else:
                        mensagem_fulfillment = f"Falha ao criar fulfillment: {str(erro_detalhes)}"
            except Exception as e:
                mensagem_fulfillment = f"Erro ao criar fulfillment: {str(e)}"
            
            # Adicionar status de fulfillment
            pedido_processado['fulfillment_status'] = 'concluido' if sucesso_fulfillment else 'erro'
        
        # Gerenciar persistência de dados
        pedidos_atuais = utils.carregar_pedidos("data/pedidos_pendentes.json")
        gerenciar_persistencia_pedidos(
            pedido_processado['id'],
            pedidos_atuais,
            pedido_processado=pedido_processado
        )
        
        # Montar mensagem detalhada
        msg_status = "Pedido processado com sucesso"
        
        if notificar_cliente:
            if sucesso_fulfillment:
                msg_fulfilment = ". Fulfillment criado na Shopify."
            else:
                msg_fulfilment = f". Fulfillment não criado ou com falha: {mensagem_fulfillment}"
        else:
            msg_fulfilment = ". (Fulfillment não solicitado)"
            
        return True, msg_status + msg_fulfilment 
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


def mover_para_pendentes(pedido_id):
    """
    Move um pedido processado (especialmente com erro de fulfillment) 
    de volta para a lista de pendentes.
    
    Args:
        pedido_id (str): ID do pedido a ser movido
        
    Returns:
        bool: True se o pedido foi movido com sucesso, False caso contrário
    """
    try:
        # 1. Carregar os pedidos processados e pendentes
        processados = utils.carregar_pedidos("data/pedidos_processados.json")
        pendentes = utils.carregar_pedidos("data/pedidos_pendentes.json")

        # 2. Encontrar e remover o pedido com erro
        pedido = None
        for p in processados:
            if str(p.get('id')) == str(pedido_id):
                pedido = p
                break
                
        if not pedido:
            return False
            
        # 3. Remover o pedido da lista de processados
        processados = [p for p in processados if str(p.get('id')) != str(pedido_id)]
        
        # 4. Modificar o status e remover flags de erro
        pedido['status'] = 'pendente'
        if 'erro_fulfillment' in pedido:
            pedido['erro_fulfillment'] = False
        if 'fulfillment_status' in pedido:
            pedido['fulfillment_status'] = None
        
        # Remover dados de processamento se existirem
        pedido.pop('data_processado', None)

        # 5. Adicionar novamente aos pendentes
        pendentes.append(pedido)

        # 6. Salvar os arquivos atualizados
        utils.salvar_pedidos(processados, "data/pedidos_processados.json")
        utils.salvar_pedidos(pendentes, "data/pedidos_pendentes.json")
        
        # 7. Registrar no log
        logger.registrar_operacao(
            pedido_id=pedido_id,
            pedido_numero=pedido.get('order_number', 'Desconhecido'),
            cliente=pedido.get('nome', 'Cliente'),
            operacao="mover_para_pendentes",
            resultado="sucesso",
            detalhes="Pedido com erro de fulfillment movido de volta para pendentes"
        )

        return True
    except Exception as e:
        print(f"Erro ao mover pedido para pendentes: {str(e)}")
        return False
