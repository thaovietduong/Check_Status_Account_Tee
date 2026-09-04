# Handoff — Check Status Account Tee

Gửi Vũ,

Đây là tool để check hàng loạt trạng thái store TeePublic, mình fork lại
từ bản GUI cũ (Checklive.py) thành 1 bản CLI đơn giản hơn cho dễ dùng và
dễ sửa. Tài liệu này để Vũ nắm nhanh: tool làm gì, chạy sao, và cần lưu ý
gì khi dùng.

## 1. Tool này làm gì

Cho 1 danh sách username TeePublic, tool sẽ tự động mở từng trang store
(`teepublic.com/user/<username>`) và xếp mỗi username vào đúng 1 trong 3
nhóm:

1. **acc_artist** — store đang sống, được Google index (title dạng
   "T-Shirts by ..." + có thẻ `meta index,follow`). Đây là store "chính
   chủ", ổn định nhất trong 3 nhóm.
2. **acc_thuong** — store vẫn tồn tại, trang load bình thường, nhưng
   chưa/không có dấu hiệu được index như trên.
3. **acc_die_sus** — store không còn tồn tại (404 / "Page Not Found"),
   **hoặc** không kết nối được (timeout, lỗi mạng, proxy die...). Cả 2
   trường hợp này gộp chung 1 nhóm vì đều cần bỏ qua/kiểm tra lại — nên
   đặt tên "die (sus)".

Logic phân loại y hệt bản gốc, mình chỉ gom output ra 3 nhóm rõ ràng thay
vì phải tick từng checkbox như bản GUI.

## 2. Chạy như thế nào

```bash
pip install -r requirements.txt
python check_status.py -i usernames.txt          # không proxy
python check_status.py -i usernames.txt -p proxies.txt   # có proxy
```

Input là file `.txt` (mỗi dòng 1 username) hoặc `.csv` (cột `username`).
Chi tiết đầy đủ các tham số xem `README.md`.

Kết quả nằm trong thư mục `results/`, gồm 4 file (có timestamp):
`ket_qua_day_du_...`, `acc_artist_...`, `acc_thuong_...`, `acc_die_sus_...`.

## 3. Lưu ý khi vận hành

- **Proxy**: nếu check số lượng lớn (vài trăm–nghìn username), nên dùng
  proxy (`-p proxies.txt`) để tránh bị TeePublic chặn IP giữa chừng. Định
  dạng proxy xem `sample_data/proxies_sample.txt`.
- **Số luồng (`-w`)**: mặc định 15. Nếu proxy yếu hoặc bị rớt nhiều, giảm
  xuống (ví dụ `-w 5`) và tăng timeout (`-t 15`) cho ổn định hơn.
- **Nhóm `acc_die_sus` không đồng nghĩa 100% "chết hẳn"** — có thể là lỗi
  proxy/mạng tạm thời. Nếu số lượng die bất thường cao, thử chạy lại nhóm
  đó (hoặc chạy không proxy) để xác nhận trước khi kết luận.
- **Không commit** file proxy thật hay file kết quả thật lên git — cả hai
  đều đã nằm trong `.gitignore` sẵn, đừng `git add -f` đè lên.
- Tool chỉ đọc trang public (không đăng nhập, không bypass gì) — nhưng vẫn
  nên chạy vừa phải, tránh spam quá nhanh dễ bị chặn.

## 4. Quyền truy cập repo

Vũ đã được thêm vào repo với quyền **Write** (clone/sửa/push code bình
thường). Repo: https://github.com/thaovietduong/Check_Status_Account_Tee

## 5. Có vấn đề gì

Nhắn trực tiếp cho Đường (thaovietduong@gmail.com) nếu:
- Tool báo lỗi khi chạy / cần thêm tham số gì đó
- Muốn đổi logic phân loại (ví dụ thêm điều kiện khác cho "artist")
- Cần build thêm tính năng (ví dụ: chạy định kỳ, gộp nhiều lần check, xuất Excel...)

Cảm ơn Vũ đã hỗ trợ!
