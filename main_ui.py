import streamlit as st
import json
import os
import subprocess
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(page_title="Martin Autofulfill", layout="wide")

# Função para calcular tempo decorrido desde a criação do pedido
def calcular_tempo_decorrido(data_criacao_str):
    # Converter string de data para objeto datetime
    try:
        # Tentar formato ISO
        data_criacao = datetime.fromisoformat(data_criacao_str.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        try:
            # Tentar outro formato comum
            data_criacao = datetime.strptime(data_criacao_str, '%Y-%m-%dT%H:%M:%S%z')
        except (ValueError, AttributeError):
            # Se não conseguir converter, retornar mensagem padrão
            return 'Data desconhecida'
    
    # Data atual (usando a data do sistema)
    agora = datetime.now(data_criacao.tzinfo)
    
    # Calcular diferença
    diferenca = agora - data_criacao
    
    # Formatar a saída
    dias = diferenca.days
    horas = diferenca.seconds // 3600
    
    if dias > 0:
        return f'{dias} dias e {horas} horas'
    else:
        return f'{horas} horas'

# Função para formatar códigos de escape unicode no texto
def formatar_texto(texto):
    if not isinstance(texto, str):
        return texto
        
    # Substituir códigos de escape Unicode comuns
    texto = texto.replace('u00e1', 'á').replace('u00e3', 'ã').replace('u00e9', 'é')
    texto = texto.replace('u00ed', 'í').replace('u00f3', 'ó').replace('u00fa', 'ú')
    texto = texto.replace('u00e0', 'à').replace('u00f5', 'õ').replace('u00e2', 'â')
    texto = texto.replace('u00ea', 'ê').replace('u00f4', 'ô').replace('u00c7', 'Ç')
    texto = texto.replace('u00e7', 'ç').replace('u00ba', 'º').replace('u00aa', 'ª')
    return texto

# Função para buscar os pedidos da API Shopify
def buscar_pedidos_shopify():
    try:
        # Executar o script get_shopify_orders.py com a flag --apenas-retornar
        result = subprocess.run(['python', 'get_shopify_orders.py', '--apenas-retornar'], 
                             capture_output=True, text=True, check=True, 
                             cwd=os.path.dirname(os.path.abspath(__file__)))
        
        # Converter a saída JSON para uma lista de pedidos Python
        import io
        pedidos = json.load(io.StringIO(result.stdout))
        
        # Ordenar pedidos pelo mais antigo primeiro
        pedidos.sort(key=lambda x: x.get('data_criacao', ''), reverse=False)
        
        return pedidos
    except subprocess.CalledProcessError as e:
        st.error(f"Erro ao buscar pedidos: {e.stderr}")
        return []

# Função para salvar os pedidos de volta ao arquivo JSON
def salvar_pedidos(pedidos, arquivo):
    try:
        with open(arquivo, 'w', encoding='utf-8') as file:
            json.dump(pedidos, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"Erro ao salvar pedidos: {str(e)}")
        return False

# Função para carregar pedidos ignorados
def carregar_pedidos_ignorados():
    try:
        with open('pedidos_ignorados.json', 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        # Se o arquivo não existir, cria uma lista vazia
        with open('pedidos_ignorados.json', 'w', encoding='utf-8') as file:
            json.dump([], file)
        return []
    except json.JSONDecodeError:
        st.error("Erro ao decodificar o arquivo de pedidos ignorados!")
        with open('pedidos_ignorados.json', 'w', encoding='utf-8') as file:
            json.dump([], file)
        return []

# Função para ignorar um pedido
def ignorar_pedido(pedido_id, pedidos_atuais):
    # Encontrar o pedido pelo ID
    pedido_ignorado = None
    pedidos_restantes = []
    
    for pedido in pedidos_atuais:
        if str(pedido['id']) == str(pedido_id):
            pedido_ignorado = pedido
            # Marcar como ignorado
            pedido_ignorado['status'] = 'ignorado'
            pedido_ignorado['data_ignorado'] = datetime.now().isoformat()
        else:
            pedidos_restantes.append(pedido)
    
    if pedido_ignorado:
        # Carregar pedidos ignorados existentes
        pedidos_ignorados = carregar_pedidos_ignorados()
        # Adicionar o novo pedido ignorado
        pedidos_ignorados.append(pedido_ignorado)
        # Salvar pedidos ignorados
        salvar_pedidos(pedidos_ignorados, 'pedidos_ignorados.json')
        
    return pedidos_restantes

# Função para processar um pedido
def processar_pedido(pedido_id, codigo_rastreamento, transportadora, pedidos_atuais):
    # Encontrar o pedido pelo ID
    pedido_processado = None
    pedidos_restantes = []
    
    for pedido in pedidos_atuais:
        if str(pedido['id']) == str(pedido_id):
            pedido_processado = pedido
            # Marcar como processado
            pedido_processado['status'] = 'processado'
            pedido_processado['data_processado'] = datetime.now().isoformat()
            pedido_processado['codigo_rastreamento'] = codigo_rastreamento
            pedido_processado['transportadora'] = transportadora
        else:
            pedidos_restantes.append(pedido)
    
    if pedido_processado:
        # Carregar pedidos processados existentes
        try:
            with open('pedidos_processados.json', 'r', encoding='utf-8') as file:
                pedidos_processados = json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            pedidos_processados = []
        
        # Adicionar o novo pedido processado
        pedidos_processados.append(pedido_processado)
        # Salvar pedidos processados
        salvar_pedidos(pedidos_processados, 'pedidos_processados.json')
        
    return pedidos_restantes

# Removida função formatar_id_pedido - Agora usando order_number diretamente da API Shopify

# Título do aplicativo
st.title("Martin Autofulfill - Gerenciador de Pedidos")
st.subheader("Processamento automático de pedidos Shopify para Shopee")

# Criar abas para navegar entre pedidos pendentes e ignorados
tab_pendentes, tab_ignorados = st.tabs(["Pedidos Pendentes", "Pedidos Ignorados"])

# Sidebar para controles
with st.sidebar:
    st.header("Configurações")
    
    # Botão para buscar novos pedidos da Shopify
    if st.button("Buscar novos pedidos da Shopify"):
        with st.spinner("Buscando pedidos da Shopify..."):
            try:
                # Buscar pedidos diretos da API Shopify
                st.session_state.pedidos = buscar_pedidos_shopify()
                
                # Mensagem de sucesso formatada
                mensagem = f"""
                ### ✅ Pedidos atualizados com sucesso!
                
                **Encontrados:** {len(st.session_state.pedidos)} pedidos pagos não processados
                **Data mínima:** 01/06/2025
                **Ordenação:** Mais antigos primeiro
                """
                st.success(mensagem)
            except Exception as e:
                st.error(f"Erro ao buscar pedidos: {str(e)}")
                if 'pedidos' not in st.session_state:
                    st.session_state.pedidos = []
    
    st.divider()
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Iniciando sessão para manter o estado dos pedidos entre refreshes
if 'pedidos' not in st.session_state:
    st.session_state.pedidos = []

# Buscar pedidos diretamente da API Shopify se não estivermos processando um pedido
if 'processando_pedido_id' not in st.session_state and 'pedidos' not in st.session_state:
    with st.spinner("Buscando pedidos da Shopify..."):
        st.session_state.pedidos = buscar_pedidos_shopify()

# Carregar pedidos ignorados
pedidos_ignorados = carregar_pedidos_ignorados()

# Função para lidar com o clique no botão processar
def abrir_formulario_processamento(pedido_id):
    st.session_state.processando_pedido_id = pedido_id
    # Armazenar o índice do pedido para referenciar depois
    for i, p in enumerate(st.session_state.pedidos):
        if str(p['id']) == str(pedido_id):
            st.session_state.processando_pedido_idx = i
            break

# Função para lidar com o clique no botão ignorar
def ignorar_pedido_callback(pedido_id):
    # Ignorar o pedido e atualizar a lista de pedidos pendentes
    st.session_state.pedidos = ignorar_pedido(pedido_id, st.session_state.pedidos)
    st.rerun()

# Exibir informação sobre quantos pedidos foram encontrados
with tab_pendentes:
    if len(st.session_state.pedidos) > 0:
        st.info(f"Encontrados {len(st.session_state.pedidos)} pedidos pagos e não processados da Shopify")
        
        # Verificar se estamos processando um pedido
        if 'processando_pedido_id' in st.session_state:
            # Obter o pedido que está sendo processado
            pedido_atual = st.session_state.pedidos[st.session_state.processando_pedido_idx]
            
            st.subheader(f"Processando Pedido {pedido_atual['order_number']}")
            st.write(f"**Cliente:** {pedido_atual['nome']}")
            st.write(f"**Produto:** {pedido_atual['produto']}")
            
            # Formulário de processamento
            with st.form("form_processamento"):
                codigo_rastreamento = st.text_input("Código de Rastreamento", key="codigo_rastreamento")
                transportadora = st.radio("Transportadora", [
                    "Anjun Express - https://anjunexpress.com.br/rastreio", 
                    "Transportadora - https://martin4shop.com.br/pages/rastrear-pedido"
                ])
                
                cols = st.columns(2)
                with cols[0]:
                    if st.form_submit_button("Confirmar Processamento"):
                        if codigo_rastreamento:
                            # Processar o pedido
                            st.session_state.pedidos = processar_pedido(
                                st.session_state.processando_pedido_id, 
                                codigo_rastreamento, 
                                transportadora, 
                                st.session_state.pedidos
                            )
                            # Limpar o estado de processamento
                            del st.session_state.processando_pedido_id
                            del st.session_state.processando_pedido_idx
                            st.success("Pedido processado com sucesso!")
                            st.rerun()
                        else:
                            st.error("Por favor, informe o código de rastreamento.")
                
                with cols[1]:
                    if st.form_submit_button("Cancelar"):
                        # Limpar o estado de processamento
                        del st.session_state.processando_pedido_id
                        del st.session_state.processando_pedido_idx
                        st.rerun()
        else:
            # Exibir cada pedido pendente em um card, ordenados pelo mais antigo primeiro
            for i, pedido in enumerate(st.session_state.pedidos):
                # Criar um container para o pedido
                with st.container():
                    st.divider()
                    col1, col2 = st.columns([3, 1])
                    
                    # Informações do pedido na coluna 1
                    with col1:
                        # Adicionar contador de tempo desde a criação do pedido
                        tempo_decorrido = ""
                        if 'data_criacao' in pedido:
                            tempo_decorrido = calcular_tempo_decorrido(pedido['data_criacao'])
                            st.subheader(f"Pedido {pedido['order_number']} - Aguardando há {tempo_decorrido}")
                        else:
                            st.subheader(f"Pedido {pedido['order_number']}")
                            
                        st.write(f"**Cliente:** {pedido['nome']}")
                        st.write(f"**Telefone:** {pedido['telefone']}")
                    
                    # Botões para ações na coluna 2
                    with col2:
                        st.button("Processar", key=f"proc_{pedido['id']}", 
                                on_click=abrir_formulario_processamento, 
                                args=(pedido['id'],))
                        st.button("Ignorar", key=f"ign_{pedido['id']}", 
                                on_click=ignorar_pedido_callback, 
                                args=(pedido['id'],))
    else:
        st.warning("Nenhum pedido pendente encontrado")

# Exibir pedidos ignorados na segunda aba
with tab_ignorados:
    if len(pedidos_ignorados) > 0:
        st.info(f"Total de {len(pedidos_ignorados)} pedidos ignorados")
        
        # Exibir cada pedido ignorado
        for i, pedido in enumerate(pedidos_ignorados):
            with st.container():
                st.divider()
                st.subheader(f"Pedido ignorado {pedido['order_number']}")
                st.write(f"**Cliente:** {pedido['nome']}")
                
                # Mostrar quando foi ignorado
                if 'data_ignorado' in pedido:
                    try:
                        data_ignorado = datetime.fromisoformat(pedido['data_ignorado'])
                        st.write(f"**Ignorado em:** {data_ignorado.strftime('%d/%m/%Y %H:%M')}")
                    except ValueError:
                        st.write("**Data de ignorância não disponível**")
    else:
        st.info("Nenhum pedido foi ignorado ainda")

# Exibir mensagem se não houver pedidos
if not st.session_state.pedidos:
    st.info("Nenhum pedido encontrado. Use a barra lateral para buscar pedidos da Shopify.")

# Rodapé
st.markdown("""<div style='text-align:center'>
            <p>Martin Autofulfill - MVP v0.1</p>
            </div>""", unsafe_allow_html=True)
