import streamlit as st
import subprocess
import json
import os
import io
from datetime import datetime

# Importar módulos do projeto
import utils
from utils import formatar_endereco_shopee
from processamento_pedidos import ignorar_pedido_completo, processar_pedido_completo, gerenciar_persistencia_pedidos
import shopee_produtos
import logger

# Garantir que os diretórios necessários existam
def garantir_diretorios():
    diretorios = ['data', 'logs']
    for diretorio in diretorios:
        caminho = os.path.join(os.path.dirname(os.path.abspath(__file__)), diretorio)
        if not os.path.exists(caminho):
            os.makedirs(caminho)
            print(f"Diretório criado: {caminho}")

# Criar diretórios necessários
garantir_diretorios()

# Funções para carregar diferentes tipos de pedidos
def carregar_pedidos_pendentes():
    return utils.carregar_pedidos("data/pedidos_pendentes.json")

def carregar_pedidos_processados():
    return utils.carregar_pedidos("data/pedidos_processados.json")

def carregar_pedidos_ignorados():
    return utils.carregar_pedidos("data/pedidos_ignorados.json")

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
    """Busca pedidos da Shopify de forma robusta, com tratamento de erros
    
    Returns:
        list: Lista de pedidos da Shopify ou lista vazia em caso de erro
    """
    try:
        # Executar o script get_shopify_orders.py com a flag --apenas-retornar
        result = subprocess.run(['python3', 'get_shopify_orders.py', '--apenas-retornar'], 
                             capture_output=True, text=True, check=True, 
                             cwd=os.path.dirname(os.path.abspath(__file__)))
        
        # Converter a saída JSON para uma lista de pedidos Python
        pedidos = json.loads(result.stdout.strip())
        
        # Verificar se os dados são válidos
        if not isinstance(pedidos, list):
            st.error(f"Formato de resposta inválido: esperava uma lista, recebeu {type(pedidos)}")
            return []
            
        # Ordenar pedidos pelo mais antigo primeiro
        pedidos.sort(key=lambda x: x.get('data_criacao', ''), reverse=False)
        
        # Log de sucesso (não visível para o usuário)
        print(f"Shopify: {len(pedidos)} pedidos encontrados")
        return pedidos
        
    except subprocess.CalledProcessError as e:
        st.error(f"Erro ao executar script: {e.stderr}")
        print(f"Erro ao buscar pedidos (script): {e}")
        return []
        
    except json.JSONDecodeError as e:
        st.error(f"Erro ao decodificar JSON: {e}")
        print(f"Dados recebidos: {result.stdout[:100]}...")
        return []
        
    except Exception as e:
        st.error(f"Erro inesperado: {type(e).__name__} - {str(e)}")
        print(f"Erro detalhado: {e}")
        return []

# Funções de persistência usando o módulo utils

# Função para carregar dados de um arquivo JSON
def carregar_pedidos(arquivo):
    # Usar o módulo utils para garantir validação e padronização
    # Garantir que o caminho comece com o diretório data/
    if not arquivo.startswith('data/'):
        arquivo_path = f"data/{arquivo}"
    else:
        arquivo_path = arquivo
    return utils.carregar_pedidos(arquivo_path)
        
# Função para carregar pedidos ignorados
def carregar_pedidos_ignorados():
    return carregar_pedidos('pedidos_ignorados.json')
    
# Função para carregar pedidos processados
def carregar_pedidos_processados():
    return carregar_pedidos('pedidos_processados.json')
    
# Função para carregar pedidos pendentes
def carregar_pedidos_pendentes():
    return carregar_pedidos('pedidos_pendentes.json')

