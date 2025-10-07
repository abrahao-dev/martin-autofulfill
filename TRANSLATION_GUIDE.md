# Translation Guide for Martin Autofulfill

This document outlines the translation changes made to convert the codebase from Portuguese to English for the Shopify Full-Stack Developer job application.

## File Renaming

| Old Name (Portuguese) | New Name (English) | Status |
|----------------------|-------------------|--------|
| `processamento_pedidos.py` | `order_processing.py` | ✅ Done |
| `produtos_ui.py` | `products_ui.py` | ✅ Done |
| `shopee_produtos.py` | `shopee_products.py` | ✅ Done |
| `logs/operacoes.csv` | `logs/operations.csv` | ✅ Done |

## Function Name Translations

### logger.py
- `inicializar_csv_log()` → `initialize_csv_log()`
- `registrar_operacao()` → `log_operation()`
- `registrar_erro()` → `log_error()`

### utils.py
- `validar_pedido()` → `validate_order()`
- `padronizar_pedido()` → `standardize_order()`
- `salvar_pedidos()` → `save_orders()`
- `carregar_pedidos()` → `load_orders()`
- `formatar_endereco_shopee()` → `format_shopee_address()`

### order_processing.py (formerly processamento_pedidos.py)
- `processar_pedido_completo()` → `process_complete_order()`
- `ignorar_pedido_completo()` → `ignore_complete_order()`
- `mover_para_pendentes()` → `move_to_pending()`
- `gerenciar_persistencia_pedidos()` → `manage_order_persistence()`

### shopee_products.py (formerly shopee_produtos.py)
- `carregar_produtos()` → `load_products()`
- `salvar_produtos()` → `save_products()`
- `adicionar_produto()` → `add_product()`
- `remover_produto()` → `remove_product()`
- `encontrar_url_shopee_por_nome()` → `find_shopee_url_by_name()`

### shopify_fulfillment.py
- `criar_fulfillment()` → `create_fulfillment()`
- `formatar_shopify_url()` → `format_shopify_url()`

### get_shopify_orders.py
- `buscar_pedidos_shopify()` → `fetch_shopify_orders()`
- `processar_pedido()` → `process_order()`

### get_shopify_locations.py
- `get_shopify_locations()` → (already in English)
- `get_default_location_id()` → (already in English)

## Variable Name Translations

### Common Variables
- `pedido` → `order`
- `pedidos` → `orders`
- `cliente` → `customer`
- `produto` → `product`
- `produtos` → `products`
- `endereco` → `address`
- `codigo_rastreamento` → `tracking_code`
- `transportadora` → `carrier`
- `data_criacao` → `created_date`
- `data_processado` → `processed_date`
- `data_ignorado` → `ignored_date`
- `ja_comprado` → `already_purchased`
- `palavra_chave` → `keyword`
- `palavra_chave_enviada` → `keyword_sent`

### Field Names in Data Structures
- `pedido_id` → `order_id`
- `pedido_numero` → `order_number`
- `nome` → `name`
- `telefone` → `phone`
- `rua` → `street`
- `numero` → `number`
- `cidade` → `city`
- `estado` → `state`
- `cep` → `zip_code`
- `complemento` → `complement`
- `url_shopee` → `shopee_url`
- `palavras_chave` → `keywords`
- `detalhes` → `details`
- `resultado` → `result`
- `operacao` → `operation`
- `sucesso` → `success`
- `mensagem` → `message`

## String Translations in UI

### Main UI (main_ui.py)
- "Gerenciar Pedidos" → "Manage Orders"
- "Produtos Shopify-Shopee" → "Shopify-Shopee Products"
- "Logs" → "Logs"
- "Pedidos Pendentes" → "Pending Orders"
- "Pedidos Processados" → "Processed Orders"
- "Pedidos Ignorados" → "Ignored Orders"
- "Buscar novos pedidos da Shopify" → "Fetch new Shopify orders"
- "Atualizar Interface" → "Refresh Interface"
- "Código de Rastreamento" → "Tracking Code"
- "Transportadora" → "Carrier"
- "Confirmar" → "Confirm"
- "Cancelar" → "Cancel"
- "Processar" → "Process"
- "Ignorar" → "Ignore"
- "Já comprado" → "Already purchased"
- "Não comprado" → "Not purchased"
- "Copiar para Shopee" → "Copy for Shopee"
- "Ver dados formatados" → "View formatted data"
- "Dados do Cliente" → "Customer Data"
- "Produtos" → "Products"
- "Status do Pedido" → "Order Status"

### Products UI (products_ui.py)
- "Gerenciamento de Produtos Shopify-Shopee" → "Shopify-Shopee Product Management"
- "Cadastrar Novo Produto" → "Register New Product"
- "Nome do produto na Shopify" → "Shopify product name"
- "Palavras-chave (uma por linha)" → "Keywords (one per line)"
- "URL do produto na Shopee" → "Shopee product URL"
- "Cadastrar Produto" → "Register Product"
- "Produtos Cadastrados" → "Registered Products"
- "Buscar produto" → "Search product"
- "Editar" → "Edit"
- "Excluir" → "Delete"

## Status Messages Translation
- "sucesso" → "success"
- "erro" → "error"
- "pendente" → "pending"
- "processado" → "processed"
- "ignorado" → "ignored"
- "Pedido processado com sucesso!" → "Order processed successfully!"
- "Erro ao processar pedido" → "Error processing order"
- "Pedido ignorado com sucesso" → "Order ignored successfully"
- "Nenhum pedido encontrado" → "No orders found"
- "Pedidos atualizados com sucesso!" → "Orders updated successfully!"

## Comment Translations

### Python Docstrings
All docstrings should be translated to professional English with proper technical terminology.

Example:
```python
# Portuguese
"""
Processa um pedido e marca como concluído
"""

# English
"""
Process an order and mark it as completed
"""
```

## Notes for Implementation

1. All user-facing strings must be in English
2. Internal variable names should follow Python naming conventions
3. CSV column headers must match the new English field names
4. JSON data structures should maintain backward compatibility where possible
5. Log messages should be in English
6. Error messages should be professional and clear

## Testing Checklist

- [ ] All UI labels are in English
- [ ] All function names follow English naming
- [ ] All variable names are in English
- [ ] All comments and docstrings are in English
- [ ] CSV log files use English column headers
- [ ] Error messages are clear and professional
- [ ] README is professional and detailed
- [ ] No Portuguese strings remain in user-facing elements
