"""
AI智能优化建议模块
基于视频分析结果，调用DeepSeek API生成内容优化建议
"""

from openai import OpenAI
import pandas as pd
import os

# ── 配置API Key ──
DEEPSEEK_API_KEY = "你的DeepSeek_API_KEY粘贴到这里"
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)


def generate_advice(df: pd.DataFrame) -> str:
    # 1. 提取低效视频
    low_df = df[df['内容评级'].isin(['⚠️  待优化', '❌ 低效内容'])][
        ['视频名称', '认真观看率', '完播率', '质量得分']
    ].sort_values('质量得分').head(5)

    # 2. 提取优质视频
    top_df = df[df['内容评级'] == '🏆 优质内容'][
        ['视频名称', '认真观看率', '完播率', '质量得分']
    ].sort_values('质量得分', ascending=False).head(3)

    # 3. 整体统计
    avg_finish  = df['完播率'].mean()
    avg_serious = df['认真观看率'].mean()
    total       = len(df)

    # 4. 构建Prompt
    prompt = f"""
你是一名在线教育课程质量分析师。以下是一批课程视频的观看数据分析结果，请根据数据给出专业的优化建议。

【整体概况】
- 视频总数：{total} 个
- 平均完播率：{avg_finish:.1f}%
- 平均认真观看率：{avg_serious:.1f}%

【需要优化的视频（完播率和认真观看率偏低）】
{low_df.to_string(index=False)}

【表现优秀的视频（可作为参考标杆）】
{top_df.to_string(index=False)}

请从以下三个角度给出建议（每点2-3句话，语言简洁专业）：
1. 低效视频的可能原因分析
2. 针对低效视频的具体优化建议
3. 如何借鉴优质视频的经验复制到其他内容

请用中文回答。
"""

    # 5. 调用DeepSeek API
    print("\n🤖 正在调用DeepSeek AI生成优化建议，请稍候...")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "你是一名专业的在线教育课程质量分析师。"},
            {"role": "user",   "content": prompt}
        ],
        temperature=0.7,
        max_tokens=1000
    )
    return response.choices[0].message.content


def run_ai_advisor(report_path: str = "output_reports/video_analysis_report.xlsx"):
    if not os.path.exists(report_path):
        print(f"❌ 找不到分析报告：{report_path}")
        print("   请先运行 analyze.py 生成报告")
        return

    df = pd.read_excel(report_path, sheet_name='完整分析结果')
    print(f"✅ 读取报告成功，共 {len(df)} 条视频数据")

    advice = generate_advice(df)

    print("\n" + "="*50)
    print("📋 AI课程优化建议报告")
    print("="*50)
    print(advice)

    output_path = "output_reports/AI优化建议.txt"
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("AI课程优化建议报告\n")
        f.write("="*50 + "\n\n")
        f.write(advice)
    print(f"\n✅ 建议已保存至：{output_path}")


if __name__ == "__main__":
    run_ai_advisor()
