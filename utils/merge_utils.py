# utils/merge_utils.py - Utilitários para união de planilhas

import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import re

class MergeUtils:
    """Classe utilitária para operações de união de planilhas"""
    
    @staticmethod
    def clean_column_for_comparison(series: pd.Series) -> pd.Series:
        """
        Limpa uma coluna para melhor comparação, especialmente útil para números de processo.
        
        Args:
            series: Série pandas para limpeza
            
        Returns:
            Série limpa
        """
        # Converter para string
        cleaned = series.astype(str)
        
        # Remover espaços extras
        cleaned = cleaned.str.strip()
        
        # Para números de processo, padronizar formato
        # Remove caracteres especiais extras e padroniza
        def normalize_processo(value):
            if pd.isna(value) or value in ['nan', 'None', '']:
                return value
            
            # Remover espaços e caracteres especiais desnecessários
            value = re.sub(r'\s+', '', str(value))
            
            # Se parece com número de processo, tentar padronizar
            if re.match(r'\d+[-\.]\d+', value):
                # Remover pontos e hífens extras, manter apenas estrutura principal
                value = re.sub(r'\.+', '.', value)
                value = re.sub(r'-+', '-', value)
            
            return value
        
        cleaned = cleaned.apply(normalize_processo)
        
        return cleaned
    
    @staticmethod
    def analyze_columns_compatibility(df1: pd.DataFrame, col1: str, df2: pd.DataFrame, col2: str) -> Dict[str, Any]:
        """
        Analisa a compatibilidade entre duas colunas para união.
        
        Args:
            df1, df2: DataFrames
            col1, col2: Nomes das colunas
            
        Returns:
            Dicionário com análise de compatibilidade
        """
        # Limpar colunas
        series1_clean = MergeUtils.clean_column_for_comparison(df1[col1])
        series2_clean = MergeUtils.clean_column_for_comparison(df2[col2])
        
        # Converter para sets para análise
        values1 = set(series1_clean.dropna())
        values2 = set(series2_clean.dropna())
        
        # Análise
        common_values = values1.intersection(values2)
        only_in_1 = values1.difference(values2)
        only_in_2 = values2.difference(values1)
        
        # Estatísticas
        total_unique_1 = len(values1)
        total_unique_2 = len(values2)
        common_count = len(common_values)
        
        compatibility_score = (common_count / max(total_unique_1, total_unique_2)) * 100 if max(total_unique_1, total_unique_2) > 0 else 0
        
        return {
            'total_unique_1': total_unique_1,
            'total_unique_2': total_unique_2,
            'common_values': common_count,
            'only_in_1': len(only_in_1),
            'only_in_2': len(only_in_2),
            'compatibility_score': compatibility_score,
            'common_examples': list(common_values)[:10],
            'only_in_1_examples': list(only_in_1)[:5],
            'only_in_2_examples': list(only_in_2)[:5],
            'null_count_1': df1[col1].isnull().sum(),
            'null_count_2': df2[col2].isnull().sum()
        }
    
    @staticmethod
    def smart_merge(df1: pd.DataFrame, df2: pd.DataFrame, 
                   left_on: str, right_on: str,
                   left_columns: List[str] = None,
                   right_columns: List[str] = None,
                   how: str = 'inner',
                   suffixes: Tuple[str, str] = ('_x', '_y'),
                   clean_comparison_columns: bool = True) -> pd.DataFrame:
        """
        Executa uma união inteligente entre dois DataFrames.
        
        Args:
            df1, df2: DataFrames para unir
            left_on, right_on: Colunas de comparação
            left_columns, right_columns: Colunas para manter (None = todas)
            how: Tipo de join ('inner', 'left', 'right', 'outer')
            suffixes: Sufixos para colunas duplicadas
            clean_comparison_columns: Se deve limpar colunas de comparação
            
        Returns:
            DataFrame resultado da união
        """
        # Preparar DataFrames
        df1_work = df1.copy()
        df2_work = df2.copy()
        
        # Selecionar colunas
        if left_columns:
            df1_work = df1_work[left_columns]
        
        if right_columns:
            # Garantir que a coluna de comparação está incluída
            if right_on not in right_columns:
                right_columns = [right_on] + right_columns
            df2_work = df2_work[right_columns]
        
        # Limpar colunas de comparação se solicitado
        if clean_comparison_columns:
            df1_work[left_on] = MergeUtils.clean_column_for_comparison(df1_work[left_on])
            df2_work[right_on] = MergeUtils.clean_column_for_comparison(df2_work[right_on])
        
        # Executar merge
        result = pd.merge(
            df1_work,
            df2_work,
            left_on=left_on,
            right_on=right_on,
            how=how,
            suffixes=suffixes
        )
        
        # Limpar coluna duplicada se necessário
        if left_on != right_on and right_on in result.columns:
            # Se as colunas são idênticas após merge, remover duplicata
            if result[left_on].equals(result[right_on]):
                result = result.drop(columns=[right_on])
        
        return result
    
    @staticmethod
    def generate_merge_report(df1: pd.DataFrame, df2: pd.DataFrame, 
                            result: pd.DataFrame,
                            left_on: str, right_on: str) -> Dict[str, Any]:
        """
        Gera relatório detalhado sobre a operação de merge.
        
        Args:
            df1, df2: DataFrames originais
            result: DataFrame resultado
            left_on, right_on: Colunas de comparação
            
        Returns:
            Dicionário com relatório detalhado
        """
        return {
            'original_rows': {
                'df1': len(df1),
                'df2': len(df2)
            },
            'original_columns': {
                'df1': len(df1.columns),
                'df2': len(df2.columns)
            },
            'result_rows': len(result),
            'result_columns': len(result.columns),
            'data_quality': {
                'null_values_result': result.isnull().sum().sum(),
                'duplicate_rows_result': result.duplicated().sum(),
                'memory_usage_mb': result.memory_usage(deep=True).sum() / 1024 / 1024
            },
            'column_mapping': {
                'from_df1': [col for col in result.columns if col in df1.columns],
                'from_df2': [col for col in result.columns if col in df2.columns],
                'new_columns': [col for col in result.columns if col not in df1.columns and col not in df2.columns]
            }
        }
    
    @staticmethod
    def suggest_merge_strategy(df1: pd.DataFrame, df2: pd.DataFrame,
                              left_on: str, right_on: str) -> Dict[str, Any]:
        """
        Sugere a melhor estratégia de merge baseada na análise dos dados.
        
        Args:
            df1, df2: DataFrames
            left_on, right_on: Colunas de comparação
            
        Returns:
            Dicionário com sugestões
        """
        compatibility = MergeUtils.analyze_columns_compatibility(df1, left_on, df2, right_on)
        
        # Determinar melhor estratégia
        if compatibility['compatibility_score'] > 80:
            recommended_join = 'inner'
            reason = "Alta compatibilidade entre as colunas - INNER JOIN recomendado"
        elif compatibility['compatibility_score'] > 50:
            recommended_join = 'left'
            reason = "Compatibilidade média - LEFT JOIN recomendado para preservar dados da primeira planilha"
        else:
            recommended_join = 'outer'
            reason = "Baixa compatibilidade - OUTER JOIN recomendado para preservar todos os dados"
        
        # Sugestões de limpeza
        cleaning_suggestions = []
        
        if compatibility['null_count_1'] > 0 or compatibility['null_count_2'] > 0:
            cleaning_suggestions.append("Considere tratar valores nulos nas colunas de comparação")
        
        if compatibility['compatibility_score'] < 70:
            cleaning_suggestions.append("Considere padronizar o formato das colunas de comparação")
        
        return {
            'recommended_join_type': recommended_join,
            'reason': reason,
            'compatibility_score': compatibility['compatibility_score'],
            'cleaning_suggestions': cleaning_suggestions,
            'expected_result_size': {
                'inner': compatibility['common_values'],
                'left': len(df1),
                'right': len(df2),
                'outer': compatibility['total_unique_1'] + compatibility['total_unique_2'] - compatibility['common_values']
            }
        }
    
    @staticmethod
    def validate_merge_inputs(df1: pd.DataFrame, df2: pd.DataFrame,
                            left_on: str, right_on: str,
                            left_columns: List[str] = None,
                            right_columns: List[str] = None) -> Dict[str, Any]:
        """
        Valida os inputs para operação de merge.
        
        Returns:
            Dicionário com validação e erros (se houver)
        """
        errors = []
        warnings = []
        
        # Validar colunas de comparação
        if left_on not in df1.columns:
            errors.append(f"Coluna '{left_on}' não encontrada na primeira planilha")
        
        if right_on not in df2.columns:
            errors.append(f"Coluna '{right_on}' não encontrada na segunda planilha")
        
        # Validar colunas selecionadas
        if left_columns:
            missing_left = [col for col in left_columns if col not in df1.columns]
            if missing_left:
                errors.append(f"Colunas não encontradas na primeira planilha: {missing_left}")
        
        if right_columns:
            missing_right = [col for col in right_columns if col not in df2.columns]
            if missing_right:
                errors.append(f"Colunas não encontradas na segunda planilha: {missing_right}")
        
        # Verificar se DataFrames não estão vazios
        if len(df1) == 0:
            warnings.append("Primeira planilha está vazia")
        
        if len(df2) == 0:
            warnings.append("Segunda planilha está vazia")
        
        # Verificar tamanhos muito diferentes
        size_ratio = max(len(df1), len(df2)) / max(min(len(df1), len(df2)), 1)
        if size_ratio > 10:
            warnings.append(f"Planilhas têm tamanhos muito diferentes ({len(df1)} vs {len(df2)} linhas)")
        
        return {
            'is_valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings
        }