# Função para processar um pedido
def processar_pedido(idx, pedido_id, codigo_rastreamento, transportadora):
    """ Processa um pedido e marca como concluído """
    if idx < len(st.session_state.pedidos):
        pedido = st.session_state.pedidos[idx]
        
        # Chamar função central de processamento no módulo processamento_pedidos
        sucesso, mensagem = processamento_pedidos.processar_pedido_completo(
            pedido,
            codigo_rastreamento=codigo_rastreamento,
            transportadora=transportadora
        )
        
        if sucesso:
            # Atualizar pedidos na sessão após o processamento bem-sucedido
            st.session_state.pedidos = utils.carregar_pedidos("data/pedidos_pendentes.json")
            st.success(mensagem)
            # Recarregar a página para atualizar contadores
            st.rerun()
        else:
            st.error(mensagem)
            
        return sucesso, mensagem
    
    return False, "Pedido não encontrado"

# Função para ignorar um pedido
def ignorar_pedido(idx, pedido_id):
    """Marca um pedido como ignorado"""
    if idx < len(st.session_state.pedidos):
        pedido = st.session_state.pedidos[idx]
        
        # Chamar função central de ignorar pedido no módulo processamento_pedidos
        sucesso, mensagem = processamento_pedidos.ignorar_pedido_completo(pedido)
        
        if sucesso:
            # Atualizar pedidos na sessão após ignorar pedido
            st.session_state.pedidos = utils.carregar_pedidos("data/pedidos_pendentes.json")
            st.success(mensagem)
            # Recarregar a página para atualizar contadores
            st.rerun()
        else:
            st.error(mensagem)
            
        return sucesso, mensagem
    
    return False, "Pedido não encontrado"

# Título do aplicativo
st.title("Martin Autofulfill - Gerenciador de Pedidos")

# Menu de navegação
menu = st.sidebar.radio(
    "Menu",
    ["Gerenciar Pedidos", "Produtos Shopify-Shopee", "Logs"],
    index=0
)

# Inicializar o logger
logger.inicializar_csv_log()

# Roteamento das páginas
if menu == "Produtos Shopify-Shopee":
    import produtos_ui
    produtos_ui.app()
    st.stop()  # Para a execução do código atual
elif menu == "Logs":
    # Página de visualização de logs
    st.header("Logs de Operações")
    
    # Verificar se o arquivo de logs existe
    log_path = os.path.join("logs", "operacoes.csv")
    if os.path.exists(log_path):
        # Ler o arquivo CSV
        try:
            import pandas as pd
            df = pd.read_csv(log_path)
            # Ordenar por data_hora decrescente
            df = df.sort_values(by='data_hora', ascending=False)
            # Exibir a tabela
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Erro ao ler logs: {str(e)}")
    else:
        st.info("Nenhum log de operação encontrado.")
    
    st.stop()  # Para a execução do código atual

# Contadores de pedidos
pendentes = len(st.session_state.pedidos) if 'pedidos' in st.session_state else 0
processados = len(pedidos_processados) if 'pedidos_processados' in locals() else 0
ignorados = len(pedidos_ignorados) if 'pedidos_ignorados' in locals() else 0
total = pendentes + processados + ignorados

# Exibir contadores em métricas no topo da interface
col_metricas1, col_metricas2, col_metricas3, col_metricas4 = st.columns(4)
with col_metricas1:
    st.metric("Pedidos Pendentes", pendentes, help="Pedidos aguardando processamento")
with col_metricas2:
    st.metric("Pedidos Processados", processados, help="Pedidos já processados e concluídos")
with col_metricas3:
    st.metric("Pedidos Ignorados", ignorados, help="Pedidos marcados como ignorados")
with col_metricas4:
    st.metric("Total de Pedidos", total, help="Total de pedidos no sistema")

# Subtítulo da aplicação
st.subheader("Processamento automático de pedidos Shopify para Shopee")

# Botão para buscar pedidos da Shopify
col1, col2 = st.columns([3, 1])

