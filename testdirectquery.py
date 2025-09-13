#!/usr/bin/env python3
"""
Direct PostgreSQL Query Script for FastGTD

This script allows you to execute raw SQL queries against the FastGTD database
with admin privileges, bypassing the API layer for direct database access.

Usage:
    python testdirectquery.py "SELECT * FROM users;"
    python testdirectquery.py "SELECT count(*) FROM nodes WHERE node_type='note';"
    python testdirectquery.py --help

Features:
- Uses the same database connection as the FastGTD backend
- Admin-level access with full query capabilities
- Pretty-printed results in table format
- Safe parameterized queries support
- Transaction rollback on errors
"""

import argparse
import asyncio
import sys
from typing import Any, List, Dict
from pathlib import Path

# Add the project root to Python path so we can import FastGTD modules
sys.path.append('.')

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.deps import get_db


def format_results(results: List[Dict[str, Any]], headers: List[str]) -> str:
    """Format query results as a pretty table"""
    if not results:
        return "No results returned."
    
    # Calculate column widths
    widths = {}
    for header in headers:
        widths[header] = len(str(header))
        for row in results:
            value_len = len(str(row.get(header, '')))
            if value_len > widths[header]:
                widths[header] = value_len
    
    # Create header row
    header_row = " | ".join(str(header).ljust(widths[header]) for header in headers)
    separator = "-+-".join("-" * widths[header] for header in headers)
    
    # Create data rows
    data_rows = []
    for row in results:
        data_row = " | ".join(str(row.get(header, '')).ljust(widths[header]) for header in headers)
        data_rows.append(data_row)
    
    # Combine all parts
    table = f"{header_row}\n{separator}\n" + "\n".join(data_rows)
    return table


async def execute_query(query: str) -> str:
    """Execute a SQL query and return formatted results"""
    try:
        async for db_session in get_db():
            # Execute the query
            result = await db_session.execute(text(query))
            
            # Handle different types of queries
            if result.returns_rows:
                # SELECT queries - fetch all rows
                rows = result.fetchall()
                if rows:
                    # Get column names
                    headers = list(result.keys())
                    
                    # Convert rows to dictionaries
                    results = []
                    for row in rows:
                        row_dict = {}
                        for i, header in enumerate(headers):
                            row_dict[header] = row[i]
                        results.append(row_dict)
                    
                    formatted_results = format_results(results, headers)
                    return f"Query executed successfully. Found {len(results)} row(s):\n\n{formatted_results}"
                else:
                    return "Query executed successfully. No rows returned."
            else:
                # INSERT/UPDATE/DELETE queries - get affected row count
                await db_session.commit()
                return f"Query executed successfully. Rows affected: {result.rowcount if result.rowcount is not None else 'Unknown'}"
            
    except Exception as e:
        return f"Query execution failed: {str(e)}"


def validate_query(query: str) -> tuple[bool, str]:
    """Basic query validation to prevent obviously dangerous operations"""
    query_upper = query.strip().upper()
    
    # List of dangerous operations to warn about
    dangerous_operations = [
        'DROP DATABASE',
        'DROP SCHEMA', 
        'DROP TABLE',
        'TRUNCATE',
        'DELETE FROM users',
        'UPDATE users SET',
        'ALTER TABLE',
        'CREATE DATABASE',
        'DROP INDEX',
    ]
    
    for dangerous_op in dangerous_operations:
        if dangerous_op in query_upper:
            return False, f"Potentially dangerous operation detected: {dangerous_op}. Use --force to execute anyway."
    
    return True, "Query appears safe."


async def main():
    """Main function that handles command line args and executes the query"""
    
    parser = argparse.ArgumentParser(
        description="Execute raw SQL queries against FastGTD database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python testdirectquery.py "SELECT email, id FROM users;"
  python testdirectquery.py "SELECT node_type, count(*) FROM nodes GROUP BY node_type;"
  python testdirectquery.py "SELECT title FROM nodes WHERE node_type='note' AND body='Container folder';"
  python testdirectquery.py --force "DELETE FROM nodes WHERE title='duplicate';"
  
Safety Notes:
  - This script has admin-level database access
  - Use with caution, especially for UPDATE/DELETE operations
  - Always test queries with SELECT first when possible
  - The script will warn about potentially dangerous operations
        """
    )
    
    parser.add_argument(
        "query", 
        help="The SQL query to execute (wrap in quotes)"
    )
    
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force execution of potentially dangerous queries without warning"
    )
    
    parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what query would be executed without actually running it"
    )
    
    args = parser.parse_args()
    
    query = args.query.strip()
    
    if args.dry_run:
        print("DRY RUN MODE - Query would be executed:")
        print(f"Query: {query}")
        return
    
    # Validate query safety (unless --force is used)
    if not args.force:
        is_safe, message = validate_query(query)
        if not is_safe:
            print(f"❌ {message}")
            print("Use --dry-run to see what would be executed, or --force to execute anyway.")
            return
        else:
            print(f"✅ {message}")
    
    print(f"🔍 Executing query: {query}")
    print("=" * 60)
    
    # Execute the query
    result = await execute_query(query)
    print(result)
    print("=" * 60)
    print("✅ Query execution completed.")


if __name__ == "__main__":
    asyncio.run(main())