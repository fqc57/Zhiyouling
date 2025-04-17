import pandas as pd
import os

def convert_excel_to_csv(excel_file, output_csv='data.csv', sheet_name=0):
    """
    将Excel文件转换为CSV格式

    参数:
    - excel_file: Excel文件路径
    - output_csv: 输出的CSV文件名，默认为data.csv
    - sheet_name: 要转换的工作表，默认为第一个工作表
    """
    try:
        # 读取Excel文件
        df = pd.read_excel(excel_file, sheet_name=sheet_name)

        # 清理列名，去除空白
        df.columns = df.columns.str.strip()

        # 处理可能的中文编码问题
        # 对于字符串列，去除两端空白
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].astype(str).str.strip()

        # 处理缺失值
        # 对于数值列，用0填充
        df[df.select_dtypes(include=['float64', 'int64']).columns] = \
            df.select_dtypes(include=['float64', 'int64']).fillna(0)

        # 对于字符串列，用空字符串填充
        df[df.select_dtypes(include=['object']).columns] = \
            df.select_dtypes(include=['object']).fillna('')

        # 创建新列的DataFrame
        new_columns = {}

        # 添加文化标签列（如果不存在）
        culture_columns = [col for col in df.columns if col.startswith('tag_')]
        if not culture_columns:
            if 'name' in df.columns:
                import jieba
                import jieba.analyse
                new_columns['tag_culture_1'] = df['name'].apply(
                    lambda x: ':'.join(
                        jieba.analyse.extract_tags(str(x), topK=1) + ['1.0']
                    )
                )
            else:
                # 将标量值转换为与df长度相同的列表
                new_columns['tag_culture_1'] = [''] * len(df)

        # 添加评论列（如果不存在）
        comment_columns = [col for col in df.columns if col.startswith('comment_')]
        if not comment_columns:
            if 'name' in df.columns:
                new_columns['评论内容'] = df['name'].apply(lambda x: f"这是{x}的默认评论，描述其特色和文化价值。")
            else:
                # 将标量值转换为与df长度相同的列表
                new_columns['评论内容'] = ["这是默认评论，描述其特色和文化价值。"] * len(df)

        # 确保必要的列存在，如果不存在则添加默认值
        required_columns = ['name', 'longitude', 'latitude']
        for col in required_columns:
            if col not in df.columns:
                if col in ['longitude', 'latitude']:
                    df[col] = 0  # 添加默认值为0
                else:
                    df[col] = ''  # 'name' 列默认值为空字符串

        # 添加情感分析、主题聚类、时间模式列，默认值为空字符串
        new_columns['情感分析'] = [''] * len(df)
        new_columns['主题聚类'] = [''] * len(df)
        new_columns['时间模式'] = [''] * len(df)

        # 合并新列
        new_df = pd.DataFrame(new_columns)
        df = pd.concat([df, new_df], axis=1)

        # 调整列顺序
        desired_columns = ['name', 'longitude', 'latitude', '评论内容', '情感分析', '主题聚类', '时间模式']
        other_columns = [col for col in df.columns if col not in desired_columns]
        final_columns = desired_columns + other_columns
        df = df[final_columns]

        # 保存为CSV
        df.to_csv(output_csv, index=False, encoding='utf-8-sig')

        print(f"成功将 {excel_file} 转换为 {output_csv}")
        print("转换后的文件信息:")
        print(f"总行数: {len(df)}")
        print(f"列名: {list(df.columns)}")

        return True

    except Exception as e:
        print(f"转换过程中出现错误: {e}")
        return False

# 使用示例
convert_excel_to_csv('data.xlsx', output_csv='new_data.csv')