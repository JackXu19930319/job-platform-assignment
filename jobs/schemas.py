from typing import List, Optional
from datetime import date, datetime
from ninja import Schema, Field
from enum import Enum


class JobStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"


class JobPostingIn(Schema):
    """
    職缺建立/更新的輸入結構 / Input schema for job posting creation/update
    """
    title: str
    description: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    company_name: str
    posting_date: date
    expiration_date: date
    required_skills: List[str]


class JobPostingOut(Schema):
    """
    職缺資訊的輸出結構 / Output schema for job posting
    """
    id: int
    title: str
    description: str
    location: str
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    company_name: str
    posting_date: date
    expiration_date: date
    required_skills: List[str]
    created_at: datetime
    updated_at: datetime
    
    # 計算職缺狀態 / Calculate job status
    @property
    def status(self) -> JobStatus:
        today = date.today()
        if today < self.posting_date:
            return JobStatus.SCHEDULED
        elif today > self.expiration_date:
            return JobStatus.EXPIRED
        else:
            return JobStatus.ACTIVE


class JobFilterParams(Schema):
    """
    職缺搜尋與過濾參數 / Search and filter parameters for job postings
    """
    search: Optional[str] = None  # 搜索标题、描述和公司名
    status: Optional[JobStatus] = None  # 按状态筛选
    location: Optional[str] = None  # 按地点筛选
    company: Optional[str] = None  # 按公司筛选
    skill: Optional[str] = None  # 按技能筛选
    sort_by: Optional[str] = "posting_date"  # 排序字段
    sort_desc: bool = False  # 是否降序排序
    limit: int = 10  # 每页数量
    offset: int = 0  # 分页偏移量


class ErrorMessage(Schema):
    """
    錯誤響應結構 / Error response schema
    """
    detail: str


class SuccessMessage(Schema):
    """
    成功響應結構 / Success response schema
    """
    message: str
