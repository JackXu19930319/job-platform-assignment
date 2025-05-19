from datetime import date, timedelta
from django.test import TestCase

from jobs.models import JobPosting

class JobPostingModelTest(TestCase):
    """
    測試JobPosting模型的基本功能 / Test basic functionality of JobPosting model
    """
    
    def setUp(self):
        # 創建測試職缺 / Create a test job posting
        self.today = date.today()
        self.yesterday = self.today - timedelta(days=1)
        self.tomorrow = self.today + timedelta(days=1)
        self.next_month = self.today + timedelta(days=30)
        self.last_month = self.today - timedelta(days=30)
        
        # 建立活躍職缺 / Create an active job
        self.active_job = JobPosting.objects.create(
            title="Active Job",
            description="This is an active job",
            location="Taipei",
            salary_min=50000,
            salary_max=70000,
            company_name="Test Company",
            posting_date=self.yesterday,
            expiration_date=self.next_month,
            _required_skills='["Python", "Django", "SQL"]'
        )
        
        # 建立過期職缺 / Create an expired job
        self.expired_job = JobPosting.objects.create(
            title="Expired Job",
            description="This is an expired job",
            location="Taichung",
            company_name="Test Company",
            posting_date=self.last_month,
            expiration_date=self.yesterday,
            _required_skills='["JavaScript", "React"]'
        )
        
        # 建立預約職缺 / Create a scheduled job
        self.scheduled_job = JobPosting.objects.create(
            title="Scheduled Job",
            description="This is a scheduled job",
            location="Kaohsiung",
            salary_min=60000,
            company_name="Future Company",
            posting_date=self.tomorrow,
            expiration_date=self.next_month,
            _required_skills='["Go", "Rust", "Docker"]'
        )
    
    def test_job_creation(self):
        """測試職缺能否正確創建 / Test if job posting can be correctly created"""
        self.assertEqual(self.active_job.title, "Active Job")
        self.assertEqual(self.active_job.company_name, "Test Company")
        
        # 測試 required_skills 屬性 / Test required_skills property
        self.assertEqual(self.active_job.required_skills, ["Python", "Django", "SQL"])
        self.assertEqual(len(self.active_job.required_skills), 3)
    
    def test_required_skills_property(self):
        """測試 required_skills 屬性的 getter 和 setter / Test getter and setter for required_skills property"""
        # 測試getter / Test getter
        self.assertEqual(self.scheduled_job.required_skills, ["Go", "Rust", "Docker"])
        
        # 測試setter / Test setter
        new_skills = ["Python", "Django", "REST API"]
        self.scheduled_job.required_skills = new_skills
        self.scheduled_job.save()
        
        # 重新從數據庫讀取 / Reload from database
        refreshed_job = JobPosting.objects.get(id=self.scheduled_job.id)
        self.assertEqual(refreshed_job.required_skills, new_skills)
    
    def test_job_status_methods(self):
        """測試職缺狀態判斷方法 / Test job status determination methods"""
        # 測試活躍狀態 / Test active status
        self.assertTrue(self.active_job.is_active())
        self.assertFalse(self.active_job.is_expired())
        self.assertFalse(self.active_job.is_scheduled())
        
        # 測試過期狀態 / Test expired status
        self.assertFalse(self.expired_job.is_active())
        self.assertTrue(self.expired_job.is_expired())
        self.assertFalse(self.expired_job.is_scheduled())
        
        # 測試預約狀態 / Test scheduled status
        self.assertFalse(self.scheduled_job.is_active())
        self.assertFalse(self.scheduled_job.is_expired())
        self.assertTrue(self.scheduled_job.is_scheduled())
    
    def test_string_representation(self):
        """測試字符串表示 / Test string representation"""
        self.assertEqual(str(self.active_job), "Active Job at Test Company")
    
    def test_custom_date_status(self):
        """測試使用自定義日期判斷狀態 / Test status with custom date"""
        # 預約職缺有效日期 / Scheduled job validity date
        future_date = self.tomorrow + timedelta(days=10)  # 處於有效期內的日期 / A date within the validity period
        
        # 在未來日期，活躍職缺會變成過期 / In future date, active job becomes expired
        self.assertFalse(self.active_job.is_active(future_date + timedelta(days=60)))
        self.assertTrue(self.active_job.is_expired(future_date + timedelta(days=60)))
        
        # 在未來日期，預約職缺會變成活躍 / In future date, scheduled job becomes active
        self.assertTrue(self.scheduled_job.is_active(future_date))
        self.assertFalse(self.scheduled_job.is_scheduled(future_date)) 