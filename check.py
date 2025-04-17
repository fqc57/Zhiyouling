import sqlite3

def check_cultural_tags():
    """
    查看cultural_tags表的结构和内容
    """
    try:
        # 连接到数据库
        conn = sqlite3.connect('travel_db.sqlite')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 获取表结构
        print("=== cultural_tags表结构 ===")
        cursor.execute("PRAGMA table_info(cultural_tags)")
        columns = cursor.fetchall()
        
        # 打印列信息
        print("列名\t\t类型\t\t可空\t\t默认值")
        print("-" * 60)
        for col in columns:
            print(f"{col['name']}\t\t{col['type']}\t\t{col['notnull'] == 0}\t\t{col['dflt_value']}")
        
        # 获取表内容
        print("\n=== cultural_tags表内容 ===")
        cursor.execute("SELECT * FROM cultural_tags LIMIT 10")  # 限制只显示前10条
        rows = cursor.fetchall()
        
        # 获取行数
        cursor.execute("SELECT COUNT(*) FROM cultural_tags")
        total_rows = cursor.fetchone()[0]
        print(f"总记录数: {total_rows}")
        
        # 如果有数据则显示
        if rows:
            # 打印列名
            headers = [column[0] for column in cursor.description]
            print("\t".join(headers))
            print("-" * 80)
            
            # 打印数据
            for row in rows:
                print("\t".join(str(value) for value in row))
        else:
            print("表中没有数据")
        
        # 检查是否有category列
        has_category = any(col['name'] == 'category' for col in columns)
        if has_category:
            print("\n表中有'category'列")
        else:
            print("\n表中没有'category'列")
            
        # 获取与pois表的关联情况
        print("\n=== 检查与pois表的关联 ===")
        cursor.execute("""
            SELECT t.tag, COUNT(t.tag) as count, p.category, p.category_type
            FROM cultural_tags t
            JOIN pois p ON t.poi_id = p.id
            GROUP BY t.tag
            ORDER BY count DESC
            LIMIT 10
        """)
        
        tag_stats = cursor.fetchall()
        if tag_stats:
            print("标签\t\t出现次数\t景点类别\t大类别")
            print("-" * 80)
            for stat in tag_stats:
                print(f"{stat[0]}\t\t{stat[1]}\t\t{stat[2]}\t\t{stat[3]}")
        else:
            print("没有关联数据")
            
    except Exception as e:
        print(f"查询数据库时出错: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭连接
        if conn:
            conn.close()

if __name__ == "__main__":
    check_cultural_tags()