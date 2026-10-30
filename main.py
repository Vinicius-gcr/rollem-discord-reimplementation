import re
import secrets
import discord
from discord import app_commands

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

rigged_rolls = {}

ROLL_REGEX = re.compile(
    r"^(?:(\d+)#)?(\d*)d(\d+)(?:\s*([+-])\s*(\d+))?(?:\s+(.+))?$", re.IGNORECASE
)

@tree.command(
    name="rollem",
    description="Mostra informações sobre o sistema de dados Rollem.",
)
async def comando_rollem(interaction: discord.Interaction):
  await interaction.response.send_message(
      "**Rollem está ativo!** Digite a rolagem diretamente no chat (ex:"
      " `1d20` ou `3d8`).",
      ephemeral=True,
  )


def gerar_dados_manipulados(
    qtd: int, lados: int, valores_forcados: list[int]
) -> list[int]:
  if len(valores_forcados) == qtd:
    return [max(1, min(lados, v)) for v in valores_forcados]

  if qtd == 1:
    return [max(1, min(lados, valores_forcados[0]))]

  alvo = max(qtd, min(qtd * lados, valores_forcados[0]))
  dados = [1] * qtd
  restante = alvo - qtd
  while restante > 0:
    idx = secrets.randbelow(qtd)
    if dados[idx] < lados:
      dados[idx] += 1
      restante -= 1
  return dados


def pode_aplicar_set(qtd: int, lados: int, config: dict) -> bool:
  lados_alvo = config["lados_alvo"]
  valores = config["valores"]

  if lados_alvo is not None and lados != lados_alvo:
    return False

  if len(valores) == qtd and qtd > 1:
    return all(1 <= v <= lados for v in valores)

  soma_desejada = valores[0]
  return (qtd * 1) <= soma_desejada <= (qtd * lados)


def formatar_dado_rollem(valor: int, lados: int) -> str:
  if valor == 1 or valor == lados:
    return f"**{valor}**"
  return str(valor)


@client.event
async def on_ready():
  await tree.sync()

  atividade = discord.Game(name="rollem.rocks|v2.11.5")
  await client.change_presence(
      status=discord.Status.online, activity=atividade
  )
  print(f"Bot online como {client.user} com status e comandos configurados!")