# Função para buscar novos pedidos da Shopify
def atualizar_pedidos():
    """Busca novos pedidos da Shopify, filtra os já processados/ignorados e atualiza a interface"""
    with st.spinner("Buscando pedidos da Shopify..."):
        try:
            # Buscar pedidos da API Shopify
            novos_pedidos = buscar_pedidos_shopify()
            
            # Se não encontrou nenhum pedido, mostra aviso e encerra
            if not novos_pedidos:
                st.warning("Nenhum novo pedido encontrado na Shopify.")
                return
            
            # Filtrar pedidos que já foram processados ou ignorados
            pedidos_processados = carregar_pedidos_processados()
            pedidos_ignorados = carregar_pedidos_ignorados()
            
            # Criar conjuntos de IDs para comparação rápida
            processados_ids = set(str(p.get('id')) for p in pedidos_processados)
            ignorados_ids = set(str(p.get('id')) for p in pedidos_ignorados)
            
            # Filtrar apenas pedidos que não estão nas listas de processados ou ignorados
            pedidos_pendentes_filtrados = [p for p in novos_pedidos 
                                        if str(p.get('id')) not in processados_ids 
                                        and str(p.get('id')) not in ignorados_ids]
            
            # Atualizar o campo status para todos os pedidos
            for p in pedidos_pendentes_filtrados:
                p['status'] = 'pendente'
                
            # Salvar os pedidos pendentes filtrados
            utils.salvar_pedidos(pedidos_pendentes_filtrados, 'data/pedidos_pendentes.json')
            
            # Atualizar a sessão com os novos pedidos filtrados
            st.session_state.pedidos = pedidos_pendentes_filtrados
            
            # Formatar mensagem de sucesso
            mensagem_sucesso = f"""### ✅ Pedidos atualizados com sucesso!

**Buscados:** {len(novos_pedidos)} pedidos pagos da Shopify
**Pendentes:** {len(pedidos_pendentes_filtrados)} pedidos após filtragem
**Processados:** {len(pedidos_processados)} pedidos já processados
**Ignorados:** {len(pedidos_ignorados)} pedidos marcados como ignorados
            """
            
            # Mostrar mensagem de sucesso
            st.success(mensagem_sucesso)
            
            # Recarregar a página para atualizar os contadores
            st.rerun()
            
        except Exception as e:
            # Capturar qualquer erro inesperado
            st.error(f"Erro ao atualizar pedidos: {type(e).__name__} - {str(e)}")
            print(f"Erro detalhado na atualização: {e}")
            return False

# Botão para buscar novos pedidos
with col1:
    if st.button("🔄 Atualizar Pedidos da Shopify", use_container_width=True):
        atualizar_pedidos()

# Criar abas para navegar entre diferentes tipos de pedidos
tab_pendentes, tab_processados, tab_ignorados = st.tabs(["Pedidos Pendentes", "Pedidos Processados", "Pedidos Ignorados"])

# Sidebar para controles
with st.sidebar:
    st.header("Configurações")
    
    # Botão para buscar novos pedidos da Shopify
    if st.button("Buscar novos pedidos da Shopify"):
        # Reutilizar a função já implementada para reduzir código duplicado
        atualizar_pedidos()
    
    st.divider()
    st.caption(f"Última atualização: {datetime.now().strftime('%d/%m/%Y %H:%M')}")

# Iniciando sessão para manter o estado dos pedidos entre refreshes
if 'pedidos' not in st.session_state:
    # Carregar pedidos pendentes do arquivo de persistência
    pedidos_pendentes = carregar_pedidos_pendentes()
    if pedidos_pendentes:
        st.session_state.pedidos = pedidos_pendentes
    else:
        st.session_state.pedidos = []

# Carregar pedidos ignorados e processados para as abas
pedidos_ignorados = carregar_pedidos_ignorados()
pedidos_processados = carregar_pedidos_processados()

