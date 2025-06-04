#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface para gerenciamento de produtos e correspondências Shopify-Shopee
"""

import streamlit as st
from datetime import datetime

import shopee_produtos
import logger

def app():
    st.title("Gerenciamento de Produtos Shopify-Shopee")
    
    # Carregar produtos existentes
    produtos = shopee_produtos.carregar_produtos()
    
    # Exibir estatísticas
    st.info(f"Total de {len(produtos)} produtos cadastrados")
    
    # Interface dividida em duas colunas: cadastro e listagem
    col1, col2 = st.columns([1, 2])
    
    # Coluna 1: Cadastro de novos produtos
    with col1:
        st.subheader("Cadastrar Novo Produto")
        with st.form(key="novo_produto_form"):
            nome_produto = st.text_input("Nome do produto na Shopify")
            
            # Campo para palavras-chave (uma por linha)
            palavras_chave_text = st.text_area("Palavras-chave (uma por linha)")
            
            url_shopee = st.text_input("URL do produto na Shopee")
            
            submit = st.form_submit_button("Cadastrar Produto")
            
            if submit:
                if nome_produto and url_shopee:
                    # Processar palavras-chave
                    palavras_chave = [p.strip() for p in palavras_chave_text.split("\n") if p.strip()]
                    
                    # Adicionar ao banco de dados
                    sucesso = shopee_produtos.adicionar_produto(
                        nome_produto=nome_produto,
                        palavras_chave=palavras_chave,
                        url_shopee=url_shopee
                    )
                    
                    if sucesso:
                        st.success("Produto cadastrado com sucesso!")
                        logger.registrar_operacao(
                            pedido_id="-",
                            pedido_numero="-",
                            cliente="-",
                            operacao="cadastro_produto",
                            resultado="sucesso",
                            detalhes=f"Produto: {nome_produto}, URL Shopee: {url_shopee}"
                        )
                        # Recarregar a página
                        st.rerun()
                    else:
                        st.error("Erro ao cadastrar produto.")
                else:
                    st.warning("Preencha o nome do produto e a URL da Shopee.")
    
    # Coluna 2: Lista de produtos cadastrados
    with col2:
        st.subheader("Produtos Cadastrados")
        
        # Campo de busca
        busca = st.text_input("Buscar produto", "")
        
        produtos_filtrados = produtos
        if busca:
            busca = busca.lower()
            produtos_filtrados = [p for p in produtos if (
                busca in p.get('nome', '').lower() or 
                busca in p.get('url_shopee', '').lower() or
                any(busca in palavra.lower() for palavra in p.get('palavras_chave', []))
            )]
        
        # Exibir produtos em cards
        for i, produto in enumerate(produtos_filtrados):
            with st.container():
                st.divider()
                
                # Dados do produto
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(produto.get('nome', 'Sem nome'))
                    st.write(f"**URL Shopee:** [{produto.get('url_shopee', 'N/A')}]({produto.get('url_shopee', '#')})")
                    
                    # Palavras-chave
                    if produto.get('palavras_chave'):
                        st.write("**Palavras-chave:**")
                        tags = ", ".join(produto.get('palavras_chave', []))
                        st.write(f"_{tags}_")
                    
                    # Data de atualização
                    if produto.get('atualizado_em'):
                        try:
                            data = datetime.fromisoformat(produto.get('atualizado_em'))
                            data_formatada = data.strftime('%d/%m/%Y %H:%M')
                            st.write(f"**Atualizado em:** {data_formatada}")
                        except:
                            pass
                
                with col2:
                    # Botão para excluir
                    if st.button("🗑️ Excluir", key=f"del_{i}"):
                        if shopee_produtos.remover_produto(nome_produto=produto.get('nome')):
                            st.success("Produto removido!")
                            logger.registrar_operacao(
                                pedido_id="-",
                                pedido_numero="-",
                                cliente="-",
                                operacao="remocao_produto",
                                resultado="sucesso",
                                detalhes=f"Produto: {produto.get('nome')}"
                            )
                            # Recarregar a página
                            st.rerun()
                        else:
                            st.error("Erro ao remover produto.")

if __name__ == "__main__":
    app()
