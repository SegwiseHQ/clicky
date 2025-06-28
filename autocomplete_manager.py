"""SQL autocomplete functionality for ClickHouse Client."""

import re
from typing import Dict, List, Optional, Set, Tuple

from database import DatabaseManager


class AutocompleteManager:
    """Manages SQL autocomplete functionality for column names and table suggestions."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.table_columns_cache: Dict[str, List[Tuple[str, str]]] = {}
        self.sql_keywords = [
            # Primary keywords
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP',
            'ALTER', 'TABLE', 'DATABASE', 'INDEX', 'VIEW', 'JOIN', 'INNER', 'LEFT', 
            'RIGHT', 'FULL', 'OUTER', 'ON', 'UNION', 'ALL', 'DISTINCT', 'GROUP', 'BY', 
            'ORDER', 'HAVING', 'LIMIT', 'OFFSET', 'AS', 'CASE', 'WHEN', 'THEN', 'ELSE', 
            'END', 'IF', 'EXISTS', 'WITH', 'RECURSIVE', 'USING', 'NATURAL',
            # ClickHouse specific keywords
            'PREWHERE', 'FINAL', 'SAMPLE', 'ARRAY', 'GLOBAL', 'ANY', 'ASOF', 'SETTINGS',
            'FORMAT', 'INTO OUTFILE', 'TOTALS', 'EXTREMES', 'OPTIMIZE', 'SYSTEM',
            # Functions (common and ClickHouse-specific)
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CAST', 'SUBSTRING', 'LENGTH', 
            'UPPER', 'LOWER', 'TRIM', 'CONCAT', 'NOW', 'CURRENT_DATE', 'toString',
            'toDate', 'toInt32', 'toFloat64', 'formatDateTime', 'groupArray', 'uniq',
            'uniqExact', 'topK', 'quantile', 'median', 'stddevPop', 'varPop',
            'argMax', 'argMin', 'any', 'anyLast', 'groupUniqArray', 'sumMap',
            'minMap', 'maxMap', 'avgMap', 'groupBitAnd', 'groupBitOr', 'groupBitXor',
            # Data types
            'UInt8', 'UInt16', 'UInt32', 'UInt64', 'Int8', 'Int16', 'Int32', 'Int64',
            'Float32', 'Float64', 'String', 'FixedString', 'UUID', 'Date', 'DateTime',
            'DateTime64', 'Enum8', 'Enum16', 'Array', 'Tuple', 'Nullable', 'LowCardinality'
        ]

    def get_table_columns(self, table_name: str) -> List[Tuple[str, str]]:
        """Get columns for a table, using cache when possible."""
        if not table_name or not self.db_manager.is_connected:
            return []

        table_name = table_name.strip()

        # Check cache first
        if table_name in self.table_columns_cache:
            return self.table_columns_cache[table_name]

        # Fetch from database
        try:
            columns = self.db_manager.get_table_columns(table_name)
            self.table_columns_cache[table_name] = columns
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

        print(f"DEBUG: Determining context for: '{context_clean}'")

        # Split into tokens to analyze the SQL structure
        tokens = re.findall(r'\b\w+\b', context_clean)
        if not tokens:
            print("DEBUG: No tokens found, returning keyword context")
            return 'keyword'

        print(f"DEBUG: Tokens found: {tokens}")

        # Look at the last few tokens to determine context
        last_tokens = tokens[-3:] if len(tokens) >= 3 else tokens
        last_token = tokens[-1] if tokens else ''

        print(f"DEBUG: Last token: '{last_token}', Last tokens: {last_tokens}")

        # Special case: if the last token is a partial word that's not a complete SQL keyword,
        # we need to look at the token before it to determine context
        if current_word and len(tokens) >= 2:
            # Check if current word might be a partial column/table name
            second_last_token = tokens[-2] if len(tokens) >= 2 else ''

            print(f"DEBUG: Second last token: '{second_last_token}'")

            # If the second-to-last token suggests column context, use column context
            if second_last_token in {'SELECT', 'WHERE', 'HAVING', 'PREWHERE', 'AND', 'OR', 'ON'}:
                print("DEBUG: Found column context from second-to-last token")
                return 'column'

            # If the second-to-last token suggests table context, use table context
            if second_last_token in {'FROM', 'JOIN', 'UPDATE'} or ' '.join(tokens[-3:-1]) in {'INNER JOIN', 'LEFT JOIN', 'RIGHT JOIN'}:
                print("DEBUG: Found table context from second-to-last token")
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
            print(f"DEBUG: Found table context from last token: {last_token}")
            return 'table'

        # Check for multi-word table phrases
        last_two = ' '.join(last_tokens[-2:]) if len(last_tokens) >= 2 else ''
        if last_two in table_phrases:
            print(f"DEBUG: Found table context from phrase: {last_two}")
            return 'table'

        # Column context patterns
        column_keywords = {
            'SELECT', 'WHERE', 'HAVING', 'PREWHERE', 'BY', 'AND', 'OR', 'ON'
        }
        column_phrases = {
            'ORDER BY', 'GROUP BY'
        }

        # Check for column context
        if last_token in column_keywords:
            print(f"DEBUG: Found column context from last token: {last_token}")
            return 'column'

        if last_two in column_phrases:
            print(f"DEBUG: Found column context from phrase: {last_two}")
            return 'column'

        # Check for comma in SELECT clause (column context)
        if ',' in context_before and any(kw in context_before for kw in ['SELECT']):
            # Check if we're still in the SELECT clause (before FROM)
            select_pos = context_before.rfind('SELECT')
            from_pos = context_before.rfind('FROM')
            if from_pos == -1 or select_pos > from_pos:
                print("DEBUG: Found column context from SELECT clause comma")
                return 'column'

        # Special case: Check if we're positioned after column names in a SELECT statement
        # This handles cases like "SELECT name " where we want to add more columns
        if "SELECT" in context_before:
            select_pos = context_before.rfind("SELECT")
            from_pos = context_before.rfind("FROM")

            # If we're after SELECT but before FROM (or no FROM yet)
            if from_pos == -1 or select_pos > from_pos:
                # Check if the content after SELECT looks like column names
                after_select = context_before[select_pos + 6 :].strip()

                # If we have content after SELECT that's not just whitespace, and we're not immediately
                # after SELECT keyword, we're likely in column position
                if after_select and not after_select.endswith(
                    ("FROM", "WHERE", "GROUP", "ORDER", "HAVING")
                ):
                    # Additional check: make sure we're not in a function call or complex expression
                    if not re.search(
                        r"\([^)]*$", after_select
                    ):  # Not in unclosed parentheses
                        print(
                            "DEBUG: Found column context from SELECT statement position"
                        )
                        return "column"

        # Check for comparison operators (column context)
        if re.search(r'[=<>!]\s*$', context_before):
            print("DEBUG: Found column context from comparison operator")
            return 'column' 

        # Check for WHERE clause continuation
        if 'WHERE' in context_before:
            where_pos = context_before.rfind('WHERE')
            # Look for logical operators after WHERE
            after_where = context_before[where_pos:]
            if re.search(r'\b(AND|OR)\s*$', after_where):
                print("DEBUG: Found column context from WHERE clause continuation")
                return 'column'

        # Default to keyword suggestions
        print("DEBUG: Defaulting to keyword context")
        return 'keyword'

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

        if context['context_type'] == 'column':
            # Suggest column names from ALL tables in the database (not just query tables)
            all_columns = set()
            table_sources = {}  # Track which table each column comes from

            if self.db_manager.is_connected:
                try:
                    # Get all tables in the database
                    all_tables = self.db_manager.get_tables()

                    # Get columns from all tables
                    for table_name in all_tables:
                        columns = self.get_table_columns(table_name)
                        for col_name, col_type in columns:
                            col_key = col_name.lower()
                            all_columns.add(col_key)
                            if col_key not in table_sources:
                                table_sources[col_key] = []
                            table_sources[col_key].append((table_name, col_type))

                except Exception as e:
                    print(f"Error fetching all table columns: {e}")

            # If no columns found and database is not connected, provide helpful message
            if not all_columns and not self.db_manager.is_connected:
                suggestions.append({
                    'text': '-- Connect to database to see column suggestions --',
                    'type': 'info',
                    'description': 'Database connection required for column names'
                })
            # If no columns found but database is connected, provide fallback suggestions
            elif not all_columns and self.db_manager.is_connected:
                # Common column name suggestions as fallback
                common_columns = ['id', 'name', 'email', 'created_at', 'updated_at', 'status', 'timestamp', 'user_id', 'date', 'time', 'count', 'value']
                for col in common_columns:
                    suggestions.append({
                        'text': col,
                        'type': 'common_column',
                        'description': f"Common column name: {col}"
                    })
            else:
                # Filter columns that match the current word
                for col_name in sorted(all_columns):
                    # Get source info for description
                    sources = table_sources[col_name]
                    if len(sources) == 1:
                        table, col_type = sources[0]
                        description = f"Column from {table} ({col_type})"
                    else:
                        tables_str = ', '.join([s[0] for s in sources[:3]])  # Show first 3 tables
                        if len(sources) > 3:
                            tables_str += f" (+{len(sources) - 3} more)"
                        description = f"Column from tables: {tables_str}"

                    suggestions.append({
                        'text': col_name,
                        'type': 'column',
                        'description': description
                    })

        elif context['context_type'] == 'table':
            # Suggest ALL table names from the database
            if self.db_manager.is_connected:
                try:
                    all_tables = self.db_manager.get_tables()
                    for table_name in sorted(all_tables):
                        # Get table metadata for better descriptions
                        try:
                            columns = self.get_table_columns(table_name)
                            column_count = len(columns)
                            description = f"Table: {table_name} ({column_count} columns)"
                        except:
                            description = f"Table: {table_name}"

                        suggestions.append({
                            'text': table_name,
                            'type': 'table', 
                            'description': description
                        })
                except Exception as e:
                    print(f"Error fetching tables: {e}")
                    # Fallback: suggest common table names
                    common_tables = ['users', 'orders', 'products', 'events', 'logs', 'analytics', 'metrics', 'sessions']
                    for table in common_tables:
                        suggestions.append({
                            'text': table,
                            'type': 'table',
                            'description': f"Common table name: {table}"
                        })
            else:
                # If not connected, suggest common table names and info message
                suggestions.append({
                    'text': '-- Connect to database to see table suggestions --',
                    'type': 'info',
                    'description': 'Database connection required for table names'
                })

                # Also provide common table name suggestions as fallback
                common_tables = ['users', 'orders', 'products', 'events', 'logs', 'analytics', 'metrics', 'sessions']
                for table in common_tables:
                    if not current_word or table.lower().startswith(current_word.lower()):
                        suggestions.append({
                            'text': table,
                            'type': 'table',
                            'description': f"Common table name: {table}"
                        })

        elif context['context_type'] == 'keyword':
            # Suggest SQL keywords
            for keyword in self.sql_keywords:
                keyword_lower = keyword.lower()
                if not current_word or keyword_lower.startswith(current_word):
                    suggestions.append({
                        'text': keyword,
                        'type': 'keyword',
                        'description': f"SQL keyword: {keyword}"
                    })

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
        """Clear the table columns cache."""
        self.table_columns_cache.clear()
