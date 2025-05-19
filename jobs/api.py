from datetime import date
from typing import List, Dict, Any
from django.db.models import Q
from django.http import Http404
from django.contrib.auth import authenticate
from ninja import Router, Query
from ninja.pagination import paginate
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.tokens import RefreshToken
from ninja_extra import status

from jobs.models import JobPosting
from jobs.schemas import (
    JobPostingIn, 
    JobPostingOut, 
    JobStatus, 
    JobFilterParams, 
    ErrorMessage, 
    SuccessMessage
)

# JWT 認證路由 / JWT Authentication router
auth_router = Router(tags=["auth"])

@auth_router.post("/token", response={200: Dict[str, Any], 401: ErrorMessage})
def login(request, username: str, password: str):
    """
    獲取JWT令牌 / Get JWT token
    
    使用用戶名和密碼來獲取訪問令牌和刷新令牌
    Use username and password to get access token and refresh token
    """
    user = authenticate(username=username, password=password)
    if user is None:
        return 401, {"detail": "Invalid credentials"}
    
    refresh = RefreshToken.for_user(user)
    
    return {
        "refresh": str(refresh),
        "access": str(refresh.access_token),
    }

@auth_router.post("/token/refresh", response={200: Dict[str, str], 401: ErrorMessage})
def refresh_token(request, refresh: str):
    """
    刷新訪問令牌 / Refresh access token
    
    使用刷新令牌獲取新的訪問令牌
    Use refresh token to get new access token
    """
    try:
        refresh_token = RefreshToken(refresh)
        return {
            "access": str(refresh_token.access_token),
        }
    except Exception as e:
        return 401, {"detail": str(e)}


# 創建API路由器，並設置認證 / Create API router with authentication
router = Router(tags=["jobs"])


