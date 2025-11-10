# ✅ 初始数据和分页功能更新完成

## 🎯 更新内容

### 1. 新的初始故事（3个）

**故事 1: 深夜地铁的第13节车厢**
- 分类：地铁怪谈 (subway_ghost)
- 地点：地铁2号线
- 角色：偏执记录者 (paranoid_reporter)
- 内容：凌晨地铁出现不存在的13号车厢，时间显示异常，镜中倒影表情诡异

**故事 2: 出租屋镜子里的"室友"**
- 分类：诅咒物品 (cursed_object)
- 地点：老城区单身公寓
- 角色：惊恐目击者 (scared_witness)
- 内容：浴室镜子里出现神秘人影，对着主角微笑并说话

**故事 3: 凌晨三点的敲门声**
- 分类：公寓迷案 (apartment_mystery)
- 地点：某住宅小区
- 角色：调查者 (investigator)
- 内容：7楼住户每天凌晨3点被敲门，门外出现悬空的腿和血手印

### 2. 分页功能

**后端改动 (app.py)**:
- ✅ 添加 `init_default_stories()` 函数，首次运行时自动创建3个故事
- ✅ 修改 `/api/stories` API，支持分页参数
  - `page`: 页码（默认 1）
  - `per_page`: 每页数量（默认 8）
- ✅ 返回分页信息：
  ```json
  {
    "stories": [...],
    "pagination": {
      "page": 1,
      "per_page": 8,
      "total": 15,
      "pages": 2,
      "has_prev": false,
      "has_next": true,
      "prev_page": null,
      "next_page": 2
    }
  }
  ```

**前端改动 (static/app.js)**:
- ✅ 添加分页状态变量：`currentPage`, `totalPages`, `pagination`
- ✅ 修改 `loadStories()` 支持页码参数
- ✅ 新增 `renderPagination()` 函数渲染分页控件
- ✅ 新增 `changePage()` 函数处理翻页

**界面改动 (index.html)**:
- ✅ 添加 `<div id="pagination-container">` 分页容器
- ✅ 添加 `.pagination` CSS 样式

## 📊 分页逻辑

```
第1页: 故事 1-8
第2页: 故事 9-16
第3页: 故事 17-24
...
```

- 每页显示 **8 个故事**
- 超过 8 个故事自动分页
- 翻页按钮：◀ 上一页 | 第 X / Y 页 | 下一页 ▶
- 首页禁用"上一页"，末页禁用"下一页"
- 翻页后自动滚动到顶部

## 🧪 如何测试

### 测试初始数据

1. **删除旧数据库**（可选）:
   ```bash
   rm instance/urban_legends.db
   ```

2. **重启应用**:
   ```bash
   lsof -ti:5001 | xargs kill -9 2>/dev/null
   .venv/bin/python app.py
   ```

3. **查看日志**，应该看到:
   ```
   📝 创建默认故事...
   ✅ 默认故事创建完成
   ```

4. **访问** http://127.0.0.1:5001
   - 应该看到3个新格式的故事
   - 标题、内容、分类都是新的

### 测试分页功能

1. **手动生成更多故事**（生成10+个故事）:
   ```bash
   for i in {1..10}; do
     .venv/bin/python manual_generate_story.py
     sleep 2
   done
   ```

2. **刷新页面**，应该看到:
   - 第一页显示最新的 8 个故事
   - 底部出现分页控件
   - 显示 "第 1 / 2 页"（假设有16个故事）

3. **点击"下一页"**:
   - 跳转到第 2 页
   - 显示第 9-16 个故事
   - "上一页"按钮激活
   - 页面自动滚动到顶部

4. **点击"上一页"**:
   - 返回第 1 页
   - "下一页"按钮激活

## 🎨 分页样式

```css
.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 10px;
    gap: 10px;
}

.pagination button {
    min-width: 80px;
}
```

- Mac OS 3 风格按钮
- 禁用按钮半透明（opacity: 0.5）
- 按钮之间间隔 10px
- 页码信息紫色加粗显示

## 📝 API 使用示例

### 获取第1页（默认）
```bash
curl http://127.0.0.1:5001/api/stories
```

### 获取第2页
```bash
curl http://127.0.0.1:5001/api/stories?page=2
```

### 每页显示5个
```bash
curl http://127.0.0.1:5001/api/stories?per_page=5
```

## ✅ 完成状态

- [x] 创建3个新格式的初始故事
- [x] 故事内容更加详细和吸引人
- [x] 后端支持分页查询
- [x] 前端显示分页控件
- [x] 翻页功能正常工作
- [x] 每页8个故事
- [x] 第一页禁用"上一页"
- [x] 最后一页禁用"下一页"
- [x] 翻页后滚动到顶部

## 🚀 现在可以测试了！

访问 http://127.0.0.1:5001 查看新的初始故事和分页功能。
