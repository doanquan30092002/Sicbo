# Telegram Notification Rules - Sicbo Project

## Khi nào BẮT BUỘC báo Telegram

Sau khi hoàn thành bất kỳ task nào thuộc các loại sau, PHẢI gọi MCP tool `telegram_report_done`:

- Implement xong 1 use case mới
- Implement xong 1 API router mới
- Implement xong 1 Telegram bot handler/conversation
- Fix xong bug quan trọng
- Tạo xong migration
- Chạy tests và có kết quả
- Hoàn thành 1 Phase

## Cách dùng MCP

```
Tool: telegram_report_done
Arguments:
  task_name: "Tên task ngắn gọn"
  result: "Tóm tắt kết quả — số file tạo/sửa, tests pass/fail, ghi chú quan trọng"
  files_changed: ["path/to/file1.py", "path/to/file2.py"]  # optional
```

## Khi nào báo START

Khi bắt đầu task lớn (> 15 phút), dùng `telegram_send_task`:

```
Tool: telegram_send_task
Arguments:
  task_name: "Tên task"
  description: "Sẽ làm gì"
  estimated_time: "30 phút"
```

## Stop Hook (tự động)

Claude Code tự động chạy `mcp_servers/notify_stop.py` sau mỗi lượt kết thúc.
Hook này là fallback — đừng dựa vào nó làm báo cáo chi tiết, dùng MCP tool trước.

## KHÔNG cần báo khi

- Đọc file để research
- Sửa typo nhỏ
- Trả lời câu hỏi đơn giản
- Viết dưới 20 dòng code