@router.post("/", response={201: JobPostingOut, 400: ErrorMessage}, auth=JWTAuth())
def create_job_posting(request, job_data: JobPostingIn):
    """
    創建新的職缺貼文 / Create a new job posting
    
    支持預約上架功能（posting_date在未來日期） / Supports scheduled posting (future posting_date)
    """
    try:
        job = JobPosting(
            title=job_data.title,
            description=job_data.description,
            location=job_data.location,
            salary_min=job_data.salary_min,
            salary_max=job_data.salary_max,
            company_name=job_data.company_name,
            posting_date=job_data.posting_date,
            expiration_date=job_data.expiration_date,
        )
        job.required_skills = job_data.required_skills
        job.save()
        
        # 準備響應 / Prepare response
        response = JobPostingOut(
            id=job.id,
            title=job.title,
            description=job.description,
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            company_name=job.company_name,
            posting_date=job.posting_date,
            expiration_date=job.expiration_date,
            required_skills=job.required_skills,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
        return 201, response
    except Exception as e:
        return 400, {"detail": str(e)}


@router.get("/", response=List[JobPostingOut], auth=JWTAuth())
def list_job_postings(request, filters: JobFilterParams = Query(...)):
    """
    獲取所有職缺，支持搜索、篩選和排序 / Get all job postings with search, filter and sort
    
    查詢參數支持:
    - search: 搜索標題，描述和公司名
    - status: 按狀態過濾 (active/expired/scheduled)
    - location, company, skill: 過濾特定字段
    - sort_by, sort_desc: 排序控制
    - limit, offset: 分頁參數
    """
    # 基础查询 / Base query
    queryset = JobPosting.objects.all()
    
    # 文本搜索 / Text search
    if filters.search:
        queryset = queryset.filter(
            Q(title__icontains=filters.search) | 
            Q(description__icontains=filters.search) | 
            Q(company_name__icontains=filters.search)
        )
    
    # 按状态筛选 / Filter by status
    today = date.today()
    if filters.status == JobStatus.ACTIVE:
        queryset = queryset.filter(posting_date__lte=today, expiration_date__gte=today)
    elif filters.status == JobStatus.EXPIRED:
        queryset = queryset.filter(expiration_date__lt=today)
    elif filters.status == JobStatus.SCHEDULED:
        queryset = queryset.filter(posting_date__gt=today)
    
    # 按特定字段筛选 / Filter by specific fields
    if filters.location:
        queryset = queryset.filter(location__icontains=filters.location)
    if filters.company:
        queryset = queryset.filter(company_name__icontains=filters.company)
    if filters.skill:
        # 由于skill是存储为JSON的TextField，我们需要使用LIKE查询
        queryset = queryset.filter(_required_skills__icontains=filters.skill)
    
    # 排序 / Sort
    sort_field = filters.sort_by
    if sort_field not in ["posting_date", "expiration_date"]:
        sort_field = "posting_date"  # 默认排序字段
    
    if filters.sort_desc:
        sort_field = f"-{sort_field}"
    
    queryset = queryset.order_by(sort_field)
    
    # 分页 / Pagination
    results = queryset[filters.offset:filters.offset + filters.limit]
    
    # 格式化响应 / Format response
    response = []
    for job in results:
        response.append(
            JobPostingOut(
                id=job.id,
                title=job.title,
                description=job.description,
                location=job.location,
                salary_min=job.salary_min,
                salary_max=job.salary_max,
                company_name=job.company_name,
                posting_date=job.posting_date,
                expiration_date=job.expiration_date,
                required_skills=job.required_skills,
                created_at=job.created_at,
                updated_at=job.updated_at,
            )
        )
    
    return response


@router.get("/{job_id}", response={200: JobPostingOut, 404: ErrorMessage}, auth=JWTAuth())
def get_job_posting(request, job_id: int):
    """
    獲取單個職缺的詳細信息 / Get details of a specific job posting
    """
    try:
        job = JobPosting.objects.get(id=job_id)
        
        return JobPostingOut(
            id=job.id,
            title=job.title,
            description=job.description,
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            company_name=job.company_name,
            posting_date=job.posting_date,
            expiration_date=job.expiration_date,
            required_skills=job.required_skills,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
    except JobPosting.DoesNotExist:
        return 404, {"detail": "Job posting not found"}


@router.put("/{job_id}", response={200: JobPostingOut, 400: ErrorMessage, 404: ErrorMessage}, auth=JWTAuth())
def update_job_posting(request, job_id: int, job_data: JobPostingIn):
    """
    更新現有職缺 / Update an existing job posting
    
    不允許更改company_name字段 / company_name field cannot be changed
    """
    try:
        job = JobPosting.objects.get(id=job_id)
        
        # 检查公司名是否被更改 / Check if company name is changed
        if job_data.company_name != job.company_name:
            return 400, {"detail": "Company name cannot be changed"}
        
        # 更新字段 / Update fields
        job.title = job_data.title
        job.description = job_data.description
        job.location = job_data.location
        job.salary_min = job_data.salary_min
        job.salary_max = job_data.salary_max
        job.posting_date = job_data.posting_date
        job.expiration_date = job_data.expiration_date
        job.required_skills = job_data.required_skills
        
        job.save()
        
        return JobPostingOut(
            id=job.id,
            title=job.title,
            description=job.description,
            location=job.location,
            salary_min=job.salary_min,
            salary_max=job.salary_max,
            company_name=job.company_name,
            posting_date=job.posting_date,
            expiration_date=job.expiration_date,
            required_skills=job.required_skills,
            created_at=job.created_at,
            updated_at=job.updated_at,
        )
    except JobPosting.DoesNotExist:
        return 404, {"detail": "Job posting not found"}
    except Exception as e:
        return 400, {"detail": str(e)}


@router.delete("/{job_id}", response={200: SuccessMessage, 404: ErrorMessage}, auth=JWTAuth())
def delete_job_posting(request, job_id: int):
    """
    刪除職缺 / Delete a job posting
    """
    try:
        job = JobPosting.objects.get(id=job_id)
        job.delete()
        return {"message": "Job posting deleted successfully"}
    except JobPosting.DoesNotExist:
        return 404, {"detail": "Job posting not found"}