@client.event
async def on_message(message: discord.Message):
  if message.author.bot:
    return

  conteudo = message.content.strip()

  # ==========================================================
  # 1. COMANDO(.set)
  # Exemplos:
  #   .set 20             -> Define a SUA próxima jogada para 20
  #   .set d20 20         -> Define o SEU próximo d20 para 20
  #   .set amigo 1        -> Define a próxima jogada de OUTRA PESSOA para 1
  #   .set @Usuario 20    -> Define a próxima jogada APENAS do usuário marcado
  #   .set @Cargo 20      -> Define a próxima jogada de quem tiver o cargo marcado
  #   .set off            -> Desativa tudo
  # ==========================================================
  if conteudo.lower().startswith(".set "):
    if message.guild is not None:
      try:
        await message.delete()
      except discord.Forbidden:
        pass

    partes = conteudo.split()[1:]
    if not partes or partes[0].lower() in ("off", "clear", "reset"):
      rigged_rolls.clear()
      if message.guild is None:
        await message.channel.send("Manipulações desativadas.")
      return

    try:
      mencao_user = re.match(r"^<@!?(\d+)>$", partes[0])
      mencao_cargo = re.match(r"^<@&(\d+)>$", partes[0])

      if mencao_user:
        alvo_key = int(mencao_user.group(1))
        tipo_alvo = "user"
        alvo_desc = f"usuário marcado (<@{alvo_key}>)"
        partes = partes[1:]
      elif mencao_cargo:
        alvo_key = int(mencao_cargo.group(1))
        tipo_alvo = "role"
        alvo_desc = f"cargo marcado (<@&{alvo_key}>)"
        partes = partes[1:]
      elif partes[0].lower() in ("amigo", "amigos", "outro", "outros"):
        alvo_key = "amigo"
        tipo_alvo = "amigo"
        alvo_desc = "próximo amigo (qualquer um menos você)"
        partes = partes[1:]
      else:
        alvo_key = message.author.id
        tipo_alvo = "user"
        alvo_desc = "você mesmo"

      if not partes:
        return

      lados_alvo = None
      if partes[0].lower().startswith("d") and partes[0][1:].isdigit():
        lados_alvo = int(partes[0][1:])
        partes = partes[1:]

      valores = [int(x) for x in partes]
      if not valores:
        return

      rigged_rolls[alvo_key] = {
          "tipo": tipo_alvo,
          "lados_alvo": lados_alvo,
          "valores": valores,
          "autor_id": message.author.id,
      }

      if message.guild is None:
        dado_txt = f" (em d{lados_alvo})" if lados_alvo else ""
        await message.channel.send(
            f"Configurado `{valores}`{dado_txt} -> Alvo: **{alvo_desc}**"
        )
    except ValueError:
      pass
    return

  match = ROLL_REGEX.match(conteudo)
  if not match:
    return

  rep_str, qtd_str, lados_str, op_str, mod_str, label = match.groups()

  repeticoes = int(rep_str) if rep_str else 1
  qtd = int(qtd_str) if qtd_str else 1
  lados = int(lados_str)
  modificador = int(mod_str) if mod_str else 0
  if op_str == "-":
    modificador = -modificador

  if qtd < 1 or qtd > 100 or lados <= 1 or repeticoes < 1 or repeticoes > 20:
    return

  linhas_resposta = []

  for _ in range(repeticoes):
    config_aplicada = None
    chave_remover = None
      
    cfg_user = rigged_rolls.get(message.author.id)
    if (
        cfg_user
        and cfg_user.get("tipo") == "user"
        and pode_aplicar_set(qtd, lados, cfg_user)
    ):
      config_aplicada = cfg_user
      chave_remover = message.author.id

    if (
        not config_aplicada
        and hasattr(message.author, "roles")
        and message.guild
    ):
      for role in message.author.roles:
        cfg_role = rigged_rolls.get(role.id)
        if (
            cfg_role
            and cfg_role.get("tipo") == "role"
            and pode_aplicar_set(qtd, lados, cfg_role)
        ):
          config_aplicada = cfg_role
          chave_remover = role.id
          break

    if not config_aplicada:
      cfg_amigo = rigged_rolls.get("amigo")
      if (
          cfg_amigo
          and message.author.id != cfg_amigo["autor_id"]
          and pode_aplicar_set(qtd, lados, cfg_amigo)
      ):
        config_aplicada = cfg_amigo
        chave_remover = "amigo"

    if config_aplicada:
      rigged_rolls.pop(chave_remover, None)
      resultados = gerar_dados_manipulados(
          qtd, lados, config_aplicada["valores"]
      )
    else:
      resultados = [secrets.randbelow(lados) + 1 for _ in range(qtd)]

    resultados.sort(reverse=True)

    soma_dados = sum(resultados)
    total = soma_dados + modificador

    dados_formatados = ", ".join(
        formatar_dado_rollem(d, lados) for d in resultados
    )

    expressao = f"{qtd}d{lados}"
    if op_str and mod_str:
      expressao += f" {op_str} {mod_str}"

    prefixo_label = f"'{label}', " if label else ""
    linha = f"{prefixo_label}` {total} ` ⟵ [{dados_formatados}] {expressao}"
    linhas_resposta.append(linha)

  resposta_final = "\n".join(linhas_resposta)

  await message.reply(
      resposta_final,
      mention_author=True,
      allowed_mentions=discord.AllowedMentions(
          everyone=False,
          users=False,
          roles=False,
          replied_user=True,
      ),
  )


client.run(
    "TOKEN DISCORD AQUI"
)