# Função para processar um pedido
def processar_pedido(pedido_id, codigo_rastreamento, transportadora, pedidos_atuais, criar_fulfillment=True):
    """Processa um pedido, adicionando código de rastreamento e transportadora"""
    # Encontrar o pedido na lista
    pedido = None
    for p in pedidos_atuais:
        if str(p['id']) == str(pedido_id):
            pedido = p
            break
    
    if not pedido:
        return False, "Pedido não encontrado"
    
    # Limpar o nome da transportadora (remover a URL)
    nome_transportadora = transportadora.split(' - ')[0] if ' - ' in transportadora else transportadora
    
    # Processar o pedido usando a função completa
    sucesso, mensagem = processar_pedido_completo(
        pedido, 
        codigo_rastreamento=codigo_rastreamento,
        transportadora=nome_transportadora,
        notificar_cliente=criar_fulfillment
    )
    
    # Registrar a operação no log
    if sucesso:
        logger.registrar_operacao(
            pedido_id=pedido_id,
            pedido_numero=pedido.get('order_number', ''),
            cliente=pedido.get('nome', ''),
            operacao="processar",
            resultado="sucesso",
            detalhes=f"Código: {codigo_rastreamento}, Transportadora: {nome_transportadora}"
        )
    else:
        logger.registrar_operacao(
            pedido_id=pedido_id,
            pedido_numero=pedido.get('order_number', ''),
            cliente=pedido.get('nome', ''),
            operacao="processar",
            resultado="erro",
            detalhes=mensagem
        )
    
    # Remover o pedido da lista de pendentes se o processamento foi bem sucedido
    pedidos_restantes = pedidos_atuais
    if sucesso:
        pedidos_restantes = [p for p in pedidos_atuais if str(p['id']) != str(pedido_id)]
    
    return sucesso, mensagem

# Função para lidar com o clique no botão processar
def abrir_formulario_processamento(pedido_id):
    st.session_state.processando_pedido_id = pedido_id
    # Armazenar o índice do pedido para referenciar depois
    for i, p in enumerate(st.session_state.pedidos):
        if str(p['id']) == str(pedido_id):
            st.session_state.processando_pedido_idx = i
            break

