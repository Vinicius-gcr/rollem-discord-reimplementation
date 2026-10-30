# Rollem - Discord Bot

Este projeto é uma reimplementação independente do bot Rollem, originalmente desenvolvido para Discord.

A partir da análise do funcionamento da versão original, desenvolvi uma versão própria em Python, utilizando engenharia reversa como base para reproduzir o sistema de rolagem de dados e implementar funcionalidades adicionais.

## Funcionalidades

- Rolagem de diferentes tipos de dados (D4, D6, D8, D10, D12, D20, entre outros).
- Rolagem de múltiplos dados simultaneamente.
- Suporte a modificadores positivos e negativos.
- Possibilidade de realizar várias rolagens em uma única mensagem.
- Configuração de resultados específicos para determinadas rolagens.
- Direcionamento de resultados para usuários, cargos ou outros membros do servidor.
- Comando de barra para consultar o funcionamento do bot.

## Tecnologias utilizadas

- Python
- discord.py
- Discord API
- Regex

## Como executar

Instale a dependência:

```bash
pip install discord.py
```

Configure o token do bot na variável de ambiente `DISCORD_TOKEN` e execute:

```bash
python main.py
```

## Sobre

Projeto independente desenvolvido para estudo e prática de Python, engenharia reversa, lógica de programação e integração com a API do Discord.

Esta implementação não é oficial e não possui vínculo com os desenvolvedores do Rollem original.
