import re

ano_meta2 = 2021  # Pode ser ajustado dinamicamente

def formatar_numero_processo(numero: str) -> str:
    """
    Formata um número de processo para o padrão CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
    """
    numero = re.sub(r'\\D', '', str(numero))
    if len(numero) == 20:
        return f"{numero[:7]}-{numero[7:9]}.{numero[9:13]}.{numero[13]}.{numero[14:16]}.{numero[16:]}"
    return numero

def extrair_ano_processo(numero: str) -> str | None:
    """
    Extrai o ano do número do processo e retorna como string formatada.
    """
    numero_formatado = formatar_numero_processo(numero)
    match = re.search(r'\\d{7}-\\d{2}\\.(\\d{4})\\.', numero_formatado)
    return match.group(1) if match else None

def extrair_digito_verificador(numero: str) -> int | None:
    """
    Extrai o dígito verificador (dois dígitos após os 7 iniciais).
    Exemplo: de '0000068-73.2017.8.05.0216' extrai '73'
    """
    numero_formatado = formatar_numero_processo(numero)
    match = re.search(r'^\\d{7}-(\\d{2})\\.', numero_formatado)
    return int(match.group(1)) if match else None

def classificar_meta2_func(ano_processo: str | None) -> str:
    """
    Classifica o processo como 'Meta 2' ou 'Fora da Meta 2' com base no ano.
    """
    if ano_processo is None:
        return "Desconhecido"
    try:
        return "Meta 2" if int(ano_processo) < ano_meta2 else "Fora da Meta 2"
    except ValueError:
        return "Desconhecido"

def atribuir_servidor(digito: int | None, configuracao: dict) -> str:
    """
    Atribui um servidor com base no dígito e configuração dos intervalos.
    """
    if digito is None:
        return "Desconhecido"

    for servidor, intervalos in configuracao.get("intervalos_servidores", {}).items():
        for intervalo in intervalos:
            if intervalo[0] <= digito <= intervalo[1]:
                return servidor
    return "Desconhecido"

def preparar_colunas_processos(df, coluna_processos: str, configuracao: dict):
    """
    Prepara colunas de número formatado, ano, digito e servidor.
    """
    df["Número Formatado"] = df[coluna_processos].apply(formatar_numero_processo)
    df["Ano Processo"] = df["Número Formatado"].apply(extrair_ano_processo)
    df["Meta 2 Classificacao"] = df["Ano Processo"].apply(classificar_meta2_func)
    df["Dígito"] = df["Número Formatado"].apply(extrair_digito_verificador)
    df["Servidor"] = df["Dígito"].apply(lambda x: atribuir_servidor(x, configuracao))
    return df
