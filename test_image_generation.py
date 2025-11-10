#!/usr/bin/env python3
"""测试伪纪实风格图片生成"""

import sys
sys.path.insert(0, '/Users/siqi/Documents/PolyU/Sem1/SD5913/FinalCode')

from ai_engine import generate_evidence_image

print("=" * 60)
print("测试伪纪实风格图片生成")
print("=" * 60)

# 测试不同类型的故事
test_cases = [
    {
        "title": "深夜地铁的第13节车厢",
        "content": "凌晨地铁出现不存在的车厢..."
    },
    {
        "title": "出租屋镜子里的室友",
        "content": "浴室镜子里出现神秘人影..."
    },
    {
        "title": "凌晨三点的敲门声",
        "content": "门外出现悬空的腿和血手印..."
    }
]

for i, test in enumerate(test_cases, 1):
    print(f"\n[{i}/{len(test_cases)}] 生成图片: {test['title']}")
    print("-" * 60)
    
    filepath = generate_evidence_image(test['title'], test['content'])
    
    if filepath:
        print(f"✅ 图片已生成: {filepath}")
    else:
        print("❌ 图片生成失败")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
print("\n💡 生成的图片保存在: static/generated/")
print("   访问 http://127.0.0.1:5001/generated/ 查看")
