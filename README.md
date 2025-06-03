# Martin Autofulfill

Automatização da rotina de pedidos pagos na Shopify para compras automatizadas na Shopee, com interface simples para selecionar os pedidos a serem processados e preenchimento automático dos dados do cliente na Shopee.

## Stack utilizada

- **Interface**: Streamlit (simples, local, fácil de usar)
- **Backend**: Python + requests + Playwright
- **Automação browser**: playwright-python
- **Armazenamento**: .json ou SQLite local

## Instalação

```bash
# Clonar o repositório
git clone <repositório>
cd martin-autofulfill

# Instalar dependências
pip install -r requirements.txt

# Instalar browsers para o Playwright
python -m playwright install
```

## Executando o projeto

```bash
streamlit run main_ui.py
```

## Etapas do Projeto

1. Interface Básica com Dados Fictícios (dummy data) ✅
2. Integração com Shopify (backend real) 🔄
3. Automação de Compra na Shopee 🔄