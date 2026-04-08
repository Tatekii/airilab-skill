# AiriLab Skill 快速入门

🎨 调用 AiriLab AI 图像生成平台，支持建筑/室内/景观/城市规划的 AI 渲染。

## 核心流程

```
登录鉴权 → 项目选择 → 图片上传 (可选) → 构建请求 → 提交任务 → 同步轮询 → 获取结果
```

**每一步都有前置条件，必须按顺序执行**。详细说明查看 `EXECUTION_FLOW.md`。

## 一、配置检查

运行配置检查脚本：
```bash
cd /home/ec2-user/.openclaw/skills/airilab
python3 scripts/check_config.py
```

## 二、快速使用

### 1. MJ 创意渲染（文生图）
```bash
python3 core/api.py --tool mj --prompt "现代建筑外观，玻璃幕墙，日落时分"
```

### 2. MJ 带参考图（最多 3 张）
```bash
python3 core/api.py --tool mj --prompt "基于参考图的室内设计" \
  --reference-image "https://example.com/image1.jpg"
```

### 3. 创意放大
```bash
python3 core/api.py --tool upscale --base-image "https://example.com/image.jpg"
```

### 4. 氛围转换
```bash
python3 core/api.py --tool atmosphere \
  --base-image "https://example.com/image.jpg" \
  --prompt "转换为夜晚氛围，暖色灯光"
```

## 三、触发关键词

当用户提到以下内容时，应该使用此技能：

- 「生成建筑效果图」「AI 绘图」「创意渲染」
- 「图片放大」「高清放大」「Upscale」
- 「氛围转换」「改变风格」「变成夜晚」
- 「MJ 渲染」「AI 出图」「快速渲染」
- 「生成室内设计图」「生成景观图」「生成城市设计图」

## 四、工作流说明

| 工作流 | 功能 | 必填参数 | 选填参数 |
|--------|------|----------|----------|
| MJ 创意渲染 | 文生图/图生图 | prompt | reference-image (≤3) |
| 创意放大 | 图片高清放大 | base-image | - |
| 氛围转换 | 改变图片氛围 | base-image, prompt | reference-image (≤1) |

## 五、输出示例

成功时返回：
```
✅ 图像生成完成！

生成了 4 张效果图：
1. https://airi-production.s3.cn-north-1.amazonaws.com.cn/...
2. https://airi-production.s3.cn-north-1.amazonaws.com.cn/...
3. https://airi-production.s3.cn-north-1.amazonaws.com.cn/...
4. https://airi-production.s3.cn-north-1.amazonaws.com.cn/...

任务 ID: xxx-xxx-xxx
```

## 六、常见问题

### Q: 提示需要认证？
A: 检查 `config/.env` 中的 `AIRILAB_API_KEY` 是否有效

### Q: 提示需要项目？
A: 检查 `config/project_config.json` 是否包含 teamId 和 projectId

### Q: 任务超时？
A: 任务通常 1-3 分钟完成，超时时间 10 分钟。如频繁超时请检查网络

### Q: 如何获取 API Token？
A: 登录 https://cn.airilab.com 获取

## 七、相关文件

- `SKILL.md` - 技能详细说明
- `SPEC.md` - 规格说明书
- `core/api.py` - 主 API 客户端
- `scripts/check_config.py` - 配置检查脚本

## 八、技术支持

- 官网：https://cn.airilab.com
- 文档：查看 SKILL.md 和 SPEC.md