# Função para ignorar um pedido
def ignorar_pedido(pedido_id, pedidos_atuais):
    """Marca um pedido como ignorado e move para a lista de ignorados"""
    # Encontrar o pedido na lista
    pedido = None
    for p in pedidos_atuais:
        if str(p['id']) == str(pedido_id):
            pedido = p
            break
    
    if not pedido:
        return pedidos_atuais
    
    # Processar o pedido usando a função completa
    sucesso, mensagem = ignorar_pedido_completo(pedido)
    
    # Registrar a operação no log
    if sucesso:
        logger.registrar_operacao(
            pedido_id=pedido_id,
            pedido_numero=pedido.get('order_number', ''),
            cliente=pedido.get('nome', ''),
            operacao="ignorar",
            resultado="sucesso",
            detalhes=mensagem
        )
        st.toast("Pedido ignorado com sucesso", icon="✅")
    else:
        logger.registrar_operacao(
            pedido_id=pedido_id,
            pedido_numero=pedido.get('order_number', ''),
            cliente=pedido.get('nome', ''),
            operacao="ignorar",
            resultado="erro",
            detalhes=mensagem
        )
        st.toast(f"Erro ao ignorar pedido: {mensagem}", icon="❌")
    
    # Remover o pedido da lista de pendentes
    return [p for p in pedidos_atuais if str(p['id']) != str(pedido_id)]

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
                
                # Opções de transportadora com layout melhorado
                st.write("**Selecione a transportadora para rastreio:**")
                transportadora = st.radio("Transportadora", [
                    "Anjun Express - https://anjunexpress.com.br/rastreio", 
                    "Martin4Shop - https://martin4shop.com.br/pages/rastrear-pedido"
                ], horizontal=True, label_visibility="collapsed")
                
                # Opção para enviar notificação para o cliente via Shopify
                criar_fulfillment = st.checkbox("Atualizar pedido na Shopify e notificar cliente", value=True,
                                           help="Cria um fulfillment na Shopify com o código de rastreio e envia notificação ao cliente")
                
                cols = st.columns(2)
                with cols[0]:
                    if st.form_submit_button("Confirmar Processamento", use_container_width=True):
                        if codigo_rastreamento:
                            # Exibir spinner durante o processamento
                            with st.spinner("Processando pedido e atualizando Shopify..."):
                                # Processar o pedido
                                sucesso, mensagem = processar_pedido(
                                    st.session_state.processando_pedido_id, 
                                    codigo_rastreamento, 
                                    transportadora, 
                                    st.session_state.pedidos,
                                    criar_fulfillment=criar_fulfillment
                                )
                                
                                if sucesso:
                                    # Atualizar a lista de pedidos - remover o pedido processado
                                    st.session_state.pedidos = [p for p in st.session_state.pedidos 
                                                            if str(p['id']) != str(st.session_state.processando_pedido_id)]
                                    
                                    # Limpar o estado de processamento
                                    del st.session_state.processando_pedido_id
                                    del st.session_state.processando_pedido_idx
                                    
                                    # Nome formatado da transportadora
                                    nome_transp = transportadora.split(' - ')[0] if ' - ' in transportadora else transportadora
                                    
                                    # Mostrar mensagem de sucesso adequada
                                    if criar_fulfillment:
                                        st.success(f"""### ✅ Pedido processado com sucesso!
                                        
                                        **Código de rastreio:** {codigo_rastreamento}
                                        **Transportadora:** {nome_transp}
                                        **Shopify:** Pedido atualizado e cliente notificado""")
                                    else:
                                        st.success(f"""### ✅ Pedido processado com sucesso!
                                        
                                        **Código de rastreio:** {codigo_rastreamento}
                                        **Transportadora:** {nome_transp}""")
                                    
                                    # Recarregar a interface
                                    st.rerun()
                                else:
                                    # Mostrar mensagem de erro
                                    st.error(f"**Erro ao processar pedido:** {mensagem}")
                                    
                                    if criar_fulfillment:
                                        st.warning("Não foi possível atualizar o pedido na Shopify. Verifique as credenciais da API.")
                                
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
                        st.write(f"**Produto:** {pedido['produto']}")
                        
                        # Buscar URL da Shopee correspondente ao produto
                        if 'url_shopee' not in pedido or not pedido['url_shopee']:
                            url_shopee = shopee_produtos.encontrar_url_shopee_por_nome(pedido['produto'])
                            if url_shopee:
                                # Atualizar a URL no pedido
                                pedido['url_shopee'] = url_shopee
                        
                        # Exibir URL da Shopee se disponível
                        if 'url_shopee' in pedido and pedido['url_shopee']:
                            st.write(f"**Link Shopee:** [Abrir produto na Shopee]({pedido['url_shopee']})")
                            # Botão para copiar URL
                            if st.button("📋 Copiar URL Shopee", key=f"copy_url_{pedido['id']}"):
                                st.code(pedido['url_shopee'])
                                st.toast("URL copiada!", icon="✅")

                        # Adicionar botão para copiar endereço completo
                        if 'endereco' in pedido and isinstance(pedido['endereco'], dict):
                            endereco_completo = f"{pedido['endereco'].get('rua', '')} {pedido['endereco'].get('numero', '')}, "
                            endereco_completo += f"{pedido['endereco'].get('complemento', '').strip()}, " if pedido['endereco'].get('complemento') else ""
                            endereco_completo += f"{pedido['endereco'].get('cidade', '')}-{pedido['endereco'].get('estado', '')}, "
                            endereco_completo += f"CEP: {pedido['endereco'].get('cep', '')}"
                            
                            st.write(f"**Endereço:** {endereco_completo}")
                            
                            # Botões para copiar endereço em diferentes formatos
                            col_btn1, col_btn2 = st.columns(2)
                            
                            # Botão para copiar no formato normal
                            with col_btn1:
                                if st.button("📋 Copiar Endereço", key=f"copy_{pedido['id']}"):
                                    st.toast("Endereço copiado!", icon="✅")
                                    st.write(f"```{endereco_completo}```")
                            
                            # Botão para copiar no formato específico da Shopee
                            with col_btn2:
                                if st.button("📋 Copiar Dados para Shopee", key=f"copy_shopee_{pedido['id']}"):
                                    # Usar a função formatadora específica para Shopee
                                    dados_shopee = formatar_endereco_shopee(pedido)
                                    st.toast("Dados para Shopee copiados!", icon="✅")
                                    st.code(dados_shopee)
                    
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

