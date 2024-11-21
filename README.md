Sau đây là bản nháp của tệp README dựa trên thông tin được cung cấp:

---

# Ứng dụng truyền tệp dựa trên socket

## Tổng quan
Ứng dụng này cho phép truyền tệp bằng lập trình socket. Nó bao gồm một máy chủ để quản lý lưu trữ tệp và các máy khách để tải lên và tải xuống tệp.

## Bắt đầu

### Thêm người dùng
Để thêm người dùng mới, hãy chạy tập lệnh sau:
```sh
python add_user.py
```
Làm theo lời nhắc để nhập tên người dùng, mật khẩu và thư mục lưu trữ tùy chọn.

### Chạy máy chủ
Để khởi động máy chủ, hãy sử dụng lệnh sau:
```sh
python server.py
```
Máy chủ sẽ khởi động và lắng nghe các kết nối của máy khách trên máy chủ và cổng mặc định.

### Chạy máy khách
Để chạy ứng dụng máy khách, hãy sử dụng lệnh sau:
```sh
python client.py
```
Giao diện người dùng đồ họa của máy khách sẽ mở ra, cho phép bạn kết nối với máy chủ, đăng nhập và tải lên/tải xuống tệp.

### Các vấn đề đã biết
- Hiện tại có một vấn đề đã biết với chức năng tải xuống. Quá trình tải xuống có thể không hoàn tất thành công trong một số trường hợp.

---
