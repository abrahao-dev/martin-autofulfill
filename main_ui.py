import io
import json
import os
import subprocess
import warnings
from datetime import datetime

# Suprimir aviso específico do urllib3 sobre LibreSSL
warnings.filterwarnings("ignore", category=Warning, message=".*OpenSSL 1\.1\.1\+.*")


import streamlit as st

import logger
import shopee_produtos
# Importar módulos do projeto
import utils
from processamento_pedidos import (gerenciar_persistencia_pedidos,
                                   ignorar_pedido_completo,
                                   mover_para_pendentes,
                                   processar_pedido_completo)
from utils import formatar_endereco_shopee


# Função para buscar novos pedidos da Shopify - Definida no início para poder ser usada em qualquer parte do código
def atualizar_pedidos():
    """Busca novos pedidos da Shopify, filtra os já processados/ignorados e atualiza a interface"""
    # Proteção contra múltiplas execuções usando session_state
    if "atualizando_pedidos" in st.session_state and st.session_state.atualizando_pedidos:
        return False

    try:
        # Marcar que estamos em processo de atualização
        st.session_state.atualizando_pedidos = True

        with st.spinner("Buscando pedidos da Shopify..."):
            # Buscar pedidos da API Shopify
            novos_pedidos = buscar_pedidos_shopify()

            # Se não encontrou nenhum pedido, mostra aviso e encerra
            if not novos_pedidos:
                st.warning("Nenhum novo pedido encontrado na Shopify.")
                st.session_state.atualizando_pedidos = False
                return False

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