# Exibir pedidos processados na aba processados
with tab_processados:
    if pedidos_processados and len(pedidos_processados) > 0:
        st.info(f"Total de {len(pedidos_processados)} pedidos processados")
        
        # Exibir cada pedido processado
        for i, pedido in enumerate(pedidos_processados):
            with st.container():
                st.divider()
                
                # Título com data de processamento se disponível
                if 'data_processado' in pedido:
                    data_proc = datetime.fromisoformat(pedido['data_processado'])
                    data_formatada = data_proc.strftime('%d/%m/%Y %H:%M')
                    st.subheader(f"Pedido {pedido['order_number']} - Processado em {data_formatada}")
                else:
                    st.subheader(f"Pedido {pedido['order_number']} - Processado")
                
                # Informações do pedido
                col1, col2 = st.columns([2,1])
                
                with col1:
                    st.write(f"**Cliente:** {pedido['nome']}")
                    st.write(f"**Produto:** {pedido['produto']}")
                    
                    # Se tiver código de rastreio, mostrar
                    if 'codigo_rastreamento' in pedido:
                        st.write(f"**Rastreio:** {pedido['codigo_rastreamento']}")
                    
                    # Se tiver transportadora, mostrar
                    if 'transportadora' in pedido:
                        st.write(f"**Transportadora:** {pedido['transportadora']}")
                    
                    # Status de fulfillment se disponível
                    if 'fulfillment_status' in pedido:
                        status = pedido['fulfillment_status']
                        if status == 'concluido':
                            st.success("✅ Fulfillment criado com sucesso na Shopify")
                        elif status == 'erro':
                            st.error("❌ Erro ao criar fulfillment na Shopify")

# Exibir pedidos ignorados na terceira aba
with tab_ignorados:
    if pedidos_ignorados and len(pedidos_ignorados) > 0:
        st.info(f"Total de {len(pedidos_ignorados)} pedidos ignorados")
        
        # Exibir cada pedido ignorado
        for i, pedido in enumerate(pedidos_ignorados):
            with st.container():
                st.divider()
                
                # Título com data de ignorado se disponível
                if 'data_ignorado' in pedido:
                    data_ign = datetime.fromisoformat(pedido['data_ignorado'])
                    data_formatada = data_ign.strftime('%d/%m/%Y %H:%M')
                    st.subheader(f"Pedido {pedido['order_number']} - Ignorado em {data_formatada}")
                else:
                    st.subheader(f"Pedido {pedido['order_number']} - Ignorado")
                
                # Informações do pedido
                st.write(f"**Cliente:** {pedido['nome']}")
                st.write(f"**Produto:** {pedido['produto']}")
                
                if 'endereco' in pedido and isinstance(pedido['endereco'], dict):
                    endereco_completo = f"{pedido['endereco'].get('rua', '')} {pedido['endereco'].get('numero', '')}, "
                    endereco_completo += f"{pedido['endereco'].get('complemento', '').strip()}, " if pedido['endereco'].get('complemento') else ""
                    endereco_completo += f"{pedido['endereco'].get('cidade', '')}-{pedido['endereco'].get('estado', '')}, "
                    endereco_completo += f"CEP: {pedido['endereco'].get('cep', '')}"
                    
                    st.write(f"**Endereço:** {endereco_completo}")
                
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
