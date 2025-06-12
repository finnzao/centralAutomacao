# utils/fileHandler.py - Versão corrigida completa

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
        Pré-processa o DataFrame com correções para o formato: 0000046-15.2017.8.05.0216
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
        
        # REGEX CORRIGIDA para extrair dígito do formato: NNNNNNN-DD.AAAA.J.TT.OOOO
        # Exemplo: 0000046-15.2017.8.05.0216 → dígito = 15
        df['Dígito'] = df[coluna_processos].str.extract(r'\d+-(\d{2})\.\d{4}\.')[0]
        df['Dígito'] = pd.to_numeric(df['Dígito'], errors='coerce').fillna(0).astype(int)
        
        # DEBUG: Verificar resultados da extração
        digitos_extraidos = df['Dígito'].value_counts().sort_index()
        print(f"DEBUG: Dígitos extraídos (frequência):")
        print(digitos_extraidos.head(10))
        print(f"DEBUG: Total de dígitos = 0 (não extraídos): {(df['Dígito'] == 0).sum()}")
        
        return df

    @staticmethod
    def debug_numero_processo(numero_processo):
        """
        Função para debugar um número específico de processo.
        """
        print(f"\nDEBUG DETALHADO para: '{numero_processo}'")
        print(f"  Tipo: {type(numero_processo)}")
        print(f"  Comprimento: {len(str(numero_processo))}")
        
        # Testar diferentes padrões
        patterns = {
            'Dígito (formato atual)': r'\d+-(\d{2})\.\d{4}\.',
            'Ano (formato atual)': r'\d+-\d{2}\.(\d{4})\.',
            'CNJ completo': r'(\d+)-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})',
        }
        
        for nome, pattern in patterns.items():
            match = re.search(pattern, str(numero_processo))
            if match:
                print(f"  ✓ {nome}: {match.groups()}")
            else:
                print(f"  ✗ {nome}: não encontrado")

# =============================================================================
# FUNÇÕES AUXILIARES PARA O DASHBOARD
# =============================================================================

def extrair_ano_processo_melhorado(numero):
    """
    Versão corrigida para extrair ano do formato: 0000046-15.2017.8.05.0216
    """
    if pd.isna(numero) or numero == '' or str(numero).lower() == 'nan':
        return None
    
    numero_str = str(numero)
    
    # REGEX CORRIGIDA: buscar ano de 4 dígitos após o dígito verificador
    # Formato: NNNNNNN-DD.AAAA.J.TT.OOOO
    match = re.search(r'\d+-\d{2}\.(\d{4})\.', numero_str)
    if match:
        ano = int(match.group(1))
        # Validar se é um ano razoável (entre 1990 e ano atual + 5)
        import datetime
        ano_atual = datetime.datetime.now().year
        if 1990 <= ano <= ano_atual + 5:
            return ano
    
    return None

def classificar_meta2_melhorado(ano_processo, ano_meta2):
    """
    Versão melhorada da classificação Meta 2.
    """
    if ano_processo is None:
        return "Ano não identificado"
    elif ano_processo < ano_meta2:
        return "Meta 2"
    else:
        return "Fora da Meta 2"

def atribuir_servidor_melhorado(digito, configuracao):
    """
    Versão melhorada com debug para atribuição de servidor.
    """
    if pd.isna(digito) or digito == 0:
        return "Dígito não identificado"
    
    intervalos_servidores = configuracao.get("intervalos_servidores", {})
    for servidor, intervalos in intervalos_servidores.items():
        for intervalo in intervalos:
            if len(intervalo) >= 2 and intervalo[0] <= digito <= intervalo[1]:
                return servidor
    
    return f"Servidor não configurado (dígito: {digito})"

# =============================================================================
# FUNÇÃO DE DIAGNÓSTICO COMPLETO
# =============================================================================

def diagnosticar_arquivo(df, config):
    """
    Função para diagnosticar problemas no processamento do arquivo.
    """
    print("=" * 50)
    print("DIAGNÓSTICO COMPLETO DO ARQUIVO")
    print("=" * 50)
    
    # 1. Informações básicas
    print(f"1. INFORMAÇÕES BÁSICAS:")
    print(f"   - Linhas: {len(df)}")
    print(f"   - Colunas: {len(df.columns)}")
    print(f"   - Colunas: {list(df.columns)}")
    
    # 2. Verificar coluna de processos
    coluna_processos = config.get('coluna_processos', 'numeroProcesso')
    print(f"\n2. COLUNA DE PROCESSOS:")
    print(f"   - Procurando: '{coluna_processos}'")
    print(f"   - Existe: {coluna_processos in df.columns}")
    
    if coluna_processos in df.columns:
        print(f"   - Valores não nulos: {df[coluna_processos].notna().sum()}")
        print(f"   - Primeiros 3 valores:")
        for i, val in enumerate(df[coluna_processos].head(3)):
            print(f"     {i+1}: '{val}'")
            FileHandler.debug_numero_processo(val)
    
    # 3. Verificar extração de dígitos
    if 'Dígito' in df.columns:
        print(f"\n3. EXTRAÇÃO DE DÍGITOS:")
        print(f"   - Dígitos únicos: {sorted(df['Dígito'].unique())}")
        print(f"   - Dígitos = 0: {(df['Dígito'] == 0).sum()}")
        print(f"   - Distribuição:")
        print(df['Dígito'].value_counts().sort_index())
    
    # 4. Verificar extração de anos
    if 'Ano Processo' in df.columns:
        print(f"\n4. EXTRAÇÃO DE ANOS:")
        anos_unicos = df['Ano Processo'].dropna().unique()
        print(f"   - Anos únicos: {sorted(anos_unicos) if len(anos_unicos) > 0 else 'Nenhum'}")
        print(f"   - Anos não identificados: {df['Ano Processo'].isna().sum()}")
    
    # 5. Verificar configuração de servidores
    print(f"\n5. CONFIGURAÇÃO DE SERVIDORES:")
    intervalos = config.get("intervalos_servidores", {})
    print(f"   - Servidores configurados: {list(intervalos.keys())}")
    for servidor, ints in intervalos.items():
        print(f"   - {servidor}: {ints}")
    
    return df