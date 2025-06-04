# Martin Autofulfill

Automatização da rotina de pedidos na Shopify para compras automatizadas na Shopee, com interface simples para selecionar os pedidos a serem processados e preenchimento automático dos dados do cliente na Shopee.

## Funcionalidades

### Implementadas ✅

- **Integração com Shopify**: Busca pedidos não processados da API Shopify
- **Interface de gerenciamento**: Abas para pedidos pendentes, processados e ignorados 
- **Formatação de endereço Shopee**: Botão compatível com macOS para copiar dados formatados
- **Sistema de logs**: Registro de operações em CSV e arquivo de log
- **Mapeamento de produtos**: Associação entre produtos Shopify e URLs da Shopee
- **Processo de fulfilment**: Atualização de pedidos com códigos de rastreio
- **Status de compra**: Seletor "Já comprado/Não comprado" com persistência de dados
- **Exibição de CPF**: Extração e display de CPF de clientes da Shopify/Yampi
- **Modo escuro**: Interface completamente compatível com tema claro e escuro

### Em desenvolvimento 🔄

- **Automação de compra na Shopee**: Integração com Playwright para preencher automaticamente formulários

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
6. Extração e exibição de CPF dos clientes ✅
7. Status de compra (Já comprado/Não comprado) ✅
8. Compatibilidade com tema claro/escuro ✅
9. Automação de Compra na Shopee 🔄

## Próximos Passos

### Automação na Shopee

O principal desafio restante é a automação completa das compras na plataforma Shopee. Para isso, será implementado:

1. **Integração com Playwright**: Para automatizar o preenchimento de dados do cliente na Shopee
   - Abertura automática da URL do produto
   - Preenchimento dos campos de endereço do destinatário
   - Seleção de variações do produto (tamanho, cor, etc.)
   - Avanço até a etapa de pagamento

2. **Fluxo de Automação**:
   - Botão na interface para iniciar a automação
   - Seleção do navegador e configuração do Playwright
   - Sistema de retry e tratamento de erros
   - Opção para modo headless ou com interface gráfica

3. **Contorno de Desafios**:
   - Identificação e bypass de captchas
   - Tratamento de login na Shopee
   - Adaptação a mudanças na interface da Shopee

### Melhorias Futuras

- **Dashboards analíticos**: Visualização de métricas de pedidos e processamento
- **Automação de pagamentos**: Integração com métodos de pagamento na Shopee
- **Multi-conta Shopee**: Suporte para várias contas de comprador
- **Integração com outros marketplaces**: Expandir para além da Shopee