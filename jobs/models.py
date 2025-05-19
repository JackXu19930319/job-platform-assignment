from django.db import models
import json

# Create your models here.

# 職缺貼文模型 / Job Posting Model
class JobPosting(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    location = models.CharField(max_length=255)
    salary_min = models.IntegerField(null=True, blank=True)
    salary_max = models.IntegerField(null=True, blank=True)
    company_name = models.CharField(max_length=255)
    posting_date = models.DateField()
    expiration_date = models.DateField()
    # 使用TextField來存儲JSON格式的技能列表 / Using TextField to store JSON formatted skills list
    _required_skills = models.TextField(db_column='required_skills', default='[]')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 创建一个序列化与反序列化的方法 / Create serialization and deserialization methods for skills
    @property
    def required_skills(self):
        return json.loads(self._required_skills)
    
    @required_skills.setter
    def required_skills(self, value):
        if isinstance(value, list):
            self._required_skills = json.dumps(value)
        else:
            raise ValueError("required_skills must be a list")
    
    def __str__(self):
        return f"{self.title} at {self.company_name}"
    
    # 判断职位状态的方法 / Methods to determine job status
    def is_active(self, current_date=None):
        """
        檢查職缺是否處於活躍狀態 / Check if the job posting is active
        
        當前日期介於 posting_date 和 expiration_date 之間時，職缺為活躍狀態
        A job is active when the current date is between posting_date and expiration_date
        """
        from datetime import date
        current_date = current_date or date.today()
        return self.posting_date <= current_date <= self.expiration_date
    
    def is_expired(self, current_date=None):
        """
        檢查職缺是否已過期 / Check if the job posting has expired
        
        當前日期大於 expiration_date 時，職缺已過期
        A job is expired when the current date is greater than expiration_date
        """
        from datetime import date
        current_date = current_date or date.today()
        return current_date > self.expiration_date
    
    def is_scheduled(self, current_date=None):
        """
        檢查職缺是否已排定但還未發佈 / Check if the job posting is scheduled but not yet published
        
        當前日期小於 posting_date 時，職缺為已排定狀態
        A job is scheduled when the current date is less than posting_date
        """
        from datetime import date
        current_date = current_date or date.today()
        return current_date < self.posting_date
