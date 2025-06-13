# utils/cache_utils.py - Utilitários para cache e persistência

import streamlit as st
import json
import os
from typing import Dict, Any

class CacheManager:
    """Gerenciador de cache para configurações do Streamlit"""
    
    @staticmethod
    def salvar_configuracao(configuracao: Dict[str, Any], nome_arquivo: str = "config.json") -> bool:
        """
        Salva configuração no cache do navegador (session_state) e opcionalmente em arquivo.
        
        Args:
            configuracao: Dicionário com as configurações
            nome_arquivo: Nome do arquivo para backup (opcional)
            
        Returns:
            bool: True se salvou com sucesso
        """
        try:
            # Salvar no cache do navegador (session_state)
            st.session_state.configuracao = configuracao.copy()
            
            # Tentar salvar backup em arquivo
            try:
                filepath = os.path.join(os.path.dirname(__file__), "..", "pages", nome_arquivo)
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(configuracao, f, indent=4, ensure_ascii=False)
                return True
            except Exception:
                # Se não conseguir salvar arquivo, pelo menos mantém no cache
                return True
                
        except Exception:
            return False
    
    @staticmethod
    def carregar_configuracao(nome_arquivo: str = "config.json") -> Dict[str, Any]:
        """
        Carrega configuração do cache ou arquivo.
        
        Args:
            nome_arquivo: Nome do arquivo de configuração
            
        Returns:
            Dict com as configurações
        """
        # Configuração padrão
        config_padrao = {
            "intervalos_servidores": {
                "ABEL": [[1, 19]],
                "CARLOS": [[20, 39]],
                "JACKMARA": [[40, 59]],
                "LEIDIANE": [[60, 79]],
                "TANIA": [[80, 99]]
            },
            "coluna_processos": "numeroProcesso",
            "ano_meta2": 2018
        }
        
        # Primeiro, verificar se existe no session_state
        if "configuracao" in st.session_state:
            return st.session_state.configuracao
        
        # Senão, tentar carregar do arquivo
        try:
            filepath = os.path.join(os.path.dirname(__file__), "..", "pages", nome_arquivo)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    # Salvar no cache para próximas vezes
                    st.session_state.configuracao = config
                    return config
        except Exception:
            pass
        
        # Se não conseguiu carregar, usar padrão e salvar no cache
        st.session_state.configuracao = config_padrao
        return config_padrao
    
    @staticmethod
    def limpar_cache():
        """Limpa o cache das configurações"""
        if "configuracao" in st.session_state:
            del st.session_state.configuracao
    
    @staticmethod
    def exportar_configuracao() -> str:
        """
        Exporta configuração atual como JSON string.
        
        Returns:
            String JSON com as configurações
        """
        config = CacheManager.carregar_configuracao()
        return json.dumps(config, indent=4, ensure_ascii=False)
    
    @staticmethod
    def importar_configuracao(json_str: str) -> bool:
        """
        Importa configuração de uma string JSON.
        
        Args:
            json_str: String JSON com as configurações
            
        Returns:
            bool: True se importou com sucesso
        """
        try:
            config = json.loads(json_str)
            return CacheManager.salvar_configuracao(config)
        except Exception:
            return False
    
    @staticmethod 
    def resetar_configuracao():
        """Reseta configuração para valores padrão"""
        config_padrao = {
            "intervalos_servidores": {
                "ABEL": [[1, 19]],
                "CARLOS": [[20, 39]],
                "JACKMARA": [[40, 59]], 
                "LEIDIANE": [[60, 79]],
                "TANIA": [[80, 99]]
            },
            "coluna_processos": "numeroProcesso",
            "ano_meta2": 2018
        }
        return CacheManager.salvar_configuracao(config_padrao)

# Funções convenientes para uso direto
def salvar_config(config: Dict[str, Any]) -> bool:
    """Função conveniente para salvar configuração"""
    return CacheManager.salvar_configuracao(config)

def carregar_config() -> Dict[str, Any]:
    """Função conveniente para carregar configuração"""
    return CacheManager.carregar_configuracao()

def obter_config_session_state() -> Dict[str, Any]:
    """Obtém configuração direto do session_state ou carrega se não existir"""
    if "configuracao" not in st.session_state:
        return carregar_config()
    return st.session_state.configuracao

def atualizar_config(updates: Dict[str, Any]):
    """Atualiza configuração no session_state"""
    if "configuracao" not in st.session_state:
        st.session_state.configuracao = carregar_config()
    
    st.session_state.configuracao.update(updates)

# Decorador para funcões que usam cache
def with_cache_config(func):
    """Decorador que garante que a configuração está carregada"""
    def wrapper(*args, **kwargs):
        if "configuracao" not in st.session_state:
            carregar_config()
        return func(*args, **kwargs)
    return wrapper