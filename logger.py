#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Módulo de logging para o Martin Autofulfill
Gerencia o registro de operações em arquivos de log
"""

import os
import csv
from datetime import datetime
import logging

# Configurar diretórios
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

# Configurar arquivo de log CSV
CSV_LOG_FILE = os.path.join(LOG_DIR, "operacoes.csv")
LOG_FILE = os.path.join(LOG_DIR, "martin_autofulfill.log")

# Configurar o logger padrão do Python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def inicializar_csv_log():
    """Inicializa o arquivo CSV de log se não existir"""
    if not os.path.exists(CSV_LOG_FILE):
        with open(CSV_LOG_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                'data_hora', 
                'pedido_id', 
                'pedido_numero', 
                'cliente', 
                'operacao', 
                'resultado', 
                'detalhes'
            ])

def registrar_operacao(pedido_id, pedido_numero, cliente, operacao, resultado, detalhes=""):
    """
    Registra uma operação no log CSV
    
    Args:
        pedido_id (int/str): ID do pedido
        pedido_numero (str): Número formatado do pedido (ex: #1001)
        cliente (str): Nome do cliente
        operacao (str): Tipo de operação (ex: processamento, ignorar)
        resultado (str): Resultado da operação (sucesso ou erro)
        detalhes (str): Detalhes adicionais da operação
    """
    # Garantir que o arquivo existe
    inicializar_csv_log()
    
    # Data e hora atual
    data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Registrar no CSV
    with open(CSV_LOG_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            data_hora,
            pedido_id,
            pedido_numero,
            cliente,
            operacao,
            resultado,
            detalhes
        ])
    
    # Registrar também no log do sistema
    status = "✅" if resultado == "sucesso" else "❌"
    logger.info(f"{status} {operacao.upper()} - Pedido {pedido_numero} - Cliente: {cliente} - {resultado}")
    if detalhes:
        logger.info(f"    Detalhes: {detalhes}")

def registrar_erro(mensagem, pedido_id=None, pedido_numero=None):
    """
    Registra um erro no log
    
    Args:
        mensagem (str): Mensagem de erro
        pedido_id (int/str): ID do pedido, se aplicável
        pedido_numero (str): Número do pedido, se aplicável
    """
    if pedido_id and pedido_numero:
        logger.error(f"ERRO - Pedido {pedido_numero} (ID: {pedido_id}): {mensagem}")
    else:
        logger.error(f"ERRO: {mensagem}")
