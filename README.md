# 工作職缺平台 API / Job Platform API

一個基於Django和Django Ninja的工作職缺發布平台後端API。

## 技術棧 / Tech Stack

* Python 3.10+
* Django 5.x
* Django Ninja (API框架)
* Django Ninja JWT (認證)
* SQLite (資料庫)
* pytest (測試框架)

## 安裝 / Installation

1. 創建虛擬環境 / Create virtual environment
```bash
python -m venv .venv
source .venv/bin/activate  # Unix/macOS
# 或者 / OR
.venv\Scripts\activate  # Windows
```

2. 安裝依賴包 / Install dependencies
```bash
pip install -r requirements.txt
```

3. 進行資料庫遷移 / Run migrations
```bash
python manage.py migrate
```

4. 創建超級用戶 / Create superuser
```bash
python manage.py createsuperuser
```

## 運行 / Running

啟動開發服務器：
```bash
python manage.py runserver
```

訪問 API 文檔： http://localhost:8000/api/docs

## API 端點 / API Endpoints

### 認證 / Authentication

* `POST /api/auth/token/pair/` - 獲取訪問和刷新令牌
* `POST /api/auth/token/refresh/` - 刷新訪問令牌

### 職缺 / Job Postings

所有職缺相關的端點需要 JWT 認證。在請求頭中添加：
`Authorization: Bearer <your_access_token>`

* `POST /api/jobs/` - 創建新職缺
* `GET /api/jobs/` - 獲取職缺列表 (支持搜索和過濾)
* `GET /api/jobs/{id}/` - 獲取單個職缺詳細信息
* `PUT /api/jobs/{id}/` - 更新職缺
* `DELETE /api/jobs/{id}/` - 刪除職缺

## 示例請求 / Example Requests

### 獲取訪問令牌 / Get Access Token

```bash
curl -X POST http://localhost:8000/api/auth/token/pair/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'
```

### 創建職缺 / Create Job

```bash
curl -X POST http://localhost:8000/api/jobs/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -d '{
    "title": "Senior Python Developer",
    "description": "We are looking for a senior Python developer...",
    "location": "Taipei",
    "salary_min": 70000,
    "salary_max": 100000,
    "company_name": "Tech Solutions Ltd",
    "posting_date": "2023-06-01",
    "expiration_date": "2023-07-01",
    "required_skills": ["Python", "Django", "REST API", "SQL"]
  }'
```

## 搜索和過濾 / Search and Filtering

可用的過濾參數:
* `search` - 搜索職缺標題、描述和公司名
* `status` - 按狀態過濾 (`active`, `expired`, `scheduled`)
* `location` - 按地點過濾
* `company` - 按公司過濾
* `skill` - 按技能過濾
* `sort_by` - 排序字段 (`posting_date`, `expiration_date`)
* `sort_desc` - 降序排序 (true/false)
* `limit` - 每頁結果數量
* `offset` - 分頁偏移量

示例:
```
/api/jobs/?status=active&location=Taipei&limit=10&offset=0
```

## 測試 / Testing

運行測試:
```bash
pytest
```

## License

MIT 