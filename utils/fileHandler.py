import pandas as pd
from csv import Sniffer

class FileHandler:
    """Classe utilitária para manipulação de arquivos CSV e Excel."""
    
    @staticmethod
    def read_file(file, file_type, config):
        """
        Lê um arquivo CSV ou Excel, realiza o pré-processamento inicial e retorna um DataFrame.
        
        Args:
            file: O arquivo enviado pelo usuário.
            file_type: Tipo do arquivo ('csv' ou 'xlsx').
            config: Configuração contendo a coluna de processos.
        
        Returns:
            pd.DataFrame: DataFrame com os dados lidos e pré-processados.
        """
        if file_type == "xlsx":
            df = pd.read_excel(file)
        elif file_type == "csv":
            # Detecta o delimitador e o caractere de aspas; utiliza fallback se necessário.
            delimiter, quotechar = FileHandler.detect_csv_properties(file)
            df = pd.read_csv(file, delimiter=delimiter, quotechar=quotechar)
        else:
            raise ValueError("Tipo de arquivo não suportado. Apenas CSV e XLSX são aceitos.")
        
        # Pré-processa o DataFrame (verifica a coluna de processos e extrai o dígito)
        df = FileHandler.preprocess_dataframe(df, config)
        return df

    @staticmethod
    def detect_csv_properties(file):
        """
        Detecta o delimitador de campo e o caractere de aspas em um arquivo CSV.
        Em caso de erro, utiliza um método alternativo baseado na contagem de delimitadores comuns.

        Args:
            file: O arquivo CSV.

        Returns:
            tuple: Um par contendo (delimiter, quotechar).
        """
        try:
            # Lê uma amostra do arquivo com tratamento de possíveis erros de decodificação
            sample = file.read(1024).decode("utf-8", errors="replace")
            file.seek(0)  # Retorna ao início do arquivo após a leitura

            # Tenta detectar as propriedades com csv.Sniffer
            sniffer = Sniffer()
            dialect = sniffer.sniff(sample)
            return dialect.delimiter, dialect.quotechar
        except Exception as e:
            # Em caso de falha, utiliza a contagem de vírgulas e ponto‑vírgulas como fallback
            file.seek(0)
            sample = file.read(1024).decode("utf-8", errors="replace")
            file.seek(0)
            if sample.count(',') >= sample.count(';'):
                return ",", '"'
            elif sample.count(';') > 0:
                return ";", '"'
            else:
                # Caso nenhum delimitador seja identificado, retorna valores padrão (vírgula e aspas duplas)
                return ",", '"'

    @staticmethod
    def preprocess_dataframe(df, config):
        """
        Pré-processa o DataFrame, garantindo que a coluna de processos exista e tratando os dígitos.

        Args:
            df: DataFrame lido do arquivo.
            config: Configuração contendo o nome da coluna de processos.

        Returns:
            pd.DataFrame: DataFrame pré-processado.
        """
        coluna_processos = config.get('coluna_processos', 'Processos')
        
        if coluna_processos not in df.columns:
            raise KeyError(f"A coluna '{coluna_processos}' não foi encontrada na planilha.")
        
        # Garante que a coluna de processos seja do tipo string para aplicar regex
        if not pd.api.types.is_string_dtype(df[coluna_processos]):
            df[coluna_processos] = df[coluna_processos].astype(str)
        
        # Extração do dígito (assumindo o padrão "-XX.") com tratamento de valores inválidos
        df['Dígito'] = df[coluna_processos].str.extract(r'-(\d{2})\.')[0]
        df['Dígito'] = pd.to_numeric(df['Dígito'], errors='coerce').fillna(0).astype(int)

        return df
