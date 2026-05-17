# Sicbo — Hướng dẫn sử dụng

Chào mừng bạn đến với **Sicbo**! Tài liệu này hướng dẫn từng bước cách:
- Đăng ký tài khoản
- Nạp tiền vào ví
- Đặt cược qua **Telegram Bot**
- Theo dõi kết quả & rút tiền

---

## 📑 Mục lục

1. [Đăng ký tài khoản](#1-đăng-ký-tài-khoản)
2. [Liên kết Telegram](#2-liên-kết-telegram-bot)
3. [Nạp tiền](#3-nạp-tiền)
4. [Đặt cược qua Telegram](#4-đặt-cược-qua-telegram-bot-quan-trọng)
5. [Theo dõi kết quả](#5-xem-kết-quả--lịch-sử)
6. [Rút tiền](#6-rút-tiền)
7. [Bảng tỷ lệ cược](#7-bảng-tỷ-lệ-cược)
8. [FAQ](#8-faq)

---

## 1. Đăng ký tài khoản

1. Mở https://sicbo-eosin.vercel.app
2. Click **Đăng ký** ở góc phải
3. Điền:
   - **Tên đăng nhập** (3-20 ký tự)
   - **Mật khẩu** (tối thiểu 6 ký tự)
   - (tuỳ chọn) số điện thoại, email
4. Click **Đăng ký** → tự động đăng nhập
5. Bạn sẽ thấy header hiển thị balance `0₫`

---

## 2. Liên kết Telegram Bot

Để đặt cược qua Telegram, bạn cần liên kết tài khoản web với Telegram của mình.

### Bước 1: Tạo mã liên kết trên web

1. Đăng nhập vào https://sicbo-eosin.vercel.app
2. Click vào tên username (góc phải) → **Tài khoản** (hoặc vào `/profile`)
3. Section **Liên kết Telegram** → click **Tạo token liên kết**
4. Sao chép **mã 6 số** hiện ra (vd: `483921`)
   - ⚠️ Token có hiệu lực 15 phút

### Bước 2: Liên kết qua bot

1. Mở Telegram → tìm bot **Sicbo Bot** (`@Sicbo_By_Quan_Bot`) hoặc click link: https://t.me/Sicbo_By_Quan_Bot
2. Nhấn **Start** hoặc gõ `/start`
3. Gõ lệnh:
   ```
   /link 483921
   ```
   (thay `483921` bằng mã của bạn)
4. Bot phản hồi:
   ```
   ✅ Liên kết thành công!
   👤 Tài khoản: your_username
   💰 Số dư: 0 ₫
   ```

Từ giờ bạn có thể đặt cược qua bot.

---

## 3. Nạp tiền

### Cách 1: Qua website (recommend)

1. Vào https://sicbo-eosin.vercel.app/wallet
2. Click **Nạp tiền** → nhập số tiền (vd: `100,000`)
3. Chọn phương thức: **Bank Transfer** (BIDV) hoặc **MoMo**
4. Hệ thống hiện:
   - **QR code** (quét bằng app ngân hàng)
   - **Số tài khoản:** `0915098027`
   - **Tên chủ TK:** DOAN DUC QUAN
   - **Ngân hàng:** BIDV
   - **Nội dung chuyển khoản:** `NAP00xxxx` (mã 8 ký tự)

5. Mở app **BIDV SmartBanking** trên điện thoại:
   - **Quét QR** → app tự điền số tiền + nội dung
   - **Hoặc nhập tay:** số TK + chính xác nội dung `NAP00xxxx`
6. Xác nhận chuyển khoản

### Cách 2: Qua Telegram

1. Trong bot, gõ:
   ```
   /deposit
   ```
2. Bot hiện thông tin bank account + QR
3. Làm theo bước 5-6 ở trên

### Sau khi chuyển khoản

- **Nếu SePay auto-credit đã active:** balance tăng tự động sau ~10-30 giây
- **Nếu chưa active (giai đoạn đầu):** gửi ảnh biên lai cho **admin Telegram** → admin xác nhận thủ công → balance tăng + bot gửi thông báo

---

## 4. Đặt cược qua Telegram Bot (QUAN TRỌNG)

Đây là **cách nhanh nhất** để đặt cược. Bot chạy 24/7 trên Telegram.

### Bước 1: Mở chat với bot

Mở Telegram, vào chat với bot Sicbo (đã liên kết ở mục 2).

### Bước 2: Gõ lệnh `/bet`

Bot sẽ dẫn bạn qua **5 bước interactive**:

#### Bước 2.1 — Chọn trò chơi
Bot hiện danh sách game đang mở:
```
🎲 ĐẶT CƯỢC
💰 Số dư: 100,000 ₫

Chọn trò chơi:
[ XSMB Số Đề ]
[ ❌ Huỷ ]
```
→ Bấm **XSMB Số Đề**

#### Bước 2.2 — Chọn loại cược
Bot hiện 4 loại cược:
```
🎲 XSMB Số Đề
Chọn loại cược:
[ Lô (1:75) ]
[ Đề (1:75) ]
[ Lô Xiên 2 (1:10) ]
[ Lô Xiên 3 (1:40) ]
[ ❌ Huỷ ]
```
→ Bấm loại bạn muốn (vd: **Đề**)

#### Bước 2.3 — Nhập số

Bot yêu cầu nhập số (00 đến 99):
```
🎲 XSMB Số Đề — Đề (1:75)
Chọn 1 số (00-99). Thắng nếu khớp 2 số cuối giải Đặc Biệt. Tỷ lệ 1:75.

Nhập các số (cách nhau bởi dấu phẩy, VD: 23,47,89).
Tối thiểu 1, tối đa 1 số.
Gõ /cancel để huỷ.
```

Nhập số bạn muốn cược, ví dụ:
```
23
```

Hoặc cược nhiều số một lúc với Lô (max 1 số/lần với Đề):
```
23, 47, 89
```

#### Bước 2.4 — Nhập tiền cược

Bot hỏi mức cược:
```
✅ Đã chọn: 23

Nhập số điểm × tiền/điểm (VD: 5x10000 hoặc chỉ tiền/điểm 10000):
```

**Định dạng:**
- Cược 1 điểm × 10,000đ → gõ: `10000`
- Cược 5 điểm × 10,000đ (50,000đ tổng) → gõ: `5x10000`

#### Bước 2.5 — Xác nhận

Bot tóm tắt:
```
📋 XÁC NHẬN CƯỢC
━━━━━━━━━━━━━━━━
🎲 XSMB Số Đề — Đề
🔢 Số: 23
💵 10,000 ₫ × 1 điểm
💰 Tổng cược: 10,000 ₫
🎯 Có thể trúng: 750,000 ₫/con
━━━━━━━━━━━━━━━━

[ ✅ Đặt cược ]  [ ❌ Huỷ ]
```

→ Bấm **✅ Đặt cược** để confirm.

Bot xác nhận:
```
✅ Đặt cược thành công!
📋 Mã: #42
💰 Tổng cược: 10,000 ₫
🎯 Có thể trúng: 750,000 ₫

Kết quả sẽ thông báo lúc 18:35.
```

### Bước 3: Đợi kết quả

- **18:30** — Hệ thống tự động lấy kết quả XSMB
- **18:35** — Tính thắng/thua, cộng tiền nếu thắng
- Bot tự gửi tin nhắn cho bạn kết quả

---

## 5. Xem kết quả & lịch sử

### Qua Telegram

| Lệnh | Mục đích |
|---|---|
| `/balance` | Xem số dư hiện tại |
| `/me` | Xem thông tin tài khoản |
| `/mybets` | Xem cược hôm nay |
| `/history` | Xem lịch sử cược cũ |
| `/result` | Xem kết quả XSMB hôm nay |

### Qua website

- **`/wallet`** — Số dư + lịch sử giao dịch (dấu + xanh, dấu − đỏ)
- **`/history`** — Tất cả các cược (pending, won, lost, cancelled)
- **`/results`** — Kết quả XSMB 7 ngày gần nhất

---

## 6. Rút tiền

### Qua website

1. Vào **Ví → Rút tiền**
2. Nhập:
   - Số tiền (tối thiểu **50,000đ**)
   - Số tài khoản ngân hàng
   - Tên chủ TK
   - Ngân hàng
3. Bấm **Yêu cầu rút**
4. Hệ thống tạo lệnh rút status `pending`
5. **Admin sẽ duyệt thủ công** trong vòng vài giờ → tiền chuyển về TK ngân hàng

### Qua Telegram

```
/withdraw
```

Bot dẫn bạn qua các bước:
1. Số tiền
2. Phương thức (bank/MoMo)
3. Số TK
4. Tên chủ TK
5. Tên ngân hàng
6. Xác nhận

### Trạng thái

- 🟡 **Pending** — đang chờ admin duyệt
- ✅ **Approved/Completed** — đã chuyển tiền
- ❌ **Rejected** — bị từ chối (tiền được hoàn lại ngay vào balance)

---

## 7. Bảng tỷ lệ cược

### Game: XSMB (Xổ Số Miền Bắc)

| Loại cược | Mô tả | Tỷ lệ | Ví dụ |
|---|---|---|---|
| **Lô** | Số 2 chữ số xuất hiện trong bất kỳ giải nào | 1 : 75 | Cược 10k → trúng 750k (nếu xuất hiện 1 lần) |
| **Đề** | Khớp 2 số cuối **giải Đặc Biệt** | 1 : 75 | Cược 10k → trúng 750k |
| **Lô Xiên 2** | Cả 2 số phải xuất hiện | 1 : 10 | Cược 10k → trúng 100k |
| **Lô Xiên 3** | Cả 3 số phải xuất hiện | 1 : 40 | Cược 10k → trúng 400k |

### Đặc biệt: Lô có **duplicate**

Nếu số bạn cược Lô xuất hiện **nhiều lần** trong kết quả, bạn được nhân lên:
- VD: Cược Lô số `23` với 10k. Kết quả có 3 lần số `23` → bạn thắng `3 × 75 × 10,000 = 2,250,000đ`

---

## 8. FAQ

### Q: Tôi đặt cược sau 18:10 được không?
**A:** Không. Server-side enforce cutoff 18:10 — sau giờ này mọi lệnh cược bị từ chối với code 422.

### Q: Có thể huỷ cược không?
**A:** Có, trước cutoff 18:10. Vào `/history` → bấm **Huỷ**. Hoặc qua bot: gõ `/mybets` → bấm nút huỷ ngay tin nhắn cược.

### Q: Tôi quên link Telegram, làm sao bot biết tôi?
**A:** Nếu bạn gõ lệnh mà chưa link → bot báo lỗi "chưa liên kết". Quay lại web `/profile` → tạo token → `/link <code>`.

### Q: Tôi mất token chưa link, làm sao?
**A:** Quay lại web → tạo token mới (token cũ tự hết hạn sau 15 phút).

### Q: Số dư trong web & Telegram có sync không?
**A:** Có. Cùng một tài khoản (sau khi link). Đặt cược ở đâu cũng trừ chung balance.

### Q: Nạp tiền nhưng balance không tăng?
**A:** Có 2 nguyên nhân:
1. **SePay auto chưa active** (giai đoạn beta) — gửi ảnh biên lai cho admin Telegram, admin sẽ confirm thủ công trong vài phút.
2. **Sai nội dung chuyển khoản** — phải có **chính xác** chuỗi `NAP00xxxx` trong nội dung. Nếu sai → liên hệ admin.

### Q: Bot không phản hồi?
**A:** Bot có thể đang restart sau deploy. Đợi 30 giây rồi gõ lại `/start`.

### Q: Tôi muốn đặt nhiều cược cùng lúc?
**A:** Có thể cược nhiều số trong cùng 1 lệnh:
- Lô: nhập nhiều số `23, 47, 89` → mỗi số là 1 cược riêng
- Xiên 2: nhập đúng 2 số `23, 47` → cược kép
- Xiên 3: nhập đúng 3 số

### Q: Cược tối thiểu / tối đa?
**A:** Stake tối thiểu **1,000đ/điểm**, tối đa **100 điểm** mỗi lệnh.

### Q: Khi nào trả thưởng?
**A:** Tự động **18:35** mỗi ngày sau khi có kết quả XSMB. Bot gửi tin nhắn thông báo + cộng tiền vào balance ngay.

---

## 9. Liên hệ hỗ trợ

- **Telegram bot:** /help để xem tất cả lệnh
- **Admin Telegram:** liên hệ qua chat trực tiếp (admin sẽ add bạn vào nhóm hỗ trợ)
- **Website:** [Profile → Liên kết Telegram](https://sicbo-eosin.vercel.app/profile)

---

## 10. Tóm tắt nhanh lệnh Telegram

```
/start          — Khởi động bot / chào mừng
/help           — Danh sách lệnh
/link <code>    — Liên kết tài khoản web
/me             — Thông tin tài khoản
/balance        — Số dư
/bet            — Đặt cược (interactive)
/mybets         — Cược hôm nay
/history        — Lịch sử cược cũ
/deposit        — Hướng dẫn nạp tiền
/withdraw       — Rút tiền (interactive)
/result         — Kết quả XSMB hôm nay
/cancel         — Huỷ thao tác hiện tại
```

**Chúc bạn may mắn! 🎰🎲**
