"""Credentials management for ClickHouse Client."""

import json
import os

from config import CREDENTIALS_FILE
from database import decrypt_password, encrypt_password


class CredentialsManager:
    """Manages saving and loading of multiple named database credentials."""

    def __init__(self, credentials_file: str = CREDENTIALS_FILE):
        self.credentials_file = credentials_file
        # Ensure the directory exists for the credentials file
        credentials_dir = os.path.dirname(self.credentials_file)
        if credentials_dir and not os.path.exists(credentials_dir):
            try:
                os.makedirs(credentials_dir, exist_ok=True)
            except Exception:
                # If we can't create the directory, fall back to current directory
                self.credentials_file = os.path.basename(self.credentials_file)

    def save_credentials(
        self,
        name: str,
        host: str,
        port: str,
        username: str,
        password: str,
        database: str,
    ) -> tuple[bool, str]:
        """
        Save named credentials to file.

        Args:
            name: Credential set name
            host: Database host
            port: Database port
            username: Database username
            password: Database password (will be encrypted)
            database: Database name

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            # Load existing credentials or create new structure
            all_credentials = self._load_all_credentials()

            credentials = {
                "host": host if host is not None else "localhost",
                "port": port if port is not None else "9000",
                "user": username if username is not None else "default",
                "database": database if database is not None else "default",
                "password": encrypt_password(password),
            }

            # Add or update the named credential
            all_credentials[name] = credentials

            # Ensure parent directory exists
            credentials_dir = os.path.dirname(self.credentials_file)
            if credentials_dir and not os.path.exists(credentials_dir):
                os.makedirs(credentials_dir, exist_ok=True)

            with open(self.credentials_file, "w") as f:
                json.dump(all_credentials, f, indent=2)

            return True, f"Credentials '{name}' saved successfully"

        except PermissionError:
            return (
                False,
                f"Permission denied: Cannot write to {self.credentials_file}. Please check file permissions.",
            )
        except Exception as e:
            return False, f"Failed to save credentials: {str(e)}"

    def load_credentials(self, name: str) -> tuple[bool, dict[str, str] | None, str]:
        """
        Load specific named credentials from file.

        Args:
            name: Name of the credential set to load

        Returns:
            tuple: (success: bool, credentials: dict or None, message: str)
        """
        try:
            all_credentials = self._load_all_credentials()

            if name not in all_credentials:
                return False, None, f"Credentials '{name}' not found"

            encrypted_credentials = all_credentials[name]

            # Decrypt password
            credentials = {
                "host": encrypted_credentials.get("host") or "localhost",
                "port": encrypted_credentials.get("port") or "9000",
                "user": encrypted_credentials.get("user") or "default",
                "database": encrypted_credentials.get("database") or "default",
                "password": decrypt_password(encrypted_credentials.get("password", "")),
            }

            return True, credentials, f"Credentials '{name}' loaded successfully"

        except Exception as e:
            return False, None, f"Failed to load credentials: {str(e)}"

    def get_credential_names(self) -> list[str]:
        """
        Get list of all saved credential names.

        Returns:
            List of credential names
        """
        try:
            all_credentials = self._load_all_credentials()
            return list(all_credentials.keys())
        except Exception:
            return []

    def delete_credentials(self, name: str) -> tuple[bool, str]:
        """
        Delete named credentials.

        Args:
            name: Name of the credential set to delete

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            all_credentials = self._load_all_credentials()

            if name not in all_credentials:
                return False, f"Credentials '{name}' not found"

            del all_credentials[name]

            # Ensure parent directory exists
            credentials_dir = os.path.dirname(self.credentials_file)
            if credentials_dir and not os.path.exists(credentials_dir):
                os.makedirs(credentials_dir, exist_ok=True)

            with open(self.credentials_file, "w") as f:
                json.dump(all_credentials, f, indent=2)

            return True, f"Credentials '{name}' deleted successfully"

        except PermissionError:
            return (
                False,
                f"Permission denied: Cannot write to {self.credentials_file}. Please check file permissions.",
            )
        except Exception as e:
            return False, f"Failed to delete credentials: {str(e)}"

    def _load_all_credentials(self) -> dict[str, dict[str, str]]:
        """
        Load all credentials from file.

        Returns:
            Dictionary of all credential sets
        """
        if not os.path.exists(self.credentials_file):
            return {}

        try:
            with open(self.credentials_file) as f:
                data = json.load(f)

            # Handle migration from old single-credential format
            if isinstance(data, dict) and "host" in data:
                # Old format - convert to new format with "default" name
                return {"default": data}

            return data if isinstance(data, dict) else {}

        except Exception:
            return {}

    # Legacy methods for backward compatibility
    def load_credentials_legacy(self) -> tuple[bool, dict[str, str] | None, str]:
        """
        Load best available credentials (prioritize cloud/remote over localhost).

        Returns:
            tuple: (success: bool, credentials: dict or None, message: str)
        """
        names = self.get_credential_names()
        if not names:
            return False, None, "No credentials found"

        # Try to find the best credential set to use
        # Priority: 1) cloud connections with valid passwords, 2) non-localhost with valid passwords, 3) any valid credential
        best_name = None
        fallback_name = None

        for name in names:
            success, creds, _ = self.load_credentials(name)
            if success and creds:
                host = creds.get("host", "")
                password = creds.get("password", "")
                has_valid_password = len(password.strip()) > 0

                # Prioritize cloud and remote connections over localhost, but only if they have valid passwords
                if "clickhouse.cloud" in host or (
                    "localhost" not in host and "127.0.0.1" not in host and host != ""
                ):
                    if has_valid_password:
                        best_name = name
                        break  # Found ideal credential - cloud/remote with valid password
                    elif best_name is None:
                        fallback_name = (
                            name  # Keep as fallback if no better option found
                        )
                elif (
                    best_name is None and fallback_name is None and has_valid_password
                ):  # Use first valid credential as ultimate fallback
                    fallback_name = name

        # Use best found credential, or fallback if no ideal one exists
        chosen_name = best_name or fallback_name

        if chosen_name is None:
            chosen_name = names[
                0
            ]  # Ultimate fallback - use first credential even if password is empty

        return self.load_credentials(chosen_name)

    def save_credentials_legacy(
        self, host: str, port: str, username: str, password: str, database: str
    ) -> tuple[bool, str]:
        """
        Save credentials with default name (for backward compatibility).
        """
        return self.save_credentials(
            "default", host, port, username, password, database
        )
