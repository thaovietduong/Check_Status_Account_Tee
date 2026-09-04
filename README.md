# Check Status Account Tee

Tool kiểm tra hàng loạt trạng thái store trên **TeePublic**, phân loại mỗi
username vào đúng 1 trong 3 nhóm:

| Nhóm | Ý nghĩa |
|---|---|
| `acc_artist` | Store đang hoạt động và được Google index (chính chủ, ổn định nhất) |
| `acc_thuong` | Store vẫn tồn tại, hoạt động bình thường, nhưng chưa/không thấy dấu hiệu được index |
| `acc_die_sus` | Store không còn tồn tại, hoặc không truy cập được (lỗi kết nối/timeout/bị chặn) |

Đây là bản fork **đơn giản hoá** từ tool GUI (Tkinter) gốc — chạy bằng dòng
lệnh (CLI) để dễ đọc, dễ sửa, dễ chạy tự động, không cần giao diện đồ hoạ.

> Xem `HANDOFF.md` để biết hướng dẫn bàn giao / vận hành chi tiết.

## 1. Cài đặt

Yêu cầu Python 3.9+.

```bash
pip install -r requirements.txt
```

## 2. Chuẩn bị file input

File `.txt`, mỗi dòng 1 username:

```
alasha
abbicuradirisplendere
alekart777
```

Hoặc file `.csv` có cột `username`.

Xem file mẫu ở `sample_data/usernames_sample.txt`.

## 3. Chạy

```bash
python check_status.py -i usernames.txt
```

Có proxy (khuyến khích khi check số lượng lớn, tránh bị chặn IP):

```bash
python check_status.py -i usernames.txt -p proxies.txt
```

Các tham số khác:

```bash
python check_status.py --help
```

```
-i, --input     File .txt hoặc .csv chứa danh sách username (bắt buộc)
-p, --proxies   File .txt chứa danh sách proxy (tuỳ chọn)
-w, --workers   Số luồng chạy song song (mặc định 15)
-t, --timeout   Timeout mỗi request, giây (mặc định 10)
```

Định dạng proxy, mỗi dòng 1 proxy (xem `sample_data/proxies_sample.txt`):

```
ip:port
ip:port:username:password
```

## 4. Kết quả

Sau khi chạy xong, tool tạo thư mục `results/` với 4 file (có timestamp):

- `ket_qua_day_du_<timestamp>.txt` — toàn bộ, kèm trạng thái chi tiết (`username|raw_status|bucket`)
- `acc_artist_<timestamp>.txt` — chỉ username thuộc nhóm artist
- `acc_thuong_<timestamp>.txt` — chỉ username thuộc nhóm thường
- `acc_die_sus_<timestamp>.txt` — chỉ username thuộc nhóm die (sus)

`results/` đã được thêm vào `.gitignore` (không commit lên git) vì đây là dữ
liệu kết quả chạy, có thể chứa danh sách tài khoản thật.

## 5. Lưu ý

- File `proxies.txt` thật (nếu có) **không** được commit lên git — đã được
  thêm vào `.gitignore`. Chỉ có file mẫu `sample_data/proxies_sample.txt`
  (không chứa proxy thật) nằm trong repo.
- Tool gọi trực tiếp trang public của TeePublic (`teepublic.com/user/...`),
  không đăng nhập, không bypass bất kỳ cơ chế bảo mật nào — chỉ đơn thuần
  đọc HTML trang store để xác định trạng thái.
- Nên chạy với số luồng (`-w`) và tần suất vừa phải để tránh bị TeePublic
  giới hạn/chặn IP.

## Cấu trúc project

```
Check_Status_Account_Tee/
├── check_status.py          # script chính (CLI)
├── requirements.txt
├── sample_data/
│   ├── usernames_sample.txt
│   └── proxies_sample.txt
├── results/                 # (tự tạo khi chạy, không commit)
├── HANDOFF.md                # tài liệu bàn giao
└── README.md
```
