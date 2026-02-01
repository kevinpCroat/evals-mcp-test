# Code Review - Pull Request #142

## Issue 1: Hardcoded API Key
- **Severity**: CRITICAL
- **Location**: Line 15
- **Description**: API key is hardcoded directly in the source code
- **Impact**: If this code is committed to version control, the API key will be exposed to anyone with repository access, leading to potential security breaches
- **Suggestion**: Move the API key to environment variables or a secure configuration management system. Use `os.getenv('API_KEY')` instead

## Issue 2: SQL Injection in Authentication
- **Severity**: CRITICAL
- **Location**: Line 26
- **Description**: User input is directly interpolated into SQL query using f-string formatting
- **Impact**: An attacker could inject malicious SQL code (e.g., username "admin' OR '1'='1") to bypass authentication or access unauthorized data
- **Suggestion**: Use parameterized queries: `cursor.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))`

## Issue 3: Off-by-One Error
- **Severity**: HIGH
- **Location**: Line 49
- **Description**: Loop starts at index 1 instead of 0, skipping the first user in the results
- **Impact**: The first active user will always be omitted from the returned list, causing data loss
- **Suggestion**: Change `range(1, len(users))` to `range(len(users))` or better yet, use `for user in users:`

## Issue 4: Cursor Not Closed
- **Severity**: HIGH
- **Location**: Line 63
- **Description**: Database cursor is created but never closed after use
- **Impact**: Resource leak that can lead to connection pool exhaustion over time
- **Suggestion**: Add `cursor.close()` after the commit, or use a context manager

## Issue 5: SQL Injection in Search
- **Severity**: CRITICAL
- **Location**: Line 148
- **Description**: Search term is directly interpolated into SQL query without sanitization
- **Impact**: Attackers could inject SQL commands through the search functionality to access or modify unauthorized data
- **Suggestion**: Use parameterized queries with LIKE: `cursor.execute("SELECT * FROM users WHERE name LIKE ? OR email LIKE ?", (f'%{search_term}%', f'%{search_term}%'))`

## Issue 6: File Handle Not Closed
- **Severity**: HIGH
- **Location**: Line 84
- **Description**: File is opened but never explicitly closed
- **Impact**: File handle leak that could prevent other processes from accessing the file and consume system resources
- **Suggestion**: Use a context manager: `with open(filename, 'w') as file:` or add `file.close()` at the end

## Issue 7: Wrong Mathematical Operator
- **Severity**: HIGH
- **Location**: Line 99
- **Description**: Using addition instead of multiplication for base_score calculation
- **Impact**: Incorrect scoring algorithm that doesn't properly weight the components
- **Suggestion**: Based on the variable names and logic, should be `base_score = login_count * activity_days`

## Issue 8: Division by Zero
- **Severity**: MEDIUM
- **Location**: Line 102
- **Description**: No validation that login_count is not zero before division
- **Impact**: Will crash with ZeroDivisionError if a user has zero logins
- **Suggestion**: Add validation: `if login_count == 0: return 0` or use safe division

## Issue 9: Race Condition
- **Severity**: HIGH
- **Location**: Line 109
- **Description**: Multiple threads accessing shared cache dictionary without synchronization
- **Impact**: Concurrent access could lead to data corruption, lost updates, or inconsistent cache state
- **Suggestion**: Use threading.Lock() to protect cache access or use thread-safe data structures like queue.Queue

## Issue 10: Missing Null Check
- **Severity**: MEDIUM
- **Location**: Line 133
- **Description**: Attempting to access result[0] without checking if result is None
- **Impact**: Will raise TypeError or AttributeError if the user is not found in the database
- **Suggestion**: Add null check: `if result is None: raise ValueError("User not found")` or `return result[0].split(',') if result else []`

## Issue 11: Inefficient Batch Processing
- **Severity**: MEDIUM
- **Location**: Line 71
- **Description**: N+1 query problem - executing separate query for each user ID
- **Impact**: Poor performance when processing large batches, especially with network latency to database
- **Suggestion**: Use a single query with IN clause: `cursor.execute("SELECT * FROM users WHERE id IN ({})".format(','.join('?' * len(user_ids))), user_ids)`
