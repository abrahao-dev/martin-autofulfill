#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo para gerenciamento de produtos Shopee e sua correspondência com produtos Shopify
"""

import os
import json
import re
from datetime import datetime
import logger

# Configuração
PRODUTOS_DB_PATH = os.path.join("data", "produtos_shopee.json")
os.makedirs(os.path.dirname(PRODUTOS_DB_PATH), exist_ok=True)

def carregar_produtos():
    """
    Carrega o banco de dados de produtos Shopee
    
    Returns:
        list: Lista de produtos com correspondências
    """
    if not os.path.exists(PRODUTOS_DB_PATH):
        # Se o arquivo não existir, criar um vazio
        salvar_produtos([])
        return []
        
    try:
        with open(PRODUTOS_DB_PATH, 'r', encoding='utf-8') as file:
            return json.load(file)
    except Exception as e:
        logger.registrar_erro(f"Erro ao carregar banco de produtos: {str(e)}")
        return []

def salvar_produtos(produtos):
    """
    Salva a lista de produtos no arquivo
    
    Args:
        produtos (list): Lista de produtos a salvar
    """
    try:
        with open(PRODUTOS_DB_PATH, 'w', encoding='utf-8') as file:
            json.dump(produtos, file, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.registrar_erro(f"Erro ao salvar banco de produtos: {str(e)}")

def adicionar_produto(nome_produto, palavras_chave, url_shopee):
    """
    Adiciona ou atualiza um produto no banco de dados
    
    Args:
        nome_produto (str): Nome do produto na Shopify
        palavras_chave (list): Lista de palavras-chave para correspondência
        url_shopee (str): URL do produto na Shopee
        
    Returns:
        bool: True se adicionado com sucesso, False caso contrário
    """
    try:
        produtos = carregar_produtos()
        
        # Verificar se já existe
        for produto in produtos:
            if produto.get('nome') == nome_produto or produto.get('url_shopee') == url_shopee:
                # Atualizar produto existente
                produto['nome'] = nome_produto
                produto['palavras_chave'] = palavras_chave
                produto['url_shopee'] = url_shopee
                produto['atualizado_em'] = datetime.now().isoformat()
                salvar_produtos(produtos)
                return True
                
        # Se não existe, adicionar novo
        novo_produto = {
            'nome': nome_produto,
            'palavras_chave': palavras_chave,
            'url_shopee': url_shopee,
            'criado_em': datetime.now().isoformat(),
            'atualizado_em': datetime.now().isoformat()
        }
        produtos.append(novo_produto)
        salvar_produtos(produtos)
        return True
        
    except Exception as e:
        logger.registrar_erro(f"Erro ao adicionar produto: {str(e)}")
        return False

def remover_produto(nome_produto=None, url_shopee=None):
    """
    Remove um produto do banco de dados
    
    Args:
        nome_produto (str, optional): Nome do produto para remover
        url_shopee (str, optional): URL do produto para remover
        
    Returns:
        bool: True se removido com sucesso, False caso contrário
    """
    if not nome_produto and not url_shopee:
        return False
        
    try:
        produtos = carregar_produtos()
        produtos_filtrados = []
        removido = False
        
        for produto in produtos:
            if (nome_produto and produto.get('nome') == nome_produto) or \
               (url_shopee and produto.get('url_shopee') == url_shopee):
                removido = True
                continue
            produtos_filtrados.append(produto)
            
        if removido:
            salvar_produtos(produtos_filtrados)
        return removido
        
    except Exception as e:
        logger.registrar_erro(f"Erro ao remover produto: {str(e)}")
        return False

def encontrar_url_shopee_por_nome(nome_produto):
    """
    Busca uma URL da Shopee correspondente a um nome de produto
    
    Args:
        nome_produto (str): Nome do produto para buscar
        
    Returns:
        str: URL da Shopee se encontrada, None caso contrário
    """
    if not nome_produto:
        return None
        
    nome_produto = nome_produto.lower()
    produtos = carregar_produtos()
    
    # Primeiro verificamos correspondência exata
    for produto in produtos:
        if produto.get('nome', '').lower() == nome_produto:
            return produto.get('url_shopee')
    
    # Depois verificamos palavras-chave
    for produto in produtos:
        for palavra_chave in produto.get('palavras_chave', []):
            if palavra_chave.lower() in nome_produto:
                return produto.get('url_shopee')
    
    # Por fim, verificamos correspondência parcial no nome
    for produto in produtos:
        produto_nome = produto.get('nome', '').lower()
        if produto_nome in nome_produto or nome_produto in produto_nome:
            return produto.get('url_shopee')
    
    return None
