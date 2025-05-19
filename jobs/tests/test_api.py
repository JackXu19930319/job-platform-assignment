import json
from datetime import date, timedelta
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from ninja_jwt.tokens import RefreshToken

from jobs.models import JobPosting


class JobPostingAPITest(TestCase):
    """
    測試職缺API的功能 / Test functionality of Job Posting API
    """
    
    def setUp(self):
        # 創建測試用戶 / Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword"
        )
        
        # 獲取測試用戶的JWT令牌 / Get JWT token for test user
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        
        # 測試日期 / Test dates
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)
        self.next_month = self.today + timedelta(days=30)
        
        # 創建測試職缺 / Create test job
        self.job = JobPosting.objects.create(
            title="Test Job",
            description="This is a test job posting",
            location="Taipei",
            salary_min=50000,
            salary_max=70000,
            company_name="Test Company",
            posting_date=self.yesterday,
            expiration_date=self.next_month,
        )
        self.job.required_skills = ["Python", "Django", "SQL"]
        self.job.save()
        
        # API URLs
        self.jobs_url = "/api/jobs/"
        self.job_detail_url = f"/api/jobs/{self.job.id}"
    
    def authenticate(self):
        """
        構建帶有認證的請求頭 / Construct headers with authentication
        """
        return {"HTTP_AUTHORIZATION": f"Bearer {self.access_token}"}
    
    def test_authentication_required(self):
        """
        測試未經認證時API拒絕訪問 / Test API refuses access without authentication
        """
        # 嘗試不帶token的請求 / Try request without token
        response = self.client.get(self.jobs_url)
        self.assertEqual(response.status_code, 401)
    
    def test_create_job_posting(self):
        """
        測試創建職缺帖子 / Test creating a job posting
        """
        new_job_data = {
            "title": "New Job",
            "description": "This is a new job",
            "location": "New Taipei",
            "salary_min": 40000,
            "salary_max": 60000,
            "company_name": "New Company",
            "posting_date": self.today.isoformat(),
            "expiration_date": self.next_month.isoformat(),
            "required_skills": ["Python", "FastAPI"]
        }
        
        # 發送POST請求 / Send POST request
        response = self.client.post(
            self.jobs_url,
            data=json.dumps(new_job_data),
            content_type="application/json",
            **self.authenticate()
        )
        
        # 檢查響應 / Check response
        self.assertEqual(response.status_code, 201)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["title"], "New Job")
        self.assertEqual(response_data["company_name"], "New Company")
        self.assertEqual(response_data["required_skills"], ["Python", "FastAPI"])
        
        # 確認數據庫中已創建 / Confirm created in database
        self.assertEqual(JobPosting.objects.count(), 2)
    
    def test_get_job_listings(self):
        """
        測試獲取職缺列表 / Test getting job listings
        """
        # 創建額外的測試職缺 / Create additional test jobs
        JobPosting.objects.create(
            title="Second Job",
            description="This is another job",
            location="Taichung",
            company_name="Second Company",
            posting_date=self.yesterday,
            expiration_date=self.next_month,
            _required_skills='["JavaScript", "React"]'
        )
        
        # 測試獲取所有職缺 / Test fetching all jobs
        response = self.client.get(
            self.jobs_url,
            **self.authenticate()
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 2)
        
        # 測試搜索功能 / Test search functionality
        response = self.client.get(
            f"{self.jobs_url}?search=Second",
            **self.authenticate()
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["company_name"], "Second Company")
        
        # 測試按地點過濾 / Test filter by location
        response = self.client.get(
            f"{self.jobs_url}?location=Taipei",
            **self.authenticate()
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["location"], "Taipei")
        
        # 測試分頁 / Test pagination
        response = self.client.get(
            f"{self.jobs_url}?limit=1&offset=0",
            **self.authenticate()
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
    
    def test_get_job_detail(self):
        """
        測試獲取單個職缺詳情 / Test getting a single job posting
        """
        response = self.client.get(
            self.job_detail_url,
            **self.authenticate()
        )
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["id"], self.job.id)
        self.assertEqual(response_data["title"], self.job.title)
        
        # 測試訪問不存在的職缺 / Test accessing non-existent job
        response = self.client.get(
            f"/api/jobs/9999",
            **self.authenticate()
        )
        self.assertEqual(response.status_code, 404)
    
    def test_update_job_posting(self):
        """
        測試更新職缺信息 / Test updating a job posting
        """
        update_data = {
            "title": "Updated Title",
            "description": "Updated description",
            "location": "Updated Location",
            "salary_min": 55000,
            "salary_max": 75000,
            "company_name": "Test Company",  # 保持公司名不變 / Keep company name unchanged
            "posting_date": self.today.isoformat(),
            "expiration_date": self.next_month.isoformat(),
            "required_skills": ["Python", "Django", "SQL", "FastAPI"]
        }
        
        response = self.client.put(
            self.job_detail_url,
            data=json.dumps(update_data),
            content_type="application/json",
            **self.authenticate()
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 驗證更新後的數據 / Verify updated data
        updated_job = JobPosting.objects.get(id=self.job.id)
        self.assertEqual(updated_job.title, "Updated Title")
        self.assertEqual(updated_job.location, "Updated Location")
        self.assertEqual(len(updated_job.required_skills), 4)
        
        # 嘗試更改公司名 / Try changing company name
        update_data["company_name"] = "New Company Name"
        response = self.client.put(
            self.job_detail_url,
            data=json.dumps(update_data),
            content_type="application/json",
            **self.authenticate()
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_delete_job_posting(self):
        """
        測試刪除職缺 / Test deleting a job posting
        """
        # 確認職缺存在 / Confirm job exists
        self.assertEqual(JobPosting.objects.filter(id=self.job.id).count(), 1)
        
        # 刪除職缺 / Delete job
        response = self.client.delete(
            self.job_detail_url,
            **self.authenticate()
        )
        
        self.assertEqual(response.status_code, 200)
        
        # 確認職缺已刪除 / Confirm job is deleted
        self.assertEqual(JobPosting.objects.filter(id=self.job.id).count(), 0)
        
        # 嘗試刪除不存在的職缺 / Try deleting non-existent job
        response = self.client.delete(
            self.job_detail_url,  # 该Job已被删除 / This job has been deleted
            **self.authenticate()
        )
        
        self.assertEqual(response.status_code, 404)
    
    def test_filter_by_status(self):
        """
        測試按狀態過濾職缺 / Test filtering jobs by status
        """
        # 創建一個預約職缺 / Create a scheduled job
        scheduled_job = JobPosting.objects.create(
            title="Scheduled Job",
            description="This job will be active in the future",
            location="Hsinchu",
            company_name="Future Company",
            posting_date=self.tomorrow,
            expiration_date=self.next_month,
            _required_skills='["Go", "Microservices"]'
        )
        
        # 創建一個過期職缺 / Create an expired job
        expired_job = JobPosting.objects.create(
            title="Expired Job",
            description="This job has expired",
            location="Taoyuan",
            company_name="Old Company",
            posting_date=self.yesterday - timedelta(days=30),
            expiration_date=self.yesterday,
            _required_skills='["PHP", "MySQL"]'
        )
        
        # 測試活躍職缺過濾 / Test active job filter
        response = self.client.get(
            f"{self.jobs_url}?status=active",
            **self.authenticate()
        )
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["title"], "Test Job")
        
        # 測試預約職缺過濾 / Test scheduled job filter
        response = self.client.get(
            f"{self.jobs_url}?status=scheduled",
            **self.authenticate()
        )
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["title"], "Scheduled Job")
        
        # 測試過期職缺過濾 / Test expired job filter
        response = self.client.get(
            f"{self.jobs_url}?status=expired",
            **self.authenticate()
        )
        response_data = json.loads(response.content)
        self.assertEqual(len(response_data), 1)
        self.assertEqual(response_data[0]["title"], "Expired Job") 