**Buscados:** {len(novos_pedidos)} pedidos da Shopify
**Pendentes:** {len(pedidos_pendentes_filtrados)} pedidos após filtragem
**Processados:** {len(pedidos_processados)} pedidos já processados
**Ignorados:** {len(pedidos_ignorados)} pedidos marcados como ignorados
            """

            # Mostrar mensagem de sucesso
            st.success(mensagem_sucesso)

            # Resetar flag de atualização antes de rerun
            st.session_state.atualizando_pedidos = False

            return True

    except Exception as e:
        # Capturar qualquer erro inesperado
        st.error(f"Erro ao atualizar pedidos: {type(e).__name__} - {str(e)}")
        print(f"Erro detalhado na atualização: {e}")
        st.session_state.atualizando_pedidos = False
        return False

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

# Funções auxiliares para carregamento de dados
def carregar_pedidos(arquivo):
    """Carrega dados de arquivo com tratamento de erro"""
    caminho = f"data/{arquivo}"
    try:
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    except Exception as e:
        print(f"Erro ao carregar {arquivo}: {e}")
        return []

# Função para carregar pedidos pendentes
def carregar_pedidos_pendentes():
    return carregar_pedidos('pedidos_pendentes.json')

# Função para carregar pedidos processados
def carregar_pedidos_processados():
    return carregar_pedidos('pedidos_processados.json')

# Função para carregar pedidos ignorados
def carregar_pedidos_ignorados():
    return carregar_pedidos('pedidos_ignorados.json')

# Configuração da página
st.set_page_config(page_title="Martin Autofulfill", layout="wide")

# CSS personalizado para melhorar a interface
css = '''
<style>
    /* Estilo geral e espaçamentos */
    .block-container {padding-top: 1rem;}
    section > div > div:has(div.element-container:first-child h1) {padding-top: 0.5rem !important;}
    .element-container {margin-bottom: 0.5rem;}

    /* Cartões de pedidos - adaptação para modo escuro/claro */
    .pedido-card {
        background-color: rgba(128, 128, 128, 0.1); 
        border: 1px solid rgba(128, 128, 128, 0.3); 
        border-left: 4px solid #1e88e5; 
        border-radius: 8px;
        padding: 20px;
        margin-bottom: 24px;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
        transition: all 0.2s ease-in-out;
    }
    
    /* Efeito hover nos cards */
    .pedido-card:hover {
        box-shadow: 0 3px 8px rgba(0, 0, 0, 0.15);
        border: 1px solid rgba(128, 128, 128, 0.4);
        transform: translateY(-1px);
    }
    
    /* Seções internas dos cards */
    .section-container {
        padding: 12px;
        margin-bottom: 12px;
        background-color: rgba(128, 128, 128, 0.05);
        border-radius: 6px;
        border: 1px solid rgba(128, 128, 128, 0.15);
    }
    
    /* Estilos para títulos de seção */
    .section-title {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 10px;
        color: #1e88e5;
        border-bottom: 1px solid rgba(128, 128, 128, 0.2);
        padding-bottom: 5px;
    }
    .pedido-numero {font-size: 1.05rem; font-weight: 600; margin-bottom: 0.4rem; color: #1e88e5;}
    .pedido-cliente {font-size: 1rem; font-weight: 500; margin-bottom: 0.2rem;}
    .pedido-produto {font-size: 0.95rem; margin-bottom: 0.3rem;}
    .pedido-info {font-size: 0.9rem; margin-bottom: 0.3rem; opacity: 0.9;}

    /* Botões mais compactos */
    .botao-acao {margin-bottom: 0.2rem !important;}

    /* Ícones mais discretos */
    .icone-botao {font-size: 0.9rem;}

    /* Botões com melhor espaçamento */
    .stButton > button {margin-bottom: 0.75rem;}
    .stButton > button:hover {transform: translateY(-1px); transition: transform 0.2s;}

    /* Separador mais leve */
    hr {margin: 0.7rem 0; opacity: 0.3;}

    /* Melhor alinhamento para formulários */
    div[data-testid="stForm"] {padding-bottom: 0.5rem;}
    div[data-testid="stHorizontalBlock"] {gap: 1rem;}

    /* Copyright footer que se adapta ao tema */
    .copyright-footer {
        color: inherit;
        opacity: 0.7;
    }
</style>
'''

st.markdown(css, unsafe_allow_html=True)

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

# CSS adicional para melhorar a barra lateral
st.sidebar.markdown('''
<style>
    .sidebar-header {font-size: 1.5rem; font-weight: 600; margin-bottom: 1rem; color: #1f77b4;}
    .sidebar-subheader {font-size: 1.1rem; font-weight: 500; margin-top: 1.2rem; margin-bottom: 0.5rem;}
    .sidebar-info {
        background-color: rgba(128, 128, 128, 0.1);
        padding: 0.8rem;
        border-radius: 4px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
        border-left: 3px solid rgba(70, 130, 180, 0.6);
    }
</style>
''', unsafe_allow_html=True)

# Cabeçalho personalizado
st.sidebar.markdown('<div class="sidebar-header">Martin Autofulfill</div>', unsafe_allow_html=True)

# Define uma função auxiliar para atualizar pedidos - colocada aqui para evitar problemas de escopo
def atualizar_pedidos_callback():
    try:
        # Não precisamos importar buscar_pedidos_shopify, já está definida neste arquivo

        with st.spinner("Buscando pedidos da Shopify..."):
            # Carregando pedidos existentes para preservar o status "ja_comprado"
            pedidos_existentes = carregar_pedidos_pendentes()
            status_ja_comprado = {}
            
            # Criar um mapeamento de IDs de pedidos para seus status "ja_comprado"
            for p in pedidos_existentes:
                if 'id' in p and 'ja_comprado' in p:
                    status_ja_comprado[str(p['id'])] = p['ja_comprado']

            # Implementamos a lógica de atualização
            novos_pedidos = buscar_pedidos_shopify()

            # Se não encontrou nenhum pedido, mostra aviso
            if not novos_pedidos:
                st.warning("Nenhum novo pedido encontrado na Shopify.")
                return False

            # Filtragem e processamento dos pedidos
            pedidos_processados = carregar_pedidos_processados()
            pedidos_ignorados = carregar_pedidos_ignorados()

            # Criamos conjuntos de IDs para comparação rápida
            processados_ids = set(str(p.get('id')) for p in pedidos_processados)
            ignorados_ids = set(str(p.get('id')) for p in pedidos_ignorados)

            # Filtrar apenas pedidos que não estão nas listas de processados ou ignorados
            pedidos_pendentes_filtrados = [p for p in novos_pedidos
                                        if str(p.get('id')) not in processados_ids
                                        and str(p.get('id')) not in ignorados_ids]

            # Atualizar o campo status para todos os pedidos e preservar o status ja_comprado
            for p in pedidos_pendentes_filtrados:
                p['status'] = 'pendente'
                
                # Preservar o status "ja_comprado" se existir
                if str(p['id']) in status_ja_comprado:
                    p['ja_comprado'] = status_ja_comprado[str(p['id'])]
                else:
                    # Valor padrão para novos pedidos
                    p['ja_comprado'] = False

            # Salvar os pedidos pendentes filtrados
            utils.salvar_pedidos(pedidos_pendentes_filtrados, 'data/pedidos_pendentes.json')

            # Atualizar a sessão com os novos pedidos
            st.session_state.pedidos = pedidos_pendentes_filtrados

            # Mostrar mensagem de sucesso
            st.success(f"Encontrados {len(pedidos_pendentes_filtrados)} pedidos pendentes")
            return True

    except Exception as e:
        st.error(f"Erro ao atualizar pedidos: {str(e)}")
        print(f"Erro detalhado na atualização: {e}")
        import traceback
        print(traceback.format_exc())
        return False

# Botão de buscar pedidos mais proeminente no topo da sidebar
st.sidebar.markdown('<div class="sidebar-subheader">Ações Rápidas</div>', unsafe_allow_html=True)
if st.sidebar.button("🔄 Buscar Novos Pedidos", use_container_width=True, type="primary"):
    # Chamamos a nova função de callback
    if atualizar_pedidos_callback():
        st.toast("Pedidos atualizados!", icon="✅")
        st.rerun()

# Menu de navegação com título melhorado
st.sidebar.markdown('<div class="sidebar-subheader">Navegação</div>', unsafe_allow_html=True)
menu = st.sidebar.radio(
    "Menu",  # Adicionando um label não-vazio para evitar o aviso
    ["Gerenciar Pedidos", "Produtos Shopify-Shopee", "Logs"],
    index=0,
    label_visibility="collapsed"
)

# Inicializar o logger
logger.inicializar_csv_log()

# Mostrar últimas atividades no rodapé da sidebar
st.sidebar.markdown('<div class="sidebar-subheader">Últimas Atividades</div>', unsafe_allow_html=True)

# Pegar os últimos registros de log para mostrar no sidebar
try:
    # Verificar se o arquivo de logs existe
    log_path = os.path.join("logs", "operacoes.csv")
    ultimos_logs = []

    if os.path.exists(log_path):
        # Ler o arquivo CSV
        import pandas as pd
        try:
            df = pd.read_csv(log_path)
            # Ordenar por data_hora decrescente
            df = df.sort_values(by='data_hora', ascending=False)
            # Pegar apenas os 3 últimos registros
            ultimos_logs = df.head(3).to_dict('records')
        except Exception as e:
            # Em caso de erro, apenas prosseguimos sem logs
            pass

    if ultimos_logs:
        log_preview = "<div class='sidebar-info'>"
        for log in ultimos_logs:
            # Formatar o preview de forma compacta
            operacao = log.get('operacao', '')
            resultado = log.get('resultado', '')
            pedido = log.get('pedido_numero', '')
            data = log.get('data_hora', '').split()[-1] if log.get('data_hora') else ''

            icon = "✅" if resultado == "sucesso" else "❌" if resultado == "erro" else "ℹ️"
            log_preview += f"{icon} <strong>{operacao}</strong> {pedido} <small>({data})</small><br>"
        log_preview += "</div>"
        st.sidebar.markdown(log_preview, unsafe_allow_html=True)

    # Botão para ver todos os logs
    if st.sidebar.button("📓 Ver todos os logs", use_container_width=True):
        st.session_state['menu'] = "Logs"
        st.rerun()
except Exception as e:
    # Se houver erro ao ler logs, apenas não mostra o preview
    st.sidebar.markdown("<div class='sidebar-info'>ℹ️ Sem registros de atividade recentes</div>", unsafe_allow_html=True)

# Adicionar um espaçador para empurrar o rodapé para o final da sidebar
st.sidebar.markdown("<div style='margin-top:50px'></div>", unsafe_allow_html=True)

# Adicionando uma linha divisória antes do rodapé
st.sidebar.markdown("<hr style='margin-top:10px; margin-bottom:10px; opacity:0.3;'>", unsafe_allow_html=True)

# Rodapé da sidebar com ícone de copyright no final (não flutuante)
st.sidebar.markdown("""
<div class="copyright-footer" style='width:100%; text-align:center; font-size:0.8rem; margin-bottom:20px;'>
    &copy; Martin4shop
