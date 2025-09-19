"""
Custom exceptions for Fantasy Football Manager
Provides meaningful exceptions that allow clients to make informed decisions
about error handling.
"""


class FantasyFootballManagerError(Exception):
    """Base exception for all Fantasy Football Manager errors"""
    pass


class AuthenticationError(FantasyFootballManagerError):
    """Raised when authentication fails or credentials are invalid"""
    pass


class DataValidationError(FantasyFootballManagerError):
    """Raised when data validation fails"""
    pass


class FileOperationError(FantasyFootballManagerError):
    """Raised when file operations fail"""
    pass


class BrowserOperationError(FantasyFootballManagerError):
    """Raised when browser automation operations fail"""
    pass


class ConfigurationError(FantasyFootballManagerError):
    """Raised when configuration is invalid or missing"""
    pass
