"""Input prompts using prompt_toolkit"""
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator, ValidationError
from typing import List, Optional
import os


class FileValidator(Validator):
    """Validator for file paths"""
    
    def validate(self, document):
        text = document.text
        if text and not os.path.exists(text):
            raise ValidationError(message="File does not exist")


class NotEmptyValidator(Validator):
    """Validator for non-empty input"""
    
    def validate(self, document):
        text = document.text.strip()
        if not text:
            raise ValidationError(message="Input cannot be empty")


class UIPrompts:
    """Collection of input prompts for the UI"""
    
    @staticmethod
    def prompt_session_name(existing_names: Optional[List[str]] = None) -> str:
        """
        Prompt for session name.
        
        Args:
            existing_names: List of existing session names (for validation)
            
        Returns:
            Session name
        """
        class SessionNameValidator(Validator):
            def validate(self, document):
                text = document.text.strip()
                if not text:
                    raise ValidationError(message="Session name cannot be empty")
                if existing_names and text in existing_names:
                    raise ValidationError(message="Session name already exists")
                if not text.replace('_', '').replace('-', '').isalnum():
                    raise ValidationError(message="Session name can only contain letters, numbers, hyphens, and underscores")
        
        return prompt("Session name: ", validator=SessionNameValidator()).strip()
    
    @staticmethod
    def prompt_device_id() -> str:
        """Prompt for device ID"""
        return prompt("Device ID: ", validator=NotEmptyValidator()).strip()
    
    @staticmethod
    def prompt_mqtt_prefix(default: str = "") -> str:
        """Prompt for MQTT prefix"""
        message = f"MQTT prefix [{default}]: " if default else "MQTT prefix: "
        result = prompt(message).strip()
        return result if result else default
    
    @staticmethod
    def prompt_notes() -> str:
        """Prompt for session notes (optional)"""
        return prompt("Notes (optional): ").strip()
    
    @staticmethod
    def prompt_file_path(prompt_text: str = "File path: ", must_exist: bool = True) -> str:
        """
        Prompt for file path.
        
        Args:
            prompt_text: Prompt message
            must_exist: If True, validate that file exists
            
        Returns:
            File path
        """
        validator = FileValidator() if must_exist else None
        return prompt(prompt_text, validator=validator).strip()
    
    @staticmethod
    def prompt_choice(prompt_text: str, choices: List[str], default: Optional[str] = None) -> str:
        """
        Prompt with auto-completion from choices.
        
        Args:
            prompt_text: Prompt message
            choices: List of valid choices
            default: Default choice
            
        Returns:
            Selected choice
        """
        completer = WordCompleter(choices, ignore_case=True)
        
        class ChoiceValidator(Validator):
            def validate(self, document):
                text = document.text.strip()
                if text and text not in choices:
                    raise ValidationError(message=f"Invalid choice. Options: {', '.join(choices)}")
        
        message = f"{prompt_text} [{default}]: " if default else f"{prompt_text}: "
        result = prompt(message, completer=completer, validator=ChoiceValidator()).strip()
        return result if result else (default or "")
    
    @staticmethod
    def prompt_yes_no(prompt_text: str, default: bool = False) -> bool:
        """
        Prompt for yes/no confirmation.
        
        Args:
            prompt_text: Prompt message
            default: Default value
            
        Returns:
            True for yes, False for no
        """
        default_text = "Y/n" if default else "y/N"
        result = prompt(f"{prompt_text} ({default_text}): ").strip().lower()
        
        if not result:
            return default
        
        return result in ['y', 'yes']
    
    @staticmethod
    def prompt_text(prompt_text: str, default: str = "", required: bool = False) -> str:
        """
        Prompt for text input.
        
        Args:
            prompt_text: Prompt message
            default: Default value
            required: If True, input cannot be empty
            
        Returns:
            Input text
        """
        validator = NotEmptyValidator() if required else None
        message = f"{prompt_text} [{default}]: " if default else f"{prompt_text}: "
        result = prompt(message, validator=validator).strip()
        return result if result else default
    
    @staticmethod
    def prompt_number(prompt_text: str, default: Optional[int] = None, 
                     min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
        """
        Prompt for number input.
        
        Args:
            prompt_text: Prompt message
            default: Default value
            min_val: Minimum value
            max_val: Maximum value
            
        Returns:
            Input number
        """
        class NumberValidator(Validator):
            def validate(self, document):
                text = document.text.strip()
                if not text and default is not None:
                    return
                try:
                    num = int(text)
                    if min_val is not None and num < min_val:
                        raise ValidationError(message=f"Value must be >= {min_val}")
                    if max_val is not None and num > max_val:
                        raise ValidationError(message=f"Value must be <= {max_val}")
                except ValueError:
                    raise ValidationError(message="Must be a valid number")
        
        message = f"{prompt_text} [{default}]: " if default is not None else f"{prompt_text}: "
        result = prompt(message, validator=NumberValidator()).strip()
        
        if not result and default is not None:
            return default
        
        return int(result)

