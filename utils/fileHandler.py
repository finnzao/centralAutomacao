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
            # Lê arquivo Excel
            df = pd.read_excel(file)
        elif file_type == "csv":
            # Detecta o delimitador e o delimitador de texto automaticamente
            delimiter, quotechar = FileHandler.detect_csv_properties(file)
            df = pd.read_csv(file, delimiter=delimiter, quotechar=quotechar)
        else:
            raise ValueError("Tipo de arquivo não suportado. Apenas CSV e XLSX são aceitos.")
        
        # Realiza o pré-processamento inicial (garante que a coluna existe e trata dígitos)
        df = FileHandler.preprocess_dataframe(df, config)
        return df

    @staticmethod
    def detect_csv_properties(file):
        """
        Detecta o delimitador de campo e o delimitador de texto em um arquivo CSV.

        Args:
            file: O arquivo CSV.

        Returns:
            tuple: Um par contendo (delimiter, quotechar).
        """
        try:
            # Lê uma amostra do arquivo
            sample = file.read(1024).decode("utf-8")
            file.seek(0)  # Retorna ao início do arquivo após a leitura

            # Usa o Sniffer para detectar delimitador e delimitador de texto
            sniffer = Sniffer()
            dialect = sniffer.sniff(sample)

            return dialect.delimiter, dialect.quotechar
        except Exception as e:
            raise RuntimeError(f"Erro ao detectar propriedades do CSV: {e}")

    @staticmethod
    def preprocess_dataframe(df, config):
        """
        Pré-processa o DataFrame, garantindo que a coluna de processos exista e lidando com os dígitos.

        Args:
            df: DataFrame lido do arquivo.
            config: Configuração contendo o nome da coluna de processos.

        Returns:
            pd.DataFrame: DataFrame pré-processado.
        """
        coluna_processos = config.get('coluna_processos', 'Processos')
        
        if coluna_processos not in df.columns:
            raise KeyError(f"A coluna '{coluna_processos}' não foi encontrada na planilha.")

        # Extração do dígito com tratamento de NaN
        df['Dígito'] = df[coluna_processos].str.extract(r'-(\d{2})\.')[0]
        df['Dígito'] = pd.to_numeric(df['Dígito'], errors='coerce').fillna(0).astype(int)

        return df