</div>
""", unsafe_allow_html=True)

# Estrutura principal baseada no menu selecionado
if menu == "Gerenciar Pedidos":
    # Já estamos na página principal de gerenciamento - continua com o código abaixo
    pass
elif menu == "Produtos Shopify-Shopee":
    import produtos_ui
    produtos_ui.app()
    st.stop()  # Para a execução do código atual
elif menu == "Logs":
    # Página de visualização de logs com interface melhorada
    st.header("📓 Logs de Operações")

    # Verificar se o arquivo de logs existe
    caminho_log = os.path.join('logs', 'operacoes.log')
    if os.path.exists(caminho_log):
        # Adicionar opções para filtrar logs
        col1, col2 = st.columns([3, 1])
        with col1:
            filtro = st.text_input("🔍 Filtrar logs", placeholder="Digite para filtrar...")
        with col2:
            mostrar_linhas = st.number_input("Máx. linhas", min_value=50, max_value=1000, value=200, step=50)

        # Ler o conteúdo do arquivo de log
        with open(caminho_log, 'r', encoding='utf-8') as f:
            conteudo = f.readlines()

        # Filtrar logs se necessário
        if filtro:
            conteudo = [linha for linha in conteudo if filtro.lower() in linha.lower()]

        # Ordenar as linhas mais recentes primeiro
        conteudo.reverse()

        # Limitar o número de linhas mostradas
        conteudo = conteudo[:mostrar_linhas]

        # Exibir conteúdo em um container com scroll e estilo melhorado
        st.markdown('<div style="background-color:#f8f9fa; padding:10px; border-radius:5px;">', unsafe_allow_html=True)
        with st.container():
            st.code(''.join(conteudo), language='text')
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum registro de log encontrado.")
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

# Adicionando um divisor para separar claramente as seções
st.divider()

# Botão para buscar pedidos da Shopify
col1, col2 = st.columns([3, 1])

# Botão para atualizar/recarregar a interface (já temos o botão de buscar na sidebar)
with col1:
    if st.button("🔄 Atualizar Interface", use_container_width=True, key="btn_atualizar_interface", help="Recarrega a interface sem buscar novos pedidos"):
        # Usar session_state para controlar e evitar loops infinitos
        if "ultima_atualizacao" not in st.session_state:
            st.session_state.ultima_atualizacao = 0
        
        # Incrementar contador de atualização
        st.session_state.ultima_atualizacao += 1
        st.toast("Interface atualizada", icon="✅")
        st.rerun()

# Criar abas para navegar entre diferentes tipos de pedidos
tab_pendentes, tab_processados, tab_ignorados = st.tabs(["Pedidos Pendentes", "Pedidos Processados", "Pedidos Ignorados"])

# Sidebar para controles
with st.sidebar:
    st.header("Configurações")

    # Botão para buscar novos pedidos da Shopify
    if st.button("Buscar novos pedidos da Shopify", use_container_width=True):
        # Usar a nova função de callback que implementamos
        sucesso = atualizar_pedidos_callback()
        if sucesso:
            st.rerun()

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
def processar_pedido(pedido_id, codigo_rastreamento, transportadora, pedidos_atuais, criar_fulfillment=True, palavra_chave_enviada=False, palavra_chave=""):
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

    # Chamar função central de processamento
    sucesso, mensagem = processamento_pedidos.processar_pedido_completo(
        pedido,
        codigo_rastreamento=codigo_rastreamento,
        transportadora=transportadora,
        notificar_cliente=criar_fulfillment,
        palavra_chave_enviada=palavra_chave_enviada,
        palavra_chave=palavra_chave
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
        st.info(f"Encontrados {len(st.session_state.pedidos)} pedidos não processados da Shopify")

        # Verificar se estamos processando um pedido
        if 'processando_pedido_id' in st.session_state:
            # Obter o pedido que está sendo processado
            pedido_atual = st.session_state.pedidos[st.session_state.processando_pedido_idx]

            st.subheader(f"Processando Pedido {pedido_atual['order_number']}")
            st.write(f"**Cliente:** {pedido_atual['nome']}")
            st.write(f"**Produto:** {pedido_atual['produto']}")

            # Formulário de processamento com melhor layout
            with st.form("form_processamento"):
                # Input para código de rastreamento
                codigo_rastreamento = st.text_input("Código de Rastreamento", key="codigo_rastreamento")

                # Criando um divisor para separar seções
                st.markdown("---")

                # Opções de transportadora com layout melhorado
                st.write("**Selecione a transportadora para rastreio:**")
                transportadora = st.radio("Transportadora", [
                    "Anjun Express - https://anjunexpress.com.br/rastreio",
                    "Martin4Shop - https://martin4shop.com.br/pages/rastrear-pedido"
                ], horizontal=True, label_visibility="collapsed")

                # Adicionando espaço após a seleção de transportadora
                st.write("")

                # Opção para enviar notificação para o cliente via Shopify
                criar_fulfillment = st.checkbox("Atualizar pedido na Shopify e notificar cliente", value=True,
                                           help="Cria um fulfillment na Shopify com o código de rastreio e envia notificação ao cliente")

                # Adicionando espaço antes dos botões
                st.write("")

                # Botões com melhor alinhamento usando colunas dentro do form
                form_col1, form_col2 = st.columns(2)
                with form_col1:
                    if st.form_submit_button("Confirmar", use_container_width=True):
                        if codigo_rastreamento:
                            # Exibir spinner durante o processamento
                            with st.spinner("Processando pedido e atualizando Shopify..."):
                                # Buscar o pedido atual para obter os dados da palavra-chave
                                pedido_para_processar = None
                                for p in st.session_state.pedidos:
                                    if str(p['id']) == str(st.session_state.processando_pedido_id):
                                        pedido_para_processar = p
                                        break
                                        
                                # Valores padrão caso não encontre o pedido
                                palavra_chave_enviada_valor = False
                                palavra_chave_valor = ""
                                
                                if pedido_para_processar:
                                    palavra_chave_enviada_valor = pedido_para_processar.get('palavra_chave_enviada', False)
                                    palavra_chave_valor = pedido_para_processar.get('palavra_chave', "")
                                        
                                # Processar o pedido
                                sucesso, mensagem = processar_pedido(
                                    st.session_state.processando_pedido_id,
                                    codigo_rastreamento,
                                    transportadora,
                                    st.session_state.pedidos,
                                    criar_fulfillment=criar_fulfillment,
                                    palavra_chave_enviada=palavra_chave_enviada_valor,
                                    palavra_chave=palavra_chave_valor
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

                with form_col2:
                    if st.form_submit_button("Cancelar", use_container_width=True):
                        # Limpar o estado de processamento
                        del st.session_state.processando_pedido_id
                        del st.session_state.processando_pedido_idx
                        st.rerun()
        else:
            # Exibir cada pedido pendente em um card, ordenados pelo mais antigo primeiro
            for i, pedido in enumerate(st.session_state.pedidos):
                # Criar um container para o pedido com estilo melhorado
                st.markdown(f'<div class="pedido-card">', unsafe_allow_html=True)

                # Cabeçalho do pedido com layout melhorado: título e botões lado a lado
                col_title, col_buttons = st.columns([3, 1])

                # MELHORIA 1: Título e timing na coluna esquerda com melhor hierarquia visual
                with col_title:
                    tempo_decorrido = ""
                    if 'data_criacao' in pedido:
                        tempo_decorrido = calcular_tempo_decorrido(pedido['data_criacao'])
                        st.markdown(f"<div class='pedido-numero'>Pedido {pedido['order_number']} • {tempo_decorrido}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='pedido-numero'>Pedido {pedido['order_number']}</div>", unsafe_allow_html=True)

                # MELHORIA 2: Botões na coluna direita do cabeçalho com ícones mais discretos
                with col_buttons:
                    # Coloque os botões na mesma linha com ícones menores para economizar espaço
                    col_proc, col_ign = st.columns(2)

                    with col_proc:
                        st.button("✓ Processar", key=f"proc_{pedido['id']}",
                                on_click=abrir_formulario_processamento,
                                args=(pedido['id'],),
                                use_container_width=True)

                    with col_ign:
                        st.button("× Ignorar", key=f"ign_{pedido['id']}",
                                on_click=ignorar_pedido_callback,
                                args=(pedido['id'],),
                                use_container_width=True)

                # Adicionar espaço e separador para melhor organização visual
                st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
                
                # Dividir o card em duas colunas principais
                col_info, col_keyword = st.columns([1, 1])
                
                # COLUNA ESQUERDA - Informações do pedido e cliente
                with col_info:
                    # Container para status de compra
                    st.markdown("<div class='section-container'>", unsafe_allow_html=True)
                    st.markdown("<div class='section-title'>Status do Pedido</div>", unsafe_allow_html=True)
                    comprado = st.radio(
                        "Status da compra",  # Adicionei um label adequado
                        ["Já comprado", "Não comprado"],
                        label_visibility="collapsed",  # Esconda o label mas mantenha-o para acessibilidade
                        index=0 if pedido.get("ja_comprado", False) else 1,
                        key=f"ja_comprado_{pedido['id']}",
                        horizontal=True,
                    )
                    # Atualizar o campo no pedido e salvar a alteração
                    novo_status = (comprado == "Já comprado")
                    if pedido.get("ja_comprado", False) != novo_status:
                        pedido["ja_comprado"] = novo_status
                        utils.salvar_pedidos(st.session_state.pedidos, 'data/pedidos_pendentes.json')
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Container para informações do cliente
                    st.markdown("<div class='section-container'>", unsafe_allow_html=True)
                    st.markdown("<div class='section-title'>Dados do Cliente</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-weight:bold;'>{pedido['nome']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:0.9em;'>CPF: {pedido.get('cpf', 'Não informado')}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size:0.9em;'>☎ {pedido['telefone']}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    # Container para produtos
                    st.markdown("<div class='section-container'>", unsafe_allow_html=True)
                    st.markdown("<div class='section-title'>Produtos</div>", unsafe_allow_html=True)
                    if 'line_items' in pedido and pedido['line_items']:
                        for item in pedido['line_items']:
                            nome_item = item['name']
                            variant_info = f" - {item['variant_title']}" if 'variant_title' in item and item['variant_title'] else ""
                            quantidade = item['quantity'] if 'quantity' in item else 1
                            st.markdown(f"<div class='pedido-produto'>📦 {nome_item}{variant_info} × {quantidade}</div>", unsafe_allow_html=True)
                    else:
                        # Fallback para compatibilidade com pedidos antigos
                        st.markdown(f"<div class='pedido-produto'>📦 {pedido['produto']}</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # COLUNA DIREITA - Palavra-chave e gerenciamento
                with col_keyword:
                    # Container para palavra-chave
                    st.markdown("<div class='section-container'>", unsafe_allow_html=True)
                    st.markdown("<div class='section-title'>Informações de Palavra-chave</div>", unsafe_allow_html=True)
                    
                    # Radio para selecionar se palavra-chave foi enviada
                    palavra_chave_enviada = st.radio(
                        "Palavra-chave enviada ao cliente?",
                        ["Não", "Sim"],
                        index=0 if not pedido.get("palavra_chave_enviada", False) else 1,
                        key=f"palavra_chave_{pedido['id']}",
                        horizontal=True
                    )
                    
                    # Campo de texto para inserir a palavra-chave (condicional)
                    palavra_chave = ""
                    palavra_chave_alterada = False
                    
                    if palavra_chave_enviada == "Sim":
                        # Armazena o valor anterior da palavra-chave
                        palavra_chave_anterior = pedido.get("palavra_chave", "")
                        
                        # Campo para digitar a palavra-chave
                        palavra_chave = st.text_input(
                            "Qual a palavra-chave?", 
                            value=palavra_chave_anterior,
                            placeholder="Digite a palavra-chave enviada",
                            key=f"palavra_chave_texto_{pedido['id']}"
                        )
                        
                        # Verifica se houve alteração
                        palavra_chave_alterada = (palavra_chave_anterior != palavra_chave)
                        
                        # Status da palavra-chave alterada
                        if palavra_chave_alterada:
                            st.info("Palavra-chave alterada. Clique em Salvar para confirmar.", icon="⚠️")
                        
                        # Botão para salvar alterações
                        novo_status_palavra = (palavra_chave_enviada == "Sim")
                        status_alterado = pedido.get("palavra_chave_enviada", False) != novo_status_palavra
                        
                        # Mostrar botão apenas se houver alterações
                        if palavra_chave_alterada or status_alterado:
                            if st.button("💾 Salvar Palavra-chave", key=f"save_keyword_{pedido['id']}", type="primary"):
                                # Salvar alterações
                                pedido["palavra_chave_enviada"] = novo_status_palavra
                                pedido["palavra_chave"] = palavra_chave
                                utils.salvar_pedidos(st.session_state.pedidos, 'data/pedidos_pendentes.json')
                                st.success("Palavra-chave salva com sucesso!", icon="✅")
                                st.experimental_rerun()  # Recarrega a página para atualizar o estado
                    else:
                        # Se mudar de Sim para Não
                        novo_status_palavra = False
                        if pedido.get("palavra_chave_enviada", False) != novo_status_palavra:
                            if st.button("💾 Salvar Alteração", key=f"save_status_{pedido['id']}", type="primary"):
                                pedido["palavra_chave_enviada"] = novo_status_palavra
                                utils.salvar_pedidos(st.session_state.pedidos, 'data/pedidos_pendentes.json')
                                st.success("Status atualizado!", icon="✅")
                                st.experimental_rerun()  # Recarrega a página para atualizar o estado
                    
                    st.markdown("</div>", unsafe_allow_html=True)

                # Buscar URL da Shopee correspondente ao produto
                if 'url_shopee' not in pedido or not pedido['url_shopee']:
                    url_shopee = shopee_produtos.encontrar_url_shopee_por_nome(pedido['produto'])
                    if url_shopee:
                        # Atualizar a URL no pedido
                        pedido['url_shopee'] = url_shopee

                # MELHORIA 4: Exibir URL da Shopee em layout compacto com separador
                if 'url_shopee' in pedido and pedido['url_shopee']:
                    # Adicionando um separador antes da URL
                    st.markdown("---")

                    # Usando colunas para melhor alinhamento
                    col_link, col_copy = st.columns([3, 1])

                    with col_link:
                        st.markdown(f"<div class='pedido-info'>🔗 <a href='{pedido['url_shopee']}' target='_blank'>Abrir produto na Shopee</a></div>", unsafe_allow_html=True)

                    with col_copy:
                        if st.button("📋 Copiar", key=f"copy_url_{pedido['id']}", use_container_width=True):
                            st.code(pedido['url_shopee'])
                            st.toast("URL copiada!", icon="✅")

                    # Adicionando espaçamento após o botão
                    st.write("")

                # MELHORIA 5: Endereço e botões de cópia mais compactos
                if 'endereco' in pedido and isinstance(pedido['endereco'], dict):
                    endereco_completo = f"{pedido['endereco'].get('rua', '')} {pedido['endereco'].get('numero', '')}, "
                    endereco_completo += f"{pedido['endereco'].get('complemento', '').strip()}, " if pedido['endereco'].get('complemento') else ""
                    endereco_completo += f"{pedido['endereco'].get('cidade', '')}-{pedido['endereco'].get('estado', '')}, "
                    endereco_completo += f"CEP: {pedido['endereco'].get('cep', '')}"

                    # Adicionando um separador antes da seção de endereço
                    st.markdown("---")

                    st.markdown(f"<div class='pedido-info'>🏠 {endereco_completo}</div>", unsafe_allow_html=True)

                    # Usar a função formatadora específica para Shopee
                    dados_shopee = formatar_endereco_shopee(pedido)
                    
                    # Escapar caracteres especiais para JavaScript
                    dados_shopee_js = dados_shopee.replace('`', '\\`').replace('\n', '\\n').replace('"', '\\"')
                    
                    # Botão HTML direto com JavaScript inline
                    import streamlit.components.v1 as components
                    
                    # ID único para esse botão
                    button_id = f"copy_btn_{pedido['id']}"
                    result_id = f"copy_result_{pedido['id']}"
                    
                    # HTML com botão estilizado e script para copiar
                    html = f"""
                    <button id="{button_id}" onclick="copyToClipboard()" 
                        style="width: 100%; padding: 10px; background-color: #4CAF50; color: white; 
                        border: none; border-radius: 4px; cursor: pointer; margin: 5px 0;">
                        📋 Copiar para Shopee
                    </button>
                    <div id="{result_id}" style="text-align: center; color: green; height: 20px; margin-bottom: 5px;"></div>
                    
                    <script>
                    function copyToClipboard() {{
                        const text = "{dados_shopee_js}";
                        
                        // Usando uma abordagem de fallback para máxima compatibilidade
                        const textArea = document.createElement("textarea");
                        textArea.value = text;
                        textArea.style.position = "fixed";  // Evita rolar para o elemento
                        document.body.appendChild(textArea);
                        textArea.focus();
                        textArea.select();
                        
                        try {{
                            const successful = document.execCommand('copy');
                            if (successful) {{
                                document.getElementById("{button_id}").innerHTML = "✅ Copiado!";
                                document.getElementById("{result_id}").innerHTML = "Endereço copiado com sucesso!";
                            }} else {{
                                document.getElementById("{result_id}").innerHTML = "Erro ao copiar. Tente novamente.";
                                document.getElementById("{result_id}").style.color = "red";
                            }}
                        }} catch (err) {{
                            document.getElementById("{result_id}").innerHTML = "Erro ao copiar. Tente novamente.";
                            document.getElementById("{result_id}").style.color = "red";
                        }}
                        
                        document.body.removeChild(textArea);
                        
                        // Restaurar texto do botão após 2 segundos
                        setTimeout(function() {{
                            document.getElementById("{button_id}").innerHTML = "📋 Copiar para Shopee";
                            document.getElementById("{result_id}").innerHTML = "";
                        }}, 2000);
                    }}
                    </script>
                    """
                    
                    # Renderizar o HTML
                    components.html(html, height=80)
                    
                    # Exibir os dados formatados abaixo do botão 
                    with st.expander("Ver dados formatados", expanded=False):
                        st.code(dados_shopee, language=None)

                    # Adicionando espaçamento inferior conforme solicitado
                    st.write("")

                # Fechamento do card
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Nenhum pedido pendente encontrado")

# Exibir pedidos processados na aba processados
with tab_processados:
    if pedidos_processados and len(pedidos_processados) > 0:
        st.info(f"Total de {len(pedidos_processados)} pedidos processados")

        # Exibir cada pedido processado com o novo estilo
        for i, pedido in enumerate(pedidos_processados):
            # Usar o mesmo estilo de cartão dos pendentes
            st.markdown(f'<div class="pedido-card">', unsafe_allow_html=True)

            # Título do pedido com data de processamento se disponível
            if 'data_processamento' in pedido:
                data_proc = datetime.fromisoformat(pedido['data_processamento'])
                data_formatada = data_proc.strftime('%d/%m/%Y %H:%M')
                st.markdown(f"<div class='pedido-numero'>Pedido {pedido['order_number']} • Processado {data_formatada}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='pedido-numero'>Pedido {pedido['order_number']} • Processado</div>", unsafe_allow_html=True)

            # Informações do cliente e produto com estilo melhorado
            st.markdown(f"<div class='pedido-cliente'>{pedido['nome']}</div>", unsafe_allow_html=True)
            
            # Exibir todos os itens do pedido processado
            if 'line_items' in pedido and pedido['line_items']:
                for item in pedido['line_items']:
                    nome_item = item['name']
                    variant_info = f" - {item['variant_title']}" if 'variant_title' in item and item['variant_title'] else ""
                    quantidade = item['quantity'] if 'quantity' in item else 1
                    st.markdown(f"<div class='pedido-produto'>📦 {nome_item}{variant_info} × {quantidade}</div>", unsafe_allow_html=True)
            else:
                # Fallback para compatibilidade com pedidos antigos
                st.markdown(f"<div class='pedido-produto'>📦 {pedido['produto']}</div>", unsafe_allow_html=True)

            # Layout horizontal para mostrar rastreio e transportadora
            if 'codigo_rastreamento' in pedido or 'transportadora' in pedido:
                col_track, col_carrier = st.columns(2)

                with col_track:
                    if 'codigo_rastreamento' in pedido:
                        st.markdown(f"<div class='pedido-info'>📬 <strong>Rastreio:</strong> {pedido['codigo_rastreamento']}</div>", unsafe_allow_html=True)

                with col_carrier:
                    if 'transportadora' in pedido:
                        # Simplificar nome da transportadora
                        transp_nome = pedido['transportadora'].split(' - ')[0] if ' - ' in pedido['transportadora'] else pedido['transportadora']
                        st.markdown(f"<div class='pedido-info'>🚚 <strong>Transportadora:</strong> {transp_nome}</div>", unsafe_allow_html=True)

            # Endereço em formato compacto
            if 'endereco' in pedido and isinstance(pedido['endereco'], dict):
                endereco_completo = f"{pedido['endereco'].get('rua', '')} {pedido['endereco'].get('numero', '')}, "
                endereco_completo += f"{pedido['endereco'].get('complemento', '').strip()}, " if pedido['endereco'].get('complemento') else ""
                endereco_completo += f"{pedido['endereco'].get('cidade', '')}-{pedido['endereco'].get('estado', '')}, "
                endereco_completo += f"CEP: {pedido['endereco'].get('cep', '')}"

                st.markdown(f"<div class='pedido-info'>🏠 {endereco_completo}</div>", unsafe_allow_html=True)

            # Status de fulfillment com estilo visual melhorado
            if 'fulfillment_status' in pedido:
                status = pedido['fulfillment_status']
                if status == 'concluido':
                    st.markdown('<div style="background-color:rgba(0, 128, 0, 0.2); padding:8px; border-radius:4px; margin-top:8px;">✅ Fulfillment criado com sucesso na Shopify</div>', unsafe_allow_html=True)
                elif status == 'erro':
                    col_erro, col_btn = st.columns([3, 1])

                    with col_erro:
                        st.markdown('<div style="background-color:rgba(255, 0, 0, 0.15); padding:8px; border-radius:4px; margin-top:8px;">❌ Erro ao criar fulfillment na Shopify</div>', unsafe_allow_html=True)

                    # Botão para mover o pedido com erro para pendentes - mais discreto
                    with col_btn:
                        if st.button(f"↩ Pendentes", key=f"mover_{pedido['id']}", use_container_width=True):
                            sucesso = mover_para_pendentes(pedido['id'])
                            if sucesso:
                                st.toast("Pedido movido para pendentes", icon="✅")
                                st.rerun()
                            else:
                                st.warning("Não foi possível mover o pedido.")

            # Fechamento do cartão
            st.markdown('</div>', unsafe_allow_html=True)

# Exibir pedidos ignorados na terceira aba
with tab_ignorados:
    if pedidos_ignorados and len(pedidos_ignorados) > 0:
        st.info(f"Total de {len(pedidos_ignorados)} pedidos ignorados")

        # Exibir cada pedido ignorado com o novo estilo visual
        for i, pedido in enumerate(pedidos_ignorados):
            # Usar o mesmo estilo de cartão dos outros pedidos
            st.markdown(f'<div class="pedido-card">', unsafe_allow_html=True)

            # Título com data de ignorado se disponível
            if 'data_ignorado' in pedido:
                data_ign = datetime.fromisoformat(pedido['data_ignorado'])
                data_formatada = data_ign.strftime('%d/%m/%Y %H:%M')
                st.markdown(f"<div class='pedido-numero'>Pedido {pedido['order_number']} • Ignorado {data_formatada}</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='pedido-numero'>Pedido {pedido['order_number']} • Ignorado</div>", unsafe_allow_html=True)

            # Informações do cliente e produto com estilo melhorado
            st.markdown(f"<div class='pedido-cliente'>{pedido['nome']}</div>", unsafe_allow_html=True)
            
            # Exibir todos os itens do pedido ignorado
            if 'line_items' in pedido and pedido['line_items']:
                for item in pedido['line_items']:
                    nome_item = item['name']
                    variant_info = f" - {item['variant_title']}" if 'variant_title' in item and item['variant_title'] else ""
                    quantidade = item['quantity'] if 'quantity' in item else 1
                    st.markdown(f"<div class='pedido-produto'>📦 {nome_item}{variant_info} × {quantidade}</div>", unsafe_allow_html=True)
            else:
                # Fallback para compatibilidade com pedidos antigos
                st.markdown(f"<div class='pedido-produto'>📦 {pedido['produto']}</div>", unsafe_allow_html=True)

            # Endereço em formato compacto
            if 'endereco' in pedido and isinstance(pedido['endereco'], dict):
                endereco_completo = f"{pedido['endereco'].get('rua', '')} {pedido['endereco'].get('numero', '')}, "
                endereco_completo += f"{pedido['endereco'].get('complemento', '').strip()}, " if pedido['endereco'].get('complemento') else ""
                endereco_completo += f"{pedido['endereco'].get('cidade', '')}-{pedido['endereco'].get('estado', '')}, "
                endereco_completo += f"CEP: {pedido['endereco'].get('cep', '')}"

                st.markdown(f"<div class='pedido-info'>🏠 {endereco_completo}</div>", unsafe_allow_html=True)

                # Separador antes dos botões de ação
                st.markdown("---")

                # Botão para mover de volta para pendentes - usando colunas mais proporcionais
                col1, col2 = st.columns([3, 1])
                with col2:
                    if st.button("↩ Desfazer", key=f"desfazer_ignorado_{pedido['id']}", use_container_width=True):
                        # Função para mover de volta para pendentes - poderia ser implementada
                        st.toast("Função não implementada ainda", icon="ℹ️")

            # Fechamento do cartão
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Nenhum pedido foi ignorado ainda")

# Exibir mensagem se não houver pedidos
if not st.session_state.pedidos:
    st.info("Nenhum pedido encontrado. Use a barra lateral para buscar pedidos da Shopify.")

# Rodapé simplificado sem versão
st.markdown("""<div style='text-align:center; opacity:0.7;'>
            <p>Martin Autofulfill</p>
            </div>""", unsafe_allow_html=True)
