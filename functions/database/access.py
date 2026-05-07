"""Microsoft Access database operations for BISSI.

Provides read/write access to .mdb and .accdb files via pyodbc.
"""
import pyodbc
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import json


def get_access_driver() -> str:
    """Find available Access ODBC driver."""
    drivers = [d for d in pyodbc.drivers() if 'Microsoft Access' in d]
    if drivers:
        return drivers[0]  # Use first available
    raise RuntimeError("No Microsoft Access ODBC driver found. Install Microsoft Access Runtime.")


class AccessDatabase:
    """Microsoft Access database handler."""
    
    def __init__(self, db_path: Union[str, Path]):
        """Initialize Access database connection.
        
        Args:
            db_path: Path to .mdb or .accdb file
        """
        self.db_path = Path(db_path)
        self.conn = None
        self.driver = None
        self._connect()
    
    def _connect(self):
        """Establish database connection."""
        self.driver = get_access_driver()
        
        conn_str = (
            f"DRIVER={{{self.driver}}};"
            f"DBQ={self.db_path.absolute()};"
            f"PWD=;"
        )
        
        self.conn = pyodbc.connect(conn_str, autocommit=True)
    
    def list_tables(self) -> List[str]:
        """List all tables in database."""
        cursor = self.conn.cursor()
        tables = [row.table_name for row in cursor.tables(tableType='TABLE')]
        cursor.close()
        return tables
    
    def list_queries(self) -> List[str]:
        """List all queries in database."""
        cursor = self.conn.cursor()
        queries = [row.table_name for row in cursor.tables(tableType='VIEW')]
        cursor.close()
        return queries
    
    def read_table(self, table_name: str) -> pd.DataFrame:
        """Read entire table into DataFrame.
        
        Args:
            table_name: Name of table to read
            
        Returns:
            DataFrame with table data
        """
        query = f"SELECT * FROM [{table_name}]"
        return pd.read_sql(query, self.conn)
    
    def execute_query(self, sql: str) -> pd.DataFrame:
        """Execute SQL query.
        
        Args:
            sql: SQL query string
            
        Returns:
            DataFrame with results
        """
        return pd.read_sql(sql, self.conn)
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table column information.
        
        Args:
            table_name: Name of table
            
        Returns:
            List of column definitions
        """
        cursor = self.conn.cursor()
        columns = []
        
        for row in cursor.columns(table=table_name):
            columns.append({
                'name': row.column_name,
                'type': row.type_name,
                'nullable': row.is_nullable == 'YES',
                'default': row.column_def
            })
        
        cursor.close()
        return columns
    
    def insert_record(self, table_name: str, data: Dict[str, Any]) -> bool:
        """Insert single record into table.
        
        Args:
            table_name: Target table
            data: Dictionary mapping column names to values
            
        Returns:
            True if successful
        """
        columns = ', '.join([f"[{c}]" for c in data.keys()])
        placeholders = ', '.join(['?' for _ in data])
        
        sql = f"INSERT INTO [{table_name}] ({columns}) VALUES ({placeholders})"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(data.values()))
            cursor.close()
            return True
        except Exception as e:
            print(f"Insert error: {e}")
            return False
    
    def update_record(self, 
                      table_name: str,
                      data: Dict[str, Any],
                      where_clause: str,
                      where_params: tuple) -> bool:
        """Update records in table.
        
        Args:
            table_name: Target table
            data: Dictionary of columns to update
            where_clause: WHERE condition
            where_params: Parameters for WHERE clause
            
        Returns:
            True if successful
        """
        set_clause = ', '.join([f"[{c}] = ?" for c in data.keys()])
        sql = f"UPDATE [{table_name}] SET {set_clause} WHERE {where_clause}"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, tuple(data.values()) + where_params)
            cursor.close()
            return True
        except Exception as e:
            print(f"Update error: {e}")
            return False
    
    def delete_record(self, 
                      table_name: str,
                      where_clause: str,
                      where_params: tuple) -> bool:
        """Delete records from table.
        
        Args:
            table_name: Target table
            where_clause: WHERE condition
            where_params: Parameters for WHERE clause
            
        Returns:
            True if successful
        """
        sql = f"DELETE FROM [{table_name}] WHERE {where_clause}"
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, where_params)
            cursor.close()
            return True
        except Exception as e:
            print(f"Delete error: {e}")
            return False
    
    def export_to_excel(self, table_name: str, output_path: str) -> bool:
        """Export table to Excel file.
        
        Args:
            table_name: Table to export
            output_path: Output Excel file path
            
        Returns:
            True if successful
        """
        try:
            df = self.read_table(table_name)
            df.to_excel(output_path, index=False, sheet_name=table_name)
            return True
        except Exception as e:
            print(f"Export error: {e}")
            return False
    
    def import_from_dataframe(self, 
                              table_name: str,
                              df: pd.DataFrame,
                              if_exists: str = 'append') -> bool:
        """Import DataFrame into table.
        
        Args:
            table_name: Target table
            df: DataFrame to import
            if_exists: 'append' or 'replace'
            
        Returns:
            True if successful
        """
        try:
            if if_exists == 'replace':
                # Clear existing data
                cursor = self.conn.cursor()
                cursor.execute(f"DELETE FROM [{table_name}]")
                cursor.close()
            
            # Insert rows
            for _, row in df.iterrows():
                data = row.to_dict()
                self.insert_record(table_name, data)
            
            return True
        except Exception as e:
            print(f"Import error: {e}")
            return False
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def read_access_table(db_path: Union[str, Path], table_name: str) -> pd.DataFrame:
    """Convenience function to read Access table.
    
    Args:
        db_path: Path to database file
        table_name: Table to read
        
    Returns:
        DataFrame with data
    """
    with AccessDatabase(db_path) as db:
        return db.read_table(table_name)


def list_access_tables(db_path: Union[str, Path]) -> List[str]:
    """List all tables in Access database.
    
    Args:
        db_path: Path to database file
        
    Returns:
        List of table names
    """
    with AccessDatabase(db_path) as db:
        return db.list_tables()


def export_access_to_json(db_path: Union[str, Path], 
                          output_path: str,
                          tables: Optional[List[str]] = None) -> None:
    """Export entire database or specific tables to JSON.
    
    Args:
        db_path: Path to database file
        output_path: Output JSON file
        tables: Specific tables to export, or all if None
    """
    with AccessDatabase(db_path) as db:
        if tables is None:
            tables = db.list_tables()
        
        data = {}
        for table in tables:
            df = db.read_table(table)
            data[table] = df.to_dict('records')
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)
