"""
课程视频质量分析工具
用途：自动分析视频观看数据，识别高/低质量内容，生成可视化报告
作者：litterburger76
"""

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import os
import sys

# 解决中文显示问题
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
matplotlib.rcParams['axes.unicode_minus'] = False


# ==================== 1. 数据读取 ====================

def load_data(filepath):
    """读取Excel或CSV文件"""
    ext = os.path.splitext(filepath)[-1].lower()
    try:
        if ext in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        elif ext == '.csv':
            df = pd.read_csv(filepath, encoding='utf-8-sig')
        else:
            raise ValueError(f"不支持的文件格式：{ext}")
        print(f"✅ 成功读取数据，共 {len(df)} 条记录")
        return df
    except Exception as e:
        print(f"❌ 读取失败：{e}")
        sys.exit(1)


# ==================== 2. 数据清洗 ====================

def clean_data(df):
    """清洗数据：重命名列、处理缺失值、转换类型"""
    # 标准化列名（去除空格）
    df.columns = df.columns.str.strip()

    # 期望的列名
    expected_cols = ['视频id', '视频名称', '总观看次数', '认真观看次数', '完播次数', '认真观看率', '完播率']

    # 检查列是否存在
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        print(f"⚠️  警告：缺少以下列：{missing}")
        print(f"   当前列名：{list(df.columns)}")

    # 填充缺失值
    num_cols = ['总观看次数', '认真观看次数', '完播次数', '认真观看率', '完播率']
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

    # 如果率是小数形式(0~1)，转换为百分比
    for rate_col in ['认真观看率', '完播率']:
        if rate_col in df.columns and df[rate_col].max() <= 1.0:
            df[rate_col] = df[rate_col] * 100

    print(f"✅ 数据清洗完成，有效记录：{len(df)} 条")
    return df


# ==================== 3. 核心分析 ====================

def analyze(df):
    """计算综合质量得分，并打标签"""

    # 综合质量得分 = 认真观看率*0.4 + 完播率*0.4 + 观看量占比*0.2
    max_views = df['总观看次数'].max() if df['总观看次数'].max() > 0 else 1
    df['观看量占比'] = df['总观看次数'] / max_views * 100
    df['质量得分'] = (
        df['认真观看率'] * 0.4 +
        df['完播率'] * 0.4 +
        df['观看量占比'] * 0.2
    ).round(2)

    # 打分级标签
    def label(score):
        if score >= 70:
            return '🏆 优质内容'
        elif score >= 50:
            return '✅ 合格内容'
        elif score >= 30:
            return '⚠️  待优化'
        else:
            return '❌ 低效内容'

    df['内容评级'] = df['质量得分'].apply(label)

    # 统计摘要
    summary = {
        '总视频数': len(df),
        '平均认真观看率': f"{df['认真观看率'].mean():.1f}%",
        '平均完播率': f"{df['完播率'].mean():.1f}%",
        '优质内容数': len(df[df['内容评级'] == '🏆 优质内容']),
        '低效内容数': len(df[df['内容评级'] == '❌ 低效内容']),
    }

    return df, summary


# ==================== 4. 可视化 ====================

def visualize(df, output_dir):
    """生成3张分析图表"""
    os.makedirs(output_dir, exist_ok=True)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle('课程视频质量分析报告', fontsize=16, fontweight='bold', y=1.02)

    # --- 图1：认真观看率 vs 完播率 散点图 ---
    ax1 = axes[0]
    colors = {'🏆 优质内容': '#2ecc71', '✅ 合格内容': '#3498db',
              '⚠️  待优化': '#f39c12', '❌ 低效内容': '#e74c3c'}
    for label, group in df.groupby('内容评级'):
        ax1.scatter(group['认真观看率'], group['完播率'],
                    c=colors.get(label, 'gray'), label=label, alpha=0.8, s=80)
    ax1.set_xlabel('认真观看率 (%)')
    ax1.set_ylabel('完播率 (%)')
    ax1.set_title('观看质量分布')
    ax1.legend(fontsize=8)
    ax1.grid(True, alpha=0.3)

    # --- 图2：内容评级占比 饼图 ---
    ax2 = axes[1]
    rating_counts = df['内容评级'].value_counts()
    pie_colors = [colors.get(r, 'gray') for r in rating_counts.index]
    ax2.pie(rating_counts.values, labels=rating_counts.index,
            colors=pie_colors, autopct='%1.1f%%', startangle=90)
    ax2.set_title('内容评级分布')

    # --- 图3：Top10 质量得分 条形图 ---
    ax3 = axes[2]
    top10 = df.nlargest(10, '质量得分')[['视频名称', '质量得分']].copy()
    # 截断长名称
    top10['视频名称'] = top10['视频名称'].apply(lambda x: str(x)[:12] + '...' if len(str(x)) > 12 else str(x))
    bars = ax3.barh(top10['视频名称'], top10['质量得分'], color='#3498db', alpha=0.8)
    ax3.set_xlabel('质量得分')
    ax3.set_title('Top10 高质量视频')
    ax3.invert_yaxis()
    for bar, val in zip(bars, top10['质量得分']):
        ax3.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                 f'{val:.1f}', va='center', fontsize=8)

    plt.tight_layout()
    chart_path = os.path.join(output_dir, 'analysis_chart.png')
    plt.savefig(chart_path, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"✅ 图表已保存：{chart_path}")
    return chart_path


# ==================== 5. 导出报告 ====================

def export_report(df, summary, output_dir):
    """导出分析结果到Excel，含多个sheet"""
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, 'video_analysis_report.xlsx')

    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        # Sheet1：完整分析结果（按质量得分排序）
        result_df = df.sort_values('质量得分', ascending=False)
        result_df.to_excel(writer, sheet_name='完整分析结果', index=False)

        # Sheet2：优质内容清单
        top_df = df[df['内容评级'] == '🏆 优质内容'].sort_values('质量得分', ascending=False)
        top_df.to_excel(writer, sheet_name='优质内容清单', index=False)

        # Sheet3：待优化内容清单
        low_df = df[df['内容评级'].isin(['⚠️  待优化', '❌ 低效内容'])].sort_values('质量得分')
        low_df.to_excel(writer, sheet_name='待优化内容', index=False)

        # Sheet4：摘要统计
        summary_df = pd.DataFrame(list(summary.items()), columns=['指标', '数值'])
        summary_df.to_excel(writer, sheet_name='摘要统计', index=False)

    print(f"✅ 报告已导出：{output_path}")
    return output_path


# ==================== 6. 主程序 ====================

def main():
    print("=" * 50)
    print("   课程视频质量分析工具 v1.0")
    print("=" * 50)

    # 读取文件（支持命令行参数或手动输入）
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
    else:
        filepath = input("\n请输入数据文件路径（Excel或CSV）：").strip()

    output_dir = "output_reports"

    # 执行分析流程
    df = load_data(filepath)
    df = clean_data(df)
    df, summary = analyze(df)

    # 打印摘要
    print("\n📊 分析摘要：")
    for k, v in summary.items():
        print(f"   {k}：{v}")

    # 生成图表和报告
    visualize(df, output_dir)
    export_report(df, summary, output_dir)

    print("\n🎉 分析完成！结果保存在 output_reports/ 文件夹")
    print("=" * 50)


if __name__ == "__main__":
    main()
