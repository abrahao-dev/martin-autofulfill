# Martin Autofulfill

Automatização da rotina de pedidos na Shopify para compras automatizadas na Shopee, com interface simples para selecionar os pedidos a serem processados e preenchimento automático dos dados do cliente na Shopee.

## Funcionalidades

- ✅ **Integração com Shopify**: Busca pedidos não processados da API Shopify
- ✅ **Interface de gerenciamento**: Abas para pedidos pendentes, processados e ignorados
- ✅ **Formatação de endereço Shopee**: Botão para copiar dados no formato exigido pela Shopee
- ✅ **Sistema de logs**: Registro de operações em CSV e arquivo de log
- ✅ **Mapeamento de produtos**: Associação entre produtos Shopify e URLs da Shopee
- ✅ **Processo de fulfilment**: Atualização de pedidos com códigos de rastreio
- 🔄 **Automação de compra na Shopee**: Em desenvolvimento

## Stack utilizada

- **Interface**: Streamlit (simples, local, fácil de usar)
- **Backend**: Python + requests + Playwright
- **API Integration**: Shopify API para pedidos e fulfillment
- **Automação browser**: playwright-python
- **Armazenamento**: Arquivos JSON locais e logs CSV

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/abrahao-dev/martin-autofulfill.git
cd martin-autofulfill

# Criar arquivo .env com as credenciais
cp .env.example .env
# Edite o arquivo .env com suas credenciais da Shopify

# Instalar dependências
pip install -r requirements.txt

# Instalar browsers para o Playwright (opcional - necessário apenas para automação)
python -m playwright install
```

## Executando o projeto

```bash
streamlit run main_ui.py
```

## Estrutura do Projeto

```
martin-autofulfill/
├── data/               # Dados de pedidos pendentes, processados e ignorados
├── logs/               # Logs de operações
├── get_shopify_orders.py # Script de integração com a API Shopify
├── main_ui.py          # Interface principal Streamlit
├── utils.py            # Funções utilitárias, incluindo formatação de endereço
├── processamento_pedidos.py # Lógica de processamento de pedidos
├── shopee_produtos.py   # Gerenciamento de produtos Shopify-Shopee
├── logger.py           # Sistema de logs para rastreabilidade
├── requirements.txt    # Dependências do projeto
└── .env               # Credenciais e configurações (não versionado)
```

## Etapas do Projeto

1. Interface Básica com Dados Fictícios ✅
2. Integração com Shopify (backend real) ✅
3. Sistema de logs e traceabilidade ✅
4. Mapeamento de produtos Shopify-Shopee ✅
5. Formatação e cópia de endereços para Shopee ✅
6. Automação de Compra na Shopee 🔄