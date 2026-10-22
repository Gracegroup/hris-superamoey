def sync_dataframe_to_db(table_name, df, conn):
    c = conn.cursor()
    # Get original IDs
    old_df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
    old_ids = set(old_df['id']) if 'id' in old_df.columns else set()
    new_ids = set(df['id']) if 'id' in df.columns else set()

    # Delete
    deleted_ids = old_ids - new_ids
    for did in deleted_ids:
        c.execute(f"DELETE FROM {table_name} WHERE id=?", (did,))

    # Insert / Update
    cols = [col for col in df.columns if col != 'id']
    for _, row in df.iterrows():
        if row['id'] not in old_ids or pd.isna(row['id']):
            # Insert
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            c.execute(f"INSERT INTO {table_name} ({col_names}) VALUES ({placeholders})", tuple(row[cols]))
        else:
            # Update
            set_clause = ", ".join([f"{col}=?" for col in cols])
            c.execute(f"UPDATE {table_name} SET {set_clause} WHERE id=?", tuple(row[cols]) + (row['id'],))
    conn.commit()
