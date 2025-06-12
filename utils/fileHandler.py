# utils/fileHandler.py - Versão completa final com formatação

import pandas as pd
import re
from csv import Sniffer

class FileHandler:
    """Classe utilitária para manipulação de arquivos CSV e Excel."""
    
    @staticmethod
    def read_file(file, file_type, config):
        if file_type == "xlsx":
            df = pd.read_excel(file)
        elif file_type == "csv":
            try:
                df = pd.read_csv(
                    file,
                    delimiter=";",
                    quotechar='"',
                    encoding="utf-8",
                    engine="python",
                    on_bad_lines="skip"
                )
            except Exception:
                file.seek(0)
                delimiter, quotechar = FileHandler.detect_csv_properties(file)
                df = pd.read_csv(
                    file,
                    delimiter=delimiter,
                    quotechar=quotechar,
                    encoding="utf-8",
                    engine="python",
                    on_bad_lines="skip"
                )
        else:
            raise ValueError("Tipo de arquivo não suportado. Apenas CSV e XLSX são aceitos.")
        
        df = FileHandler.preprocess_dataframe(df, config)
        return df

    @staticmethod
    def detect_csv_properties(file):
        """
        Detecta o delimitador de campo e o caractere de aspas em um arquivo CSV.
        """
        try:
            sample = file.read(1024).decode("utf-8", errors="replace")
            file.seek(0)
            
            sniffer = Sniffer()
            dialect = sniffer.sniff(sample)
            return dialect.delimiter, dialect.quotechar
        except Exception:
            file.seek(0)
            sample = file.read(1024).decode("utf-8", errors="replace")
            file.seek(0)
            if sample.count(',') >= sample.count(';'):
                return ",", '"'
            elif sample.count(';') > 0:
                return ";", '"'
            else:
                return ",", '"'

    @staticmethod
    def preprocess_dataframe(df, config):
        """
        Pré-processa o DataFrame - VERSÃO SIMPLIFICADA
        """
        coluna_processos = config.get('coluna_processos', 'numeroProcesso')
        
        # DEBUG: Mostrar informações do DataFrame
        print(f"DEBUG: Colunas disponíveis: {list(df.columns)}")
        print(f"DEBUG: Procurando pela coluna: '{coluna_processos}'")
        
        if coluna_processos not in df.columns:
            # Tentar encontrar coluna similar
            colunas_similares = [col for col in df.columns if 'processo' in col.lower() or 'numero' in col.lower()]
            raise KeyError(f"A coluna '{coluna_processos}' não foi encontrada. Colunas disponíveis: {list(df.columns)}. Colunas similares: {colunas_similares}")
        
        # Garantir que seja string
        df[coluna_processos] = df[coluna_processos].astype(str)
        
        # DEBUG: Mostrar alguns exemplos dos números
        print(f"DEBUG: Primeiros 5 números de processo:")
        for i, numero in enumerate(df[coluna_processos].head()):
            print(f"  {i+1}: '{numero}' (tipo: {type(numero)})")
        
        # EXTRAÇÃO SIMPLIFICADA DE DÍGITO
        df['Dígito'] = df[coluna_processos].apply(FileHandler.extrair_digito_simples)
        
        # DEBUG: Verificar resultados da extração
        digitos_extraidos = df['Dígito'].value_counts().sort_index()
        print(f"DEBUG: Dígitos extraídos (frequência):")
        print(digitos_extraidos.head(10))
        print(f"DEBUG: Total de dígitos = 0 (não extraídos): {(df['Dígito'] == 0).sum()}")
        
        return df

    @staticmethod
    def extrair_digito_simples(numero):
        """
        Extração simplificada - apenas 3 padrões necessários
        """
        if pd.isna(numero) or str(numero).lower() == 'nan':
            return 0
        
        numero_str = str(numero).strip()
        
        # Padrão 1: Com hífen e pontos (captura AMBOS os casos)
        # Funciona para: 0000046-15.2017.8.05.0216 E 0000046-15.2017.805.0216
        match1 = re.search(r'\d+-(\d{2})\.\d{4}\.', numero_str)
        if match1:
            return int(match1.group(1))
        
        # Padrão 2: 20 dígitos consecutivos
        if re.match(r'^\d{20}$', numero_str):
            return int(numero_str[7:9])  # Posições 7-8
        
        # Padrão 3: Hífen + 2 dígitos (fallback)
        match3 = re.search(r'-(\d{2})', numero_str)
        if match3:
            return int(match3.group(1))
        
        return 0

    @staticmethod
    def debug_numero_processo(numero_processo):
        """
        Debug simplificado
        """
        print(f"\nDEBUG DETALHADO para: '{numero_processo}'")
        numero_str = str(numero_processo).strip()
        
        patterns = {
            'Hífen + pontos': r'\d+-(\d{2})\.\d{4}\.',
            '20 dígitos': r'^\d{20}$',
            'Hífen + 2 dígitos': r'-(\d{2})',
        }
        
        for nome, pattern in patterns.items():
            match = re.search(pattern, numero_str)
            if match:
                print(f"  ✓ {nome}: {match.groups() if hasattr(match, 'groups') else 'Match'}")
            else:
                print(f"  ✗ {nome}: não encontrado")

