"""SQL autocomplete functionality for ClickHouse Client."""

import re
from typing import Dict, List, Optional, Set, Tuple

from database import DatabaseManager


class AutocompleteManager:
    """Manages SQL autocomplete functionality for table suggestions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.tables_cache: List[str] = []

    def cache_tables(self):
        """Cache the list of tables from the database."""
        if not self.db_manager.is_connected:
            self.tables_cache = []
            return

        try:
            self.tables_cache = self.db_manager.get_tables()
            print(f"DEBUG: Cached {len(self.tables_cache)} tables")
        except Exception as e:
            print(f"DEBUG: Error caching tables: {e}")
            self.tables_cache = []

    def get_cached_tables(self) -> List[str]:
        """Get the cached list of tables."""
        return self.tables_cache.copy()

    def get_table_columns(self, table_name: str) -> List[Tuple[str, str]]:
        """Get columns for a table - kept for compatibility but not used in autocomplete."""
        if not table_name or not self.db_manager.is_connected:
            return []

        table_name = table_name.strip()

        # Fetch from database
        try:
            columns = self.db_manager.get_table_columns(table_name)
            return columns
        except Exception:
            return []

    def extract_tables_from_query(self, query: str) -> Set[str]:
        """Extract table names referenced in the SQL query."""
        tables = set()

        if not query or not query.strip():
            return tables

        # Convert to uppercase for pattern matching but preserve original case
        query_upper = query.upper()
        query_lines = query.split('\n')

        # Pattern to match table names after FROM, JOIN, UPDATE, INSERT INTO, etc.
        patterns = [
            r'\bFROM\s+([`"]?)(\w+)\1(?:\s+(?:AS\s+)?(\w+))?',  # FROM table [AS alias]
            r'\bJOIN\s+([`"]?)(\w+)\1(?:\s+(?:AS\s+)?(\w+))?',  # JOIN table [AS alias] 
            r'\bUPDATE\s+([`"]?)(\w+)\1',                        # UPDATE table
            r'\bINSERT\s+INTO\s+([`"]?)(\w+)\1',                # INSERT INTO table
            r'\bDELETE\s+FROM\s+([`"]?)(\w+)\1'                 # DELETE FROM table
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, query_upper)
            for match in matches:
                table_name = match.group(2)
                if table_name:
                    tables.add(table_name.lower())  # Store as lowercase for consistency

        return tables

    def get_cursor_context(self, query: str, cursor_pos: int) -> Dict[str, any]:
        """
        Analyze the cursor position in the query to determine autocomplete context.
        
        Returns:
            Dict with context information including:
            - 'word_start': Start position of current word
            - 'word_end': End position of current word  
            - 'current_word': The word being typed
            - 'context_type': Type of autocomplete needed ('column', 'table', 'keyword', etc.)
            - 'tables': List of tables available for column suggestions
        """
        # Handle empty query case
        if not query:
            return {
                'context_type': 'keyword',  # Empty query should suggest keywords
                'word_start': 0,
                'word_end': 0,
                'current_word': '',
                'tables': [],
                'context_before': '',
                'context_after': ''
            }

        if cursor_pos < 0:
            cursor_pos = 0
        elif cursor_pos > len(query):
            cursor_pos = len(query)

        # Find word boundaries around cursor
        word_start = cursor_pos
        word_end = cursor_pos
        current_word = ""

        # If cursor is at the end of the query, check if we're at the end of a word
        if cursor_pos == len(query) and cursor_pos > 0:
            # Check if the last character is part of a word
            if query[cursor_pos - 1].isalnum() or query[cursor_pos - 1] in '_':
                # We're at the end of a word, find its start
                word_end = cursor_pos
                word_start = cursor_pos
                while word_start > 0 and (query[word_start - 1].isalnum() or query[word_start - 1] in '_'):
                    word_start -= 1
                current_word = query[word_start:word_end]
            # If last character is space, no current word
        elif cursor_pos > 0 and cursor_pos < len(query):
            # Cursor is in the middle of the query
            if query[cursor_pos - 1].isspace():
                # Cursor is after a space, no current word
                current_word = ""
                word_start = cursor_pos
                word_end = cursor_pos
            else:
                # Find word boundaries around cursor
                word_start = cursor_pos
                word_end = cursor_pos

                # Move backward to find word start
                while word_start > 0 and (query[word_start - 1].isalnum() or query[word_start - 1] in '_'):
                    word_start -= 1

                # Move forward to find word end
                while word_end < len(query) and (query[word_end].isalnum() or query[word_end] in '_'):
                    word_end += 1

                current_word = query[word_start:word_end]

        # Get text before and after cursor position (not word position)
        text_before_cursor = query[:cursor_pos].strip()
        text_after_cursor = query[cursor_pos:].strip()

        # Clean and normalize the text for analysis
        context_before = text_before_cursor.upper()
        context_after = text_after_cursor.upper()

        # Extract tables from the query
        tables = self.extract_tables_from_query(query)

        # Determine autocomplete type based on context - more sophisticated logic
        context_type = self._determine_context_type(context_before, context_after, current_word)

        return {
            'word_start': word_start,
            'word_end': word_end,
            'current_word': current_word,
            'context_type': context_type,
            'tables': list(tables),
            'context_before': context_before,
            'context_after': context_after
        }

    def _determine_context_type(self, context_before: str, context_after: str, current_word: str) -> str:
        """Determine the appropriate context type for autocomplete suggestions."""
        # Remove comments and normalize whitespace
        context_clean = re.sub(r'--[^\n]*', '', context_before).strip()

        # Split into tokens to analyze the SQL structure
        tokens = re.findall(r'\b\w+\b', context_clean)
        if not tokens:
            return "none"

        # Look at the last few tokens to determine context
        last_tokens = tokens[-3:] if len(tokens) >= 3 else tokens
        last_token = tokens[-1] if tokens else ''

        # Special case: if the last token is a partial word that's not a complete SQL keyword,
        # we need to look at the token before it to determine context
        if current_word and len(tokens) >= 2:
            # Check if current word might be a partial table name
            second_last_token = tokens[-2] if len(tokens) >= 2 else ''

            # If the second-to-last token suggests table context, use table context
            if second_last_token in {"FROM", "JOIN", "UPDATE"} or " ".join(
                tokens[-3:-1]
            ) in {"INNER JOIN", "LEFT JOIN", "RIGHT JOIN"}:
                return 'table'

        # Table context patterns
        table_keywords = {
            'FROM', 'JOIN', 'UPDATE', 'INTO'
        }
        table_phrases = {
            'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'FULL JOIN', 'OUTER JOIN',
            'CROSS JOIN', 'INSERT INTO'
        }

        # Check for table context - prioritize this check
        if last_token in table_keywords:
            return 'table'

        # Check for multi-word table phrases
        last_two = ' '.join(last_tokens[-2:]) if len(last_tokens) >= 2 else ''
        if last_two in table_phrases:
            print(f"DEBUG: Found table context from phrase: {last_two}")
            return 'table'

        # No suggestions for other contexts
        print("DEBUG: No table context found, returning none")
        return "none"

    def get_suggestions(self, query: str, cursor_pos: int) -> List[Dict[str, str]]:
        """
        Get autocomplete suggestions based on query and cursor position.
        
        Returns:
            List of suggestion dictionaries with 'text', 'type', and 'description' keys
        """
        context = self.get_cursor_context(query, cursor_pos)
        suggestions = []

        print(f"DEBUG: Context for '{query}' at pos {cursor_pos}: {context}")

        if context['context_type'] == 'none':
            return suggestions

        current_word = context['current_word'].lower()
        print(f"DEBUG: Current word: '{current_word}', Context type: {context['context_type']}")

        if context["context_type"] == "table":
            # Suggest table names from the cached list
            cached_tables = self.get_cached_tables()

            if cached_tables:
                for table_name in sorted(cached_tables):
                    # Get table metadata for better descriptions
                    try:
                        columns = self.get_table_columns(table_name)
                        column_count = len(columns)
                        description = f"Table: {table_name} ({column_count} columns)"
                    except:
                        description = f"Table: {table_name}"

                    suggestions.append(
                        {
                            "text": table_name,
                            "type": "table",
                            "description": description,
                        }
                    )
            else:
                # If no cached tables, provide info message
                if not self.db_manager.is_connected:
                    suggestions.append(
                        {
                            "text": "-- Connect to database to see table suggestions --",
                            "type": "info",
                            "description": "Database connection required for table names",
                        }
                    )
                else:
                    # Database connected but no cached tables - suggest refreshing
                    suggestions.append(
                        {
                            "text": "-- No tables found. Check database connection --",
                            "type": "info",
                            "description": "No tables available in the current database",
                        }
                    )

                # Also provide common table name suggestions as fallback
                common_tables = ['users', 'orders', 'products', 'events', 'logs', 'analytics', 'metrics', 'sessions']
                for table in common_tables:
                    suggestions.append(
                        {
                            "text": table,
                            "type": "table",
                            "description": f"Common table name: {table}",
                        }
                    )

        # Apply fuzzy matching and filtering - but don't filter out everything when current_word is empty
        if current_word and current_word.strip():
            suggestions = self._filter_and_rank_suggestions(suggestions, current_word)
        else:
            # No current word - return all suggestions without filtering
            suggestions = suggestions[:20]

        return suggestions

    def _fuzzy_match_score(self, text: str, query: str) -> float:
        """
        Calculate fuzzy match score between text and query.
        Returns a score between 0.0 and 1.0, higher is better match.
        """
        if not query or query.strip() == "":
            return 1.0

        text_lower = text.lower()
        query_lower = query.lower()

        # Exact match gets highest score
        if text_lower == query_lower:
            return 1.0

        # Starts with match gets high score
        if text_lower.startswith(query_lower):
            return 0.95

        # Contains match gets good score
        if query_lower in text_lower:
            # Score based on position - earlier is better
            pos = text_lower.find(query_lower)
            position_bonus = 1.0 - (pos / len(text_lower))
            return 0.7 + (position_bonus * 0.2)  # 0.7 to 0.9

        # Word boundary match (e.g., "us" matches "user_id" at word start)
        import re
        if re.search(r'\b' + re.escape(query_lower), text_lower):
            return 0.6

        # Character sequence match (fuzzy) - be more lenient
        query_chars = list(query_lower)
        text_chars = list(text_lower)

        if len(query_chars) > len(text_chars):
            return 0.0  # Query longer than text

        score = 0.0
        text_idx = 0
        matches = 0

        for query_char in query_chars:
            # Find this character in the remaining text
            found = False
            for i in range(text_idx, len(text_chars)):
                if text_chars[i] == query_char:
                    # Award points based on how close the character is
                    distance_bonus = 1.0 - (i - text_idx) / max(1, len(text_chars) - text_idx)
                    score += distance_bonus / len(query_chars)
                    text_idx = i + 1
                    found = True
                    matches += 1
                    break

            if not found:
                break  # Stop at first non-matching character

        # Require at least 30% of characters to match for short queries (was 50-70%)
        min_match_ratio = 0.3 if len(query_chars) <= 3 else 0.5
        if matches / len(query_chars) < min_match_ratio:
            return 0.0

        # Cap fuzzy matches but be more generous
        return min(score, 0.5)  # Fuzzy matches up to 0.5

    def _filter_and_rank_suggestions(self, suggestions: List[Dict[str, str]], query: str) -> List[Dict[str, str]]:
        """Filter and rank suggestions based on relevance to the query."""
        if not query or query.strip() == "":
            # If no query or empty query, return all suggestions (don't filter)
            return suggestions[:20]

        # Calculate scores for each suggestion
        scored_suggestions = []
        for suggestion in suggestions:
            # Skip filtering for info messages - always include them
            if suggestion.get('type') == 'info':
                suggestion_copy = suggestion.copy()
                suggestion_copy['_score'] = 1.0  # Give info messages high priority
                scored_suggestions.append(suggestion_copy)
                continue

            score = self._fuzzy_match_score(suggestion['text'], query)
            if score > 0.0:  # Only include matches with some relevance
                suggestion_copy = suggestion.copy()
                suggestion_copy['_score'] = score
                scored_suggestions.append(suggestion_copy)

        # If no matches found but we have a query, be more lenient
        if not scored_suggestions and query:
            # Include suggestions that contain any character from the query
            for suggestion in suggestions:
                if suggestion.get('type') == 'info':
                    continue
                text_lower = suggestion['text'].lower()
                query_lower = query.lower()
                # Check if any character from query appears in text
                if any(char in text_lower for char in query_lower):
                    suggestion_copy = suggestion.copy()
                    suggestion_copy['_score'] = 0.1  # Low score but included
                    scored_suggestions.append(suggestion_copy)

        # Sort by score (descending) and then by text (ascending)
        scored_suggestions.sort(key=lambda x: (-x['_score'], x['text'].lower()))

        # Remove the score field and return top matches
        for suggestion in scored_suggestions:
            del suggestion['_score']

        return scored_suggestions[:20]

    def clear_cache(self):
        """Clear the tables cache."""
        self.tables_cache.clear()
        print("DEBUG: Tables cache cleared")
