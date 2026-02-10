# app/core/logging.py
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Dict

from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Formatter customizado para logs estruturados em JSON.
    Adiciona campos padrão (timestamp, module) e trata exceções corretamente.
    """

    def add_fields(
        self,
        log_record: Dict[str, Any],
        record: logging.LogRecord,
        message_dict: Dict[str, Any],
    ) -> None:
        """
        Adiciona campos customizados ao record de log.
        
        Args:
            log_record: Dicionário que será serializado para JSON
            record: LogRecord original do Python
            message_dict: Mensagem formatada
        """
        super().add_fields(log_record, record, message_dict)
        
        # Adiciona timestamp ISO 8601 com timezone
        log_record["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        # Adiciona o módulo/logger name
        log_record["module"] = record.name
        
        # Normaliza o nível para minúsculas
        log_record["level"] = record.levelname.lower()
        
        # Adiciona execution_id se disponível no contexto
        if hasattr(record, "execution_id"):
            log_record["execution_id"] = record.execution_id
        
        # Trata exceções corretamente
        if record.exc_info and record.exc_text is None:
            log_record["exc_info"] = self.formatException(record.exc_info)
        
        # Remove fields desnecessários que vêm por padrão
        log_record.pop("asctime", None)


def configure_logging(level: str = "INFO") -> None:
    """
    Configura o logger raiz com formato JSON estruturado.
    
    Args:
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Example:
        >>> from app.core.logging import configure_logging
        >>> configure_logging("INFO")
    """
    # Remove handlers existentes
    root_logger = logging.getLogger()
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Cria handler para stdout com formato JSON
    stream_handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        fmt="%(timestamp)s %(level)s %(name)s %(message)s",
        json_ensure_ascii=False,
    )
    stream_handler.setFormatter(formatter)
    
    # Configura logger raiz
    root_logger.setLevel(getattr(logging, level.upper()))
    root_logger.addHandler(stream_handler)
    
    # Reduz verbosidade de bibliotecas externas
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("google").setLevel(logging.WARNING)
    logging.getLogger("google.cloud").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Retorna um logger customizado para um módulo específico.
    
    Args:
        name: Nome do módulo (__name__)
    
    Returns:
        Logger configurado para uso estruturado
    
    Example:
        >>> from app.core.logging import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Exemplo de log", extra={"execution_id": "abc123"})
    """
    return logging.getLogger(name)
