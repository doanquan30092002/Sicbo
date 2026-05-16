---
name: architecture-decisions
description: Các quyết định kiến trúc quan trọng của dự án Sicbo
type: project
---

# Architecture Decisions - Sicbo

## 1. Clean Architecture (Backend)

**Quyết định:** 4-layer Clean Architecture (domain → application → infrastructure → interfaces)
**Lý do:** Hỗ trợ mở rộng game mới (Bầu Cua, Đua Vịt...) mà không sửa core code
**Ảnh hưởng:** Dependency chỉ đi 1 chiều vào trong; infrastructure implement interfaces của domain

## 2. Game Plugin System

**Quyết định:** `AbstractGame` + `GameRegistry` ở domain layer
**Lý do:** User muốn thêm Bầu Cua, Đua Vịt, Đua Ngựa sau này
**Cách thêm:** Implement `AbstractGame`, register vào `GameRegistry`, set `is_active=True`

## 3. Cutoff Time: 18:10

**Quyết định:** Cutoff tại 18:10 (không phải 18:25 như plan ban đầu)
**Lý do:** User yêu cầu cụ thể
**Enforce:** Server-side trong `PlaceBet.execute()`, không tin client

## 4. all_last2 là LIST (không phải SET)

**Quyết định:** `parsed_data["all_last2"]` là Python list có duplicate
**Lý do:** Nếu số "23" xuất hiện 3 lần trong các giải XSMB, người chơi Lô thắng 3×75×stake
**Quan trọng:** Xiên dùng `set(all_last2)` để check, Lô dùng `sum(1 for n in all_last2 if n == number)`

## 5. Single Process trên Railway

**Quyết định:** FastAPI + APScheduler + Telegram Bot trong cùng 1 uvicorn process
**Lý do:** Railway free tier $5/tháng, không đủ cho 2 services
**Cách triển khai:** APScheduler dùng `AsyncIOScheduler`, bot dùng `asyncio.create_task` trong lifespan

## 6. SePay Free cho Payment

**Quyết định:** SePay free tier (không phải MoMo/ZaloPay API trực tiếp)
**Lý do:** SePay free support webhook cho cả bank và MoMo, không cần API key trả tiền
**Flow:** User CK với `transfer_content` code → SePay gọi webhook → auto confirm

## 7. Supabase PostgreSQL

**Quyết định:** Supabase (500MB free) thay vì Railway PostgreSQL
**Lý do:** Railway PostgreSQL hết free tier riêng; Supabase có 500MB + Row Level Security
**Connection:** `postgresql+asyncpg://...supabase...` với async SQLAlchemy