# =============================================================================
# FUNÇÕES DE FORMATAÇÃO DE NÚMEROS
# =============================================================================

def formatar_numero_processo(numero, formato_destino="padrao_cnj"):
    """
    Formata um número de processo para o formato escolhido pelo usuário.
    
    Args:
        numero: Número do processo (qualquer formato)
        formato_destino: "padrao_cnj", "tribunal_805", ou "sem_formatacao"
    
    Returns:
        Número formatado conforme escolha do usuário
    """
    if pd.isna(numero) or str(numero).lower() == 'nan':
        return numero
    
    numero_str = str(numero).strip()
    
    # Extrair componentes do número
    componentes = extrair_componentes_numero(numero_str)
    if not componentes:
        return numero  # Retorna original se não conseguir extrair
    
    # Aplicar formatação escolhida
    if formato_destino == "padrao_cnj":
        # Formato: 0000046-15.2017.8.05.0216
        return f"{componentes['sequencial']:07d}-{componentes['digito']:02d}.{componentes['ano']}.{componentes['segmento']}.{componentes['tribunal']:02d}.{componentes['origem']:04d}"
    
    elif formato_destino == "tribunal_805":
        # Formato: 0000046-15.2017.805.0216
        tribunal_formatado = f"{componentes['segmento']}{componentes['tribunal']:02d}"
        return f"{componentes['sequencial']:07d}-{componentes['digito']:02d}.{componentes['ano']}.{tribunal_formatado}.{componentes['origem']:04d}"
    
    elif formato_destino == "sem_formatacao":
        # Formato: 00000461520178050216
        return f"{componentes['sequencial']:07d}{componentes['digito']:02d}{componentes['ano']}{componentes['segmento']}{componentes['tribunal']:02d}{componentes['origem']:04d}"
    
    else:
        return numero  # Formato inválido, retorna original

def extrair_componentes_numero(numero_str):
    """
    Extrai todos os componentes de um número de processo.
    
    Returns:
        Dict com: sequencial, digito, ano, segmento, tribunal, origem
        Ou None se não conseguir extrair
    """
    # Padrão 1: Com formatação CNJ padrão (0000046-15.2017.8.05.0216)
    match1 = re.match(r'(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})', numero_str)
    if match1:
        return {
            'sequencial': int(match1.group(1)),
            'digito': int(match1.group(2)),
            'ano': int(match1.group(3)),
            'segmento': int(match1.group(4)),
            'tribunal': int(match1.group(5)),
            'origem': int(match1.group(6))
        }
    
    # Padrão 2: Com formatação variação (0000046-15.2017.805.0216)
    match2 = re.match(r'(\d{7})-(\d{2})\.(\d{4})\.(\d{3})\.(\d{4})', numero_str)
    if match2:
        tribunal_str = match2.group(4)  # "805"
        segmento = int(tribunal_str[0])  # "8"
        tribunal = int(tribunal_str[1:3])  # "05"
        return {
            'sequencial': int(match2.group(1)),
            'digito': int(match2.group(2)),
            'ano': int(match2.group(3)),
            'segmento': segmento,
            'tribunal': tribunal,
            'origem': int(match2.group(5))
        }
    
    # Padrão 3: Sem formatação (00000461520178050216)
    apenas_digitos = re.sub(r'\D', '', numero_str)
    if len(apenas_digitos) == 20:
        return {
            'sequencial': int(apenas_digitos[0:7]),
            'digito': int(apenas_digitos[7:9]),
            'ano': int(apenas_digitos[9:13]),
            'segmento': int(apenas_digitos[13]),
            'tribunal': int(apenas_digitos[14:16]),
            'origem': int(apenas_digitos[16:20])
        }
    
    return None

# =============================================================================
# FUNÇÕES AUXILIARES SIMPLIFICADAS
# =============================================================================

def extrair_ano_processo_melhorado(numero):
    """
    Extração de ano simplificada
    """
    if pd.isna(numero) or numero == '' or str(numero).lower() == 'nan':
        return None
    
    numero_str = str(numero).strip()
    
    # Padrão 1: Com hífen e pontos (funciona para ambos os casos)
    match1 = re.search(r'\d+-\d{2}\.(\d{4})\.', numero_str)
    if match1:
        ano = int(match1.group(1))
        if 1990 <= ano <= 2030:
            return ano
    
    # Padrão 2: 20 dígitos consecutivos
    apenas_digitos = re.sub(r'\D', '', numero_str)
    if len(apenas_digitos) == 20:
        try:
            ano = int(apenas_digitos[9:13])  # Posições 9-12
            if 1990 <= ano <= 2030:
                return ano
        except ValueError:
            pass
    
    # Padrão 3: Fallback - qualquer ano de 4 dígitos
    anos_encontrados = re.findall(r'(20\d{2}|19\d{2})', numero_str)
    if anos_encontrados:
        ano = int(anos_encontrados[0])
        if 1990 <= ano <= 2030:
            return ano
    
    return None

def classificar_meta2_melhorado(ano_processo, ano_meta2):
    """
    Classificação Meta 2
    """
    if ano_processo is None:
        return "Ano não identificado"
    elif ano_processo < ano_meta2:
        return "Meta 2"
    else:
        return "Fora da Meta 2"

def atribuir_servidor_melhorado(digito, configuracao):
    """
    Atribuição de servidor
    """
    if pd.isna(digito) or digito == 0:
        return "Dígito não identificado"
    
    intervalos_servidores = configuracao.get("intervalos_servidores", {})
    for servidor, intervalos in intervalos_servidores.items():
        for intervalo in intervalos:
            if len(intervalo) >= 2 and intervalo[0] <= digito <= intervalo[1]:
                return servidor
    
    return f"Servidor não configurado (dígito: {digito})"

def diagnosticar_arquivo(df, config):
    """
    Diagnóstico simplificado
    """
    print("=" * 50)
    print("DIAGNÓSTICO DO ARQUIVO")
    print("=" * 50)
    
    coluna_processos = config.get('coluna_processos', 'numeroProcesso')
    print(f"Linhas: {len(df)}, Colunas: {len(df.columns)}")
    print(f"Coluna de processos: {coluna_processos}")
    
    if coluna_processos in df.columns:
        print(f"Primeiros 3 números:")
        for i, val in enumerate(df[coluna_processos].head(3)):
            print(f"  {i+1}: '{val}'")
            FileHandler.debug_numero_processo(val)
    
    if 'Dígito' in df.columns:
        print(f"Dígitos encontrados: {sorted(df['Dígito'].unique())}")
        print(f"Dígitos não extraídos: {(df['Dígito'] == 0).sum()}")
    
